import json
import shutil
import time
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from urllib.parse import urlparse
from uuid import uuid4

import cv2
from fastapi import UploadFile
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.response import AppException
from app.core.task_queue import task_queue
from app.core.yolo_engine import yolo_engine
from app.models.detection_record import DetectionRecord
from app.models.detection_result import DetectionResult
from app.models.task import Task
from app.models.user import User
from app.services.ai_analysis_service import analyze_detection_results
from app.services.class_mapping_service import decorate_detection, reverse_lookup_class, translate_class
from app.services.log_service import create_log
from app.services.model_service import ensure_active_model_loaded
from app.utils.files import remove_file, save_upload_file
from app.utils.image import draw_detections, write_frame
from app.utils.time import utc_now


def detection_to_schema(item: dict, db: Session | None = None, model_id: int | None = None, frame_id: int | None = None) -> dict:
    if db is not None:
        return decorate_detection(db, item, model_id, frame_id)
    return {
        "class": item["class"],
        "class_zh": item.get("class_zh", item["class"]),
        "confidence": float(item["confidence"]),
        "bbox": tuple(float(v) for v in item["bbox"]),
        "frame_id": frame_id,
    }


def result_row_to_dict(row: DetectionResult) -> dict:
    return {
        "class": row.class_name,
        "class_zh": row.class_name_zh or row.class_name,
        "confidence": row.confidence,
        "bbox": (row.x1, row.y1, row.x2, row.y2),
        "frame_id": row.frame_id,
    }


def record_file_url(record_id: int, kind: str) -> str:
    return f"/api/detect/artifacts/{record_id}?kind={kind}"


def artifact_url(record_id: int) -> str:
    return record_file_url(record_id, "result")


def temp_file_url(path: Path) -> str:
    return f"/api/detect/temp/{path.name}"


def normalize_threshold(value: float | None, default: float, low: float = 0.0, high: float = 1.0) -> float:
    if value is None:
        return default
    return min(high, max(low, float(value)))


def analysis_payload(results: list[dict], analyze: bool) -> dict | None:
    return analyze_detection_results(results) if analyze else None


