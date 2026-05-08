from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.core.response import AppException
from app.models.detection_record import DetectionRecord
from app.models.detection_result import DetectionResult
from app.models.user import User
from app.services.ai_analysis_service import analyze_detection_results
from app.services.class_mapping_service import reverse_lookup_class, translate_class


def _record_file_url(record: DetectionRecord, kind: str) -> str:
    selected = record.original_path if kind == "original" else record.result_path
    if not selected or not Path(selected).is_file():
        return ""
    return f"/api/detect/artifacts/{record.id}?kind={kind}"


def _model_display_name(record: DetectionRecord) -> str:
    if record.model is not None:
        return record.model.display_name or record.model.name
    return record.model_name


def _result_to_dict(db: Session, row: DetectionResult, model_id: int | None = None) -> dict:
    class_zh = row.class_name_zh or translate_class(db, row.class_name, model_id)
    return {
        "class": row.class_name,
        "class_zh": class_zh,
        "confidence": row.confidence,
        "bbox": (row.x1, row.y1, row.x2, row.y2),
        "frame_id": row.frame_id,
    }


def _class_summary(db: Session, record: DetectionRecord) -> list[dict]:
    buckets: dict[tuple[str, str], dict] = {}
    for result in record.results:
        class_zh = result.class_name_zh or translate_class(db, result.class_name, record.model_id)
        key = (result.class_name, class_zh)
        bucket = buckets.setdefault(key, {"class": result.class_name, "class_zh": class_zh, "count": 0, "confidence_sum": 0.0})
        bucket["count"] += 1
        bucket["confidence_sum"] += float(result.confidence)
    items = []
    for bucket in buckets.values():
        count = int(bucket["count"])
        items.append(
            {
                "class": bucket["class"],
                "class_zh": bucket["class_zh"],
                "count": count,
                "avg_confidence": round(float(bucket["confidence_sum"]) / count, 4) if count else 0.0,
            }
        )
    return sorted(items, key=lambda item: item["count"], reverse=True)


def _analysis_with_zh(results: list[dict]) -> dict:
    analysis = analyze_detection_results(results)
    class_mapping = {item["class"]: item.get("class_zh", item["class"]) for item in results}
    for item in analysis.get("class_distribution", []):
        item["class_zh"] = class_mapping.get(item.get("class"), item.get("class", ""))
    return analysis


def _record_to_item(db: Session, record: DetectionRecord) -> dict:
    parameters = {
        "confidence": record.confidence_threshold,
        "iou": record.iou_threshold,
        "save_history": record.save_history,
    }
    return {
        "id": record.id,
        "user_id": record.user_id,
        "username": record.user.username if record.user else "",
        "model_id": record.model_id,
        "model_name": _model_display_name(record),
        "source_type": record.source_type,
        "file_name": record.file_name,
        "file_path": record.file_path,
        "original_path": record.original_path,
        "result_path": record.result_path,
        "original_url": _record_file_url(record, "original"),
        "result_url": _record_file_url(record, "result"),
        "status": record.status,
        "duration_ms": record.duration_ms,
        "created_at": record.created_at,
        "result_count": len(record.results),
        "classes": _class_summary(db, record),
        "confidence_threshold": record.confidence_threshold,
        "iou_threshold": record.iou_threshold,
        "save_history": record.save_history,
        "device": record.device,
        "parameters": parameters,
    }


def list_records(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    source_type: str | None = None,
    class_name: str | None = None,
    user_id: int | None = None,
    class_name_zh: str | None = None,
    username: str | None = None,
) -> tuple[list[dict], int]:
    query = db.query(DetectionRecord)
    if source_type:
        query = query.filter(DetectionRecord.source_type == source_type)
    if user_id is not None:
        query = query.filter(DetectionRecord.user_id == user_id)
    if username:
        query = query.join(User, DetectionRecord.user_id == User.id).filter(User.username.contains(username.strip()))
    if class_name or class_name_zh:
        query = query.join(DetectionResult)
    if class_name:
        normalized_class = reverse_lookup_class(db, class_name)
        query = query.filter(DetectionResult.class_name == normalized_class)
    if class_name_zh:
        normalized_zh = class_name_zh.strip()
        normalized_class = reverse_lookup_class(db, normalized_zh)
        query = query.filter(or_(DetectionResult.class_name_zh == normalized_zh, DetectionResult.class_name == normalized_class))
    total = query.distinct().count()
    rows = (
        query.options(
            selectinload(DetectionRecord.results),
            selectinload(DetectionRecord.user),
            selectinload(DetectionRecord.model),
        )
        .distinct()
        .order_by(DetectionRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_record_to_item(db, row) for row in rows], total


def get_record(db: Session, record_id: int) -> dict:
    record = (
        db.query(DetectionRecord)
        .options(
            selectinload(DetectionRecord.results),
            selectinload(DetectionRecord.user),
            selectinload(DetectionRecord.model),
        )
        .filter(DetectionRecord.id == record_id)
        .first()
    )
    if record is None:
        raise AppException(40404, "Detection record not found", 404)
    results = [_result_to_dict(db, row, record.model_id) for row in record.results]
    item = _record_to_item(db, record)
    item.update({"results": results, "analysis": _analysis_with_zh(results)})
    return item


def delete_records(db: Session, ids: list[int]) -> int:
    rows = db.query(DetectionRecord).filter(DetectionRecord.id.in_(ids)).all()
    count = len(rows)
    for row in rows:
        db.delete(row)
    db.commit()
    return count
