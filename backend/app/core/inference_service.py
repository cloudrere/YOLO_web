import json
import time
from pathlib import Path
from urllib.parse import urlparse

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
from app.services.log_service import create_log
from app.services.model_service import ensure_active_model_loaded
from app.utils.files import remove_file, save_upload_file
from app.utils.image import draw_detections, write_frame


def detection_to_schema(item: dict, frame_id: int | None = None) -> dict:
    return {
        "class": item["class"],
        "confidence": float(item["confidence"]),
        "bbox": tuple(float(v) for v in item["bbox"]),
        "frame_id": frame_id,
    }


def result_row_to_dict(row: DetectionResult) -> dict:
    return {
        "class": row.class_name,
        "confidence": row.confidence,
        "bbox": (row.x1, row.y1, row.x2, row.y2),
        "frame_id": row.frame_id,
    }


def artifact_url(record_id: int) -> str:
    return f"/api/detect/artifacts/{record_id}"


def create_record(
    db: Session,
    user_id: int | None,
    model_id: int | None,
    source_type: str,
    file_name: str,
    file_path: str,
    status: str = "done",
) -> DetectionRecord:
    record = DetectionRecord(
        user_id=user_id,
        model_id=model_id,
        source_type=source_type,
        file_name=file_name,
        file_path=file_path,
        status=status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def save_detection_results(db: Session, record_id: int, detections: list[dict], frame_id: int | None = None) -> None:
    for item in detections:
        x1, y1, x2, y2 = item["bbox"]
        db.add(
            DetectionResult(
                record_id=record_id,
                class_name=item["class"],
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


def resolve_record_artifact(db: Session, record_id: int) -> Path:
    record = db.get(DetectionRecord, record_id)
    if record is None:
        raise AppException(40404, "Detection record not found", 404)
    if not record.result_path:
        raise AppException(40406, "Detection artifact not found", 404)
    path = Path(record.result_path).resolve()
    results_root = settings.results_path.resolve()
    if results_root not in path.parents and path != results_root:
        raise AppException(40301, "Artifact path is outside result storage", 403)
    if not path.exists() or not path.is_file():
        raise AppException(40406, "Detection artifact not found", 404)
    return path


def detect_image(db: Session, file: UploadFile, user: User) -> dict:
    active_model = ensure_active_model_loaded(db)
    saved = save_upload_file(file, settings.uploads_path / "images")
    start = time.perf_counter()
    detections = yolo_engine.predict_image(str(saved))
    duration_ms = int((time.perf_counter() - start) * 1000)
    record = create_record(db, user.id, active_model.id, "image", file.filename or saved.name, str(saved))
    record.duration_ms = duration_ms
    save_detection_results(db, record.id, detections)
    result_url = save_annotated_image(record, saved, detections, "images")
    db.commit()
    create_log(db, "detect", f"Image detection completed for record {record.id}", module="detect", user_id=user.id)
    output = [detection_to_schema(item) for item in detections]
    return {
        "record_id": record.id,
        "results": output,
        "analysis": analyze_detection_results(detections),
        "duration_ms": duration_ms,
        "result_url": result_url,
    }


def detect_batch(db: Session, files: list[UploadFile], user: User) -> dict:
    active_model = ensure_active_model_loaded(db)
    saved_files: list[tuple[UploadFile, Path]] = []
    for file in files:
        saved_files.append((file, save_upload_file(file, settings.uploads_path / "batch")))

    sources = [str(path) for _, path in saved_files]
    batch_results = yolo_engine.predict_batch(sources)
    items = []
    for (file, path), detections in zip(saved_files, batch_results, strict=False):
        start = time.perf_counter()
        record = create_record(db, user.id, active_model.id, "batch_image", file.filename or path.name, str(path))
        save_detection_results(db, record.id, detections)
        record.duration_ms = int((time.perf_counter() - start) * 1000)
        result_url = save_annotated_image(record, path, detections, "batch")
        db.commit()
        items.append(
            {
                "file_name": file.filename or path.name,
                "status": "done",
                "record_id": record.id,
                "results": [detection_to_schema(item) for item in detections],
                "analysis": analyze_detection_results(detections),
                "error": "",
                "result_url": result_url,
            }
        )
    create_log(db, "detect", f"Batch detection completed for {len(items)} files", module="detect", user_id=user.id)
    return {"items": items}


def create_video_task(db: Session, file: UploadFile, user: User) -> dict:
    active_model = ensure_active_model_loaded(db)
    saved = save_upload_file(file, settings.uploads_path / "videos")
    record = create_record(db, user.id, active_model.id, "video", file.filename or saved.name, str(saved), status="running")
    task = Task(
        type="video_detection",
        status="pending",
        progress=0.0,
        user_id=user.id,
        record_id=record.id,
        payload_json=json.dumps({"video_path": str(saved), "record_id": record.id, "model_id": active_model.id}, ensure_ascii=False),
        max_retries=settings.task_max_retries,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_queue.enqueue(task.id)
    create_log(db, "task", f"Video detection task {task.id} created", module="detect", user_id=user.id)
    return {"task_id": task.id, "record_id": record.id, "status": task.status}


def process_video_task(task: Task, db: Session) -> dict:
    payload = json.loads(task.payload_json)
    video_path = payload["video_path"]
    record_id = int(payload["record_id"])
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
    processed_frames = 0
    sampled_frames = 0
    all_detections: list[dict] = []
    start = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        current_frame = processed_frames
        processed_frames += 1
        if current_frame % step != 0:
            continue
        detections = yolo_engine.predict_image(frame)
        save_detection_results(db, record.id, detections, frame_id=current_frame)
        annotated = draw_detections(frame, detections)
        frame_path = output_dir / f"frame_{current_frame:08d}.jpg"
        write_frame(frame_path, annotated)
        sampled_frames += 1
        all_detections.extend({**item, "frame_id": current_frame} for item in detections)
        if frame_count:
            task.progress = min(99.0, round((processed_frames / frame_count) * 100, 2))
        else:
            task.progress = min(99.0, sampled_frames)
        db.commit()

    cap.release()
    record.status = "done"
    record.duration_ms = int((time.perf_counter() - start) * 1000)
    record.result_path = str(output_dir)
    db.commit()
    create_log(db, "task", f"Video detection task {task.id} completed", module="detect", user_id=task.user_id)
    return {
        "record_id": record.id,
        "frames_processed": processed_frames,
        "frames_sampled": sampled_frames,
        "results_count": len(all_detections),
        "analysis": analyze_detection_results(all_detections),
        "frame_dir": str(output_dir),
        "stream_path": f"/api/detect/video/stream/{task.id}",
    }


def get_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise AppException(40405, "Task not found", 404)
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


def stream_realtime_source(source: str):
    cap = cv2.VideoCapture(normalize_realtime_source(source))
    if not cap.isOpened():
        raise AppException(40023, "Cannot open realtime video source")

    def frames():
        min_interval = 1 / max(1, settings.video_sample_fps)
        last_sent = 0.0
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                now = time.monotonic()
                if now - last_sent < min_interval:
                    time.sleep(0.01)
                    continue
                detections = yolo_engine.predict_image(frame)
                annotated = draw_detections(frame, detections)
                ok, buffer = cv2.imencode(".jpg", annotated)
                if not ok:
                    continue
                last_sent = now
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        finally:
            cap.release()

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