def create_record(
    db: Session,
    user_id: int | None,
    model_id: int | None,
    source_type: str,
    file_name: str,
    file_path: str,
    status: str = "done",
    confidence: float | None = None,
    iou: float | None = None,
    save_history: bool = True,
    model_name: str = "",
    device: str = "",
) -> DetectionRecord:
    record = DetectionRecord(
        user_id=user_id,
        model_id=model_id,
        source_type=source_type,
        file_name=file_name,
        file_path=file_path,
        original_path=file_path,
        status=status,
        confidence_threshold=confidence if confidence is not None else settings.confidence_threshold,
        iou_threshold=iou if iou is not None else settings.iou_threshold,
        save_history=save_history,
        model_name=model_name,
        device=device,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def save_detection_results(db: Session, record_id: int, detections: list[dict], frame_id: int | None = None, model_id: int | None = None) -> None:
    for item in detections:
        x1, y1, x2, y2 = item["bbox"]
        class_name = str(item["class"])
        db.add(
            DetectionResult(
                record_id=record_id,
                class_name=class_name,
                class_name_zh=translate_class(db, class_name, model_id),
                confidence=float(item["confidence"]),
                x1=float(x1),
                y1=float(y1),
                x2=float(x2),
                y2=float(y2),
                frame_id=frame_id,
            )
        )


def save_annotated_image(record: DetectionRecord, image_path: Path, detections: list[dict], group: str) -> str:
    frame = cv2.imread(str(image_path))
    if frame is None:
        raise AppException(40021, "Cannot read image file")
    output_path = settings.results_path / group / f"record_{record.id}.jpg"
    write_frame(output_path, draw_detections(frame, detections))
    record.result_path = str(output_path)
    return artifact_url(record.id)


def resolve_record_artifact(db: Session, record_id: int, kind: str = "result") -> Path:
    record = db.get(DetectionRecord, record_id)
    if record is None:
        raise AppException(40404, "Detection record not found", 404)
    selected = record.original_path if kind == "original" else record.result_path
    if not selected:
        raise AppException(40406, "Detection artifact not found", 404)
    path = Path(selected).resolve()
    if kind == "thumbnail" and record.source_type == "video":
        task = db.query(Task).filter(Task.record_id == record.id).order_by(Task.id.desc()).first()
        if task is not None:
            frame_dir = settings.results_path / "video_frames" / str(task.id)
            first_frame = next(iter(sorted(frame_dir.glob("*.jpg"))), None)
            if first_frame is not None:
                path = first_frame.resolve()
    elif path.is_dir():
        first_frame = next(iter(sorted(path.glob("*.jpg"))), None)
        if first_frame is None:
            raise AppException(40406, "Detection artifact not found", 404)
        path = first_frame.resolve()
    roots = [settings.results_path.resolve(), settings.uploads_path.resolve()]
    if not any(root in path.parents or path == root for root in roots):
        raise AppException(40301, "Artifact path is outside storage", 403)
    if not path.exists() or not path.is_file():
        raise AppException(40406, "Detection artifact not found", 404)
    return path


def resolve_temp_artifact(name: str) -> Path:
    path = (settings.results_path / "temp" / Path(name).name).resolve()
    temp_root = (settings.results_path / "temp").resolve()
    if temp_root not in path.parents and path != temp_root:
        raise AppException(40301, "Artifact path is outside temporary storage", 403)
    if not path.exists() or not path.is_file():
        raise AppException(40406, "Detection artifact not found", 404)
    return path


def save_temp_original(path: Path) -> Path:
    output_path = settings.results_path / "temp" / f"original_{uuid4().hex}{path.suffix}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, output_path)
    return output_path


def save_temp_detection_image(image_path: Path, detections: list[dict]) -> Path:
    frame = cv2.imread(str(image_path))
    if frame is None:
        raise AppException(40021, "Cannot read image file")
    output_path = settings.results_path / "temp" / f"{uuid4().hex}.jpg"
    write_frame(output_path, draw_detections(frame, detections))
    return output_path


def create_video_writer(path: Path, frame, fps: float) -> cv2.VideoWriter:
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = frame.shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), max(1.0, fps), (width, height))
    if not writer.isOpened():
        raise AppException(50021, "Cannot create detection video file")
    return writer


def detect_image(
    db: Session,
    file: UploadFile,
    user: User,
    confidence: float | None = None,
    iou: float | None = None,
    save_history: bool = True,
    analyze: bool = False,
) -> dict:
    active_model = ensure_active_model_loaded(db)
    conf_value = normalize_threshold(confidence, settings.confidence_threshold)
    iou_value = normalize_threshold(iou, settings.iou_threshold)
    saved = save_upload_file(file, settings.uploads_path / "images")
    start = time.perf_counter()
    detections = yolo_engine.predict_image(str(saved), conf=conf_value, iou=iou_value)
    duration_ms = int((time.perf_counter() - start) * 1000)
    output = [detection_to_schema(item, db, active_model.id) for item in detections]
    if not save_history:
        original_path = save_temp_original(saved)
        result_path = save_temp_detection_image(saved, detections)
        create_log(db, "detect", "单图检测已完成，未写入历史记录", module="detect", user_id=user.id)
        return {
            "record_id": None,
            "results": output,
            "analysis": analysis_payload(output, analyze),
            "duration_ms": duration_ms,
            "original_url": temp_file_url(original_path),
            "result_url": temp_file_url(result_path),
            "model_name": active_model.display_name or active_model.name,
            "device": yolo_engine.device,
            "parameters": {"confidence": conf_value, "iou": iou_value, "save_history": False, "analyze": analyze},
        }
    record = create_record(
        db,
        user.id,
        active_model.id,
        "image",
        file.filename or saved.name,
        str(saved),
        confidence=conf_value,
        iou=iou_value,
        save_history=True,
        model_name=active_model.display_name or active_model.name,
        device=yolo_engine.device,
    )
    record.duration_ms = duration_ms
    save_detection_results(db, record.id, detections, model_id=active_model.id)
    result_url = save_annotated_image(record, saved, detections, "images")
    db.commit()
    create_log(db, "detect", f"单图检测已完成，记录编号 {record.id}", module="detect", user_id=user.id)
    return {
        "record_id": record.id,
        "results": output,
        "analysis": analysis_payload(output, analyze),
        "duration_ms": duration_ms,
        "original_url": record_file_url(record.id, "original"),
        "result_url": result_url,
        "model_name": active_model.display_name or active_model.name,
        "device": yolo_engine.device,
        "parameters": {"confidence": conf_value, "iou": iou_value, "save_history": True, "analyze": analyze},
    }


