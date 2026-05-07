from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.response import AppException
from app.models.detection_record import DetectionRecord
from app.models.detection_result import DetectionResult
from app.services.ai_analysis_service import analyze_detection_results


def list_records(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    source_type: str | None = None,
    class_name: str | None = None,
    user_id: int | None = None,
) -> tuple[list[dict], int]:
    query = db.query(DetectionRecord)
    if source_type:
        query = query.filter(DetectionRecord.source_type == source_type)
    if user_id:
        query = query.filter(DetectionRecord.user_id == user_id)
    if class_name:
        query = query.join(DetectionResult).filter(DetectionResult.class_name == class_name)
    total = query.distinct(DetectionRecord.id).count()
    rows = (
        query.options(selectinload(DetectionRecord.results))
        .order_by(DetectionRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        {
            "id": row.id,
            "user_id": row.user_id,
            "model_id": row.model_id,
            "source_type": row.source_type,
            "file_name": row.file_name,
            "file_path": row.file_path,
            "status": row.status,
            "duration_ms": row.duration_ms,
            "created_at": row.created_at,
            "result_count": len(row.results),
        }
        for row in rows
    ]
    return items, total


def get_record(db: Session, record_id: int) -> dict:
    record = db.query(DetectionRecord).options(selectinload(DetectionRecord.results)).filter(DetectionRecord.id == record_id).first()
    if record is None:
        raise AppException(40404, "Detection record not found", 404)
    results = [
        {
            "class": row.class_name,
            "confidence": row.confidence,
            "bbox": (row.x1, row.y1, row.x2, row.y2),
            "frame_id": row.frame_id,
        }
        for row in record.results
    ]
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
    }


def delete_records(db: Session, ids: list[int]) -> int:
    rows = db.query(DetectionRecord).filter(DetectionRecord.id.in_(ids)).all()
    count = len(rows)
    for row in rows:
        db.delete(row)
    db.commit()
    return count