def detect_batch(
    db: Session,
    files: list[UploadFile],
    user: User,
    confidence: float | None = None,
    iou: float | None = None,
    save_history: bool = True,
    analyze: bool = False,
) -> dict:
    active_model = ensure_active_model_loaded(db)
    conf_value = normalize_threshold(confidence, settings.confidence_threshold)
    iou_value = normalize_threshold(iou, settings.iou_threshold)
    saved_files: list[tuple[UploadFile, Path]] = []
    for file in files:
        saved_files.append((file, save_upload_file(file, settings.uploads_path / "batch")))

    sources = [str(path) for _, path in saved_files]
    batch_results = yolo_engine.predict_batch(sources, conf=conf_value, iou=iou_value)
    items = []
    for (file, path), detections in zip(saved_files, batch_results, strict=False):
        start = time.perf_counter()
        output = [detection_to_schema(item, db, active_model.id) for item in detections]
        if save_history:
            record = create_record(
                db,
                user.id,
                active_model.id,
                "batch_image",
                file.filename or path.name,
                str(path),
                confidence=conf_value,
                iou=iou_value,
                save_history=True,
                model_name=active_model.display_name or active_model.name,
                device=yolo_engine.device,
            )
            save_detection_results(db, record.id, detections, model_id=active_model.id)
            record.duration_ms = int((time.perf_counter() - start) * 1000)
            result_url = save_annotated_image(record, path, detections, "batch")
            original_url = record_file_url(record.id, "original")
            record_id = record.id
            db.commit()
        else:
            original_path = save_temp_original(path)
            result_path = save_temp_detection_image(path, detections)
            original_url = temp_file_url(original_path)
            result_url = temp_file_url(result_path)
            record_id = None
        items.append(
            {
                "file_name": file.filename or path.name,
                "status": "done",
                "record_id": record_id,
                "results": output,
                "analysis": analysis_payload(output, analyze),
                "error": "",
                "original_url": original_url,
                "result_url": result_url,
                "duration_ms": int((time.perf_counter() - start) * 1000),
            }
        )
    create_log(db, "detect", f"批量检测已完成，共处理 {len(items)} 个文件", module="detect", user_id=user.id)
    return {"items": items, "parameters": {"confidence": conf_value, "iou": iou_value, "save_history": save_history, "analyze": analyze}}


def create_video_task(
    db: Session,
    file: UploadFile,
    user: User,
    confidence: float | None = None,
    iou: float | None = None,
    save_history: bool = True,
    analyze: bool = False,
) -> dict:
    active_model = ensure_active_model_loaded(db)
    conf_value = normalize_threshold(confidence, settings.confidence_threshold)
    iou_value = normalize_threshold(iou, settings.iou_threshold)
    saved = save_upload_file(file, settings.uploads_path / "videos")
    record = create_record(
        db,
        user.id,
        active_model.id,
        "video",
        file.filename or saved.name,
        str(saved),
        status="running",
        confidence=conf_value,
        iou=iou_value,
        save_history=save_history,
        model_name=active_model.display_name or active_model.name,
        device=yolo_engine.device,
    )
    task = Task(
        type="video_detection",
        status="pending",
        progress=0.0,
        user_id=user.id,
        record_id=record.id,
        payload_json=json.dumps(
            {
                "video_path": str(saved),
                "record_id": record.id,
                "model_id": active_model.id,
                "confidence": conf_value,
                "iou": iou_value,
                "save_history": save_history,
                "analyze": analyze,
            },
            ensure_ascii=False,
        ),
        max_retries=settings.task_max_retries,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_queue.enqueue(task.id)
    create_log(db, "task", f"视频检测任务 {task.id} 已创建", module="detect", user_id=user.id)
    return {
        "task_id": task.id,
        "record_id": record.id,
        "status": task.status,
        "original_url": record_file_url(record.id, "original"),
        "parameters": {"confidence": conf_value, "iou": iou_value, "save_history": save_history, "analyze": analyze},
    }


def process_video_task(task: Task, db: Session) -> dict:
    payload = json.loads(task.payload_json)
    video_path = payload["video_path"]
    record_id = int(payload["record_id"])
    model_id = int(payload.get("model_id") or 0) or None
    conf_value = normalize_threshold(payload.get("confidence"), settings.confidence_threshold)
    iou_value = normalize_threshold(payload.get("iou"), settings.iou_threshold)
    analyze = bool(payload.get("analyze", False))
    record = db.get(DetectionRecord, record_id)
    if record is None:
        raise AppException(40404, "Detection record not found", 404)

    ensure_active_model_loaded(db)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise AppException(40020, "Cannot open video file")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, int(fps / max(1, settings.video_sample_fps)))
    output_dir = settings.results_path / "video_frames" / str(task.id)
    output_dir.mkdir(parents=True, exist_ok=True)
    video_output_path = settings.results_path / "videos" / f"task_{task.id}.mp4"
    writer: cv2.VideoWriter | None = None
    processed_frames = 0
    sampled_frames = 0
    all_detections: list[dict] = []
    start = time.perf_counter()

    try:
        while True:
            db.refresh(task)
            if task.status == "cancelled":
                record.status = "cancelled"
                db.commit()
                create_log(db, "task", f"视频检测任务 {task.id} 已取消", module="detect", user_id=task.user_id)
                return {
                    "record_id": record.id,
                    "frames_processed": processed_frames,
                    "frames_sampled": sampled_frames,
                    "results_count": len(all_detections),
                    "cancelled": True,
                    "frame_dir": str(output_dir),
                    "original_url": record_file_url(record.id, "original"),
                    "stream_path": f"/api/detect/video/stream/{task.id}",
                }
            while task.status == "paused":
                time.sleep(0.3)
                db.refresh(task)
                if task.status == "cancelled":
                    record.status = "cancelled"
                    db.commit()
                    return {"record_id": record.id, "cancelled": True, "frame_dir": str(output_dir)}
            ok, frame = cap.read()
            if not ok:
                break
            current_frame = processed_frames
            processed_frames += 1
            if current_frame % step != 0:
                continue
            detections = yolo_engine.predict_image(frame, conf=conf_value, iou=iou_value)
            save_detection_results(db, record.id, detections, frame_id=current_frame, model_id=model_id)
            annotated = draw_detections(frame, detections)
            if writer is None:
                writer = create_video_writer(video_output_path, annotated, min(float(fps), float(max(1, settings.video_sample_fps))))
            writer.write(annotated)
            frame_path = output_dir / f"frame_{current_frame:08d}.jpg"
            write_frame(frame_path, annotated)
            sampled_frames += 1
            all_detections.extend({**item, "frame_id": current_frame} for item in detections)
            if frame_count:
                task.progress = min(99.0, round((processed_frames / frame_count) * 100, 2))
            else:
                task.progress = min(99.0, sampled_frames)
            db.commit()

        if writer is not None:
            writer.release()
            writer = None
        record.status = "done"
        record.duration_ms = int((time.perf_counter() - start) * 1000)
        record.result_path = str(video_output_path if video_output_path.exists() else output_dir)
        db.commit()
        result_url = artifact_url(record.id) if Path(record.result_path).is_file() else f"/api/detect/video/stream/{task.id}"
        create_log(db, "task", f"视频检测任务 {task.id} 已完成", module="detect", user_id=task.user_id)
        return {
            "record_id": record.id,
            "frames_processed": processed_frames,
            "frames_sampled": sampled_frames,
            "results_count": len(all_detections),
            "analysis": analysis_payload([detection_to_schema(item, db, model_id, item.get("frame_id")) for item in all_detections], analyze),
            "frame_dir": str(output_dir),
            "video_path": str(video_output_path) if video_output_path.exists() else "",
            "original_url": record_file_url(record.id, "original"),
            "result_url": result_url,
            "video_url": result_url if Path(record.result_path).is_file() else "",
            "stream_path": f"/api/detect/video/stream/{task.id}",
        }
    finally:
        cap.release()
        if writer is not None:
            writer.release()


def get_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise AppException(40405, "Task not found", 404)
    return task


def control_task(db: Session, task_id: int, action: str) -> Task:
    task = get_task(db, task_id)
    if action == "pause" and task.status == "running":
        task.status = "paused"
    elif action == "resume" and task.status == "paused":
        task.status = "running"
    elif action in {"cancel", "end"} and task.status in {"pending", "running", "paused"}:
        task.status = "cancelled"
        task.finished_at = utc_now()
    db.commit()
    db.refresh(task)
    return task


def get_record_detail(db: Session, record_id: int) -> dict:
    record = db.query(DetectionRecord).options(selectinload(DetectionRecord.results)).filter(DetectionRecord.id == record_id).first()
    if record is None:
        raise AppException(40404, "Detection record not found", 404)
    results = [result_row_to_dict(item) for item in record.results]
    return {
        "id": record.id,
        "user_id": record.user_id,
        "model_id": record.model_id,
        "source_type": record.source_type,
        "file_name": record.file_name,
        "file_path": record.file_path,
        "result_path": record.result_path,
        "status": record.status,
        "duration_ms": record.duration_ms,
        "created_at": record.created_at,
        "results": results,
        "analysis": analyze_detection_results(results),
        "result_url": artifact_url(record.id) if record.result_path and Path(record.result_path).is_file() else "",
    }


def stream_video_frames(task_id: int):
    output_dir = settings.results_path / "video_frames" / str(task_id)
    sent: set[Path] = set()
    idle_started = time.monotonic()
    while True:
        frames = sorted(output_dir.glob("*.jpg")) if output_dir.exists() else []
        new_frames = [path for path in frames if path not in sent]
        if new_frames:
            idle_started = time.monotonic()
        for path in new_frames:
            sent.add(path)
            data = path.read_bytes()
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n"
        if time.monotonic() - idle_started > settings.stream_frame_timeout_seconds:
            break
        time.sleep(0.2)


def normalize_realtime_source(source: str):
    value = source.strip()
    if value.isdigit():
        return int(value)
    parsed = urlparse(value)
    if parsed.scheme.lower() in {"rtsp", "http", "https"} and parsed.netloc:
        return value
    raise AppException(40022, "Realtime source must be a camera index or RTSP/HTTP(S) stream URL")


def stream_realtime_source(source: str, confidence: float | None = None, iou: float | None = None):
    cap = cv2.VideoCapture(normalize_realtime_source(source))
    if not cap.isOpened():
        raise AppException(40023, "Cannot open realtime video source")
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    stop_event = Event()
    latest_frame: Queue = Queue(maxsize=1)

    def capture_latest_frame() -> None:
        try:
            while not stop_event.is_set():
                ok, frame = cap.read()
                if not ok:
                    stop_event.set()
                    break
                if latest_frame.full():
                    try:
                        latest_frame.get_nowait()
                    except Empty:
                        pass
                latest_frame.put(frame)
        finally:
            cap.release()

    capture_thread = Thread(target=capture_latest_frame, daemon=True)
    capture_thread.start()

    def frames():
        min_interval = 1 / max(1, settings.video_sample_fps)
        last_sent = 0.0
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 72]
        try:
            while not stop_event.is_set():
                try:
                    frame = latest_frame.get(timeout=0.5)
                except Empty:
                    continue
                now = time.monotonic()
                if now - last_sent < min_interval:
                    continue
                detections = yolo_engine.predict_image(frame, conf=confidence, iou=iou)
                annotated = draw_detections(frame, detections)
                ok, buffer = cv2.imencode(".jpg", annotated, encode_params)
                if not ok:
                    continue
                last_sent = time.monotonic()
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        finally:
            stop_event.set()
            capture_thread.join(timeout=1.0)

    return frames()


def delete_record(db: Session, record_id: int, delete_file: bool = False) -> None:
    record = db.get(DetectionRecord, record_id)
    if record is None:
        raise AppException(40404, "Detection record not found", 404)
    if delete_file:
        remove_file(record.file_path)
    db.delete(record)
    db.commit()


task_queue.register("video_detection", process_video_task)
