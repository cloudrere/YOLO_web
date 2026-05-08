from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_chat_log import AIChatLog
from app.models.detection_record import DetectionRecord
from app.models.detection_result import DetectionResult
from app.models.model_info import ModelInfo
from app.models.system_log import SystemLog
from app.models.user import User
from app.services.class_mapping_service import translate_class
from app.services.system_status_service import get_system_status


def _date_range_7d() -> list[date]:
    today = datetime.utcnow().date()
    return [today - timedelta(days=offset) for offset in range(6, -1, -1)]


def get_metrics(db: Session, current_user: User | None = None) -> dict:
    total = db.query(DetectionRecord).count()
    image_count = db.query(DetectionRecord).filter(DetectionRecord.source_type.in_(["image", "batch_image"])).count()
    video_count = db.query(DetectionRecord).filter(DetectionRecord.source_type == "video").count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()

    date_range = _date_range_7d()
    start_date = date_range[0]
    rows = (
        db.query(func.date(DetectionRecord.created_at), func.count(DetectionRecord.id))
        .filter(DetectionRecord.created_at >= datetime.combine(start_date, datetime.min.time()))
        .group_by(func.date(DetectionRecord.created_at))
        .all()
    )
    count_by_date = {str(row[0]): int(row[1]) for row in rows}
    daily_trend = [{"date": str(day), "count": count_by_date.get(str(day), 0)} for day in date_range]

    user_trend_rows = (
        db.query(func.date(DetectionRecord.created_at), User.username, func.count(DetectionRecord.id))
        .join(User, DetectionRecord.user_id == User.id)
        .filter(DetectionRecord.created_at >= datetime.combine(start_date, datetime.min.time()))
        .group_by(func.date(DetectionRecord.created_at), User.username)
        .all()
    )
    user_trend_map: dict[str, dict[str, int]] = {}
    for day, username, count in user_trend_rows:
        user_trend_map.setdefault(str(day), {})[username] = int(count)
    user_detection_trend_7d = [
        {"date": str(day), "users": user_trend_map.get(str(day), {})}
        for day in date_range
    ]

    class_rows = (
        db.query(DetectionResult.class_name, func.count(DetectionResult.id), func.avg(DetectionResult.confidence))
        .group_by(DetectionResult.class_name)
        .order_by(func.count(DetectionResult.id).desc())
        .limit(10)
        .all()
    )
    top_rows = class_rows[:10]
    class_distribution = [
        {
            "class": row[0],
            "class_zh": translate_class(db, row[0]),
            "count": int(row[1]),
            "avg_confidence": round(float(row[2] or 0), 4),
        }
        for row in class_rows
    ]

    model_rows = (
        db.query(func.coalesce(ModelInfo.display_name, ModelInfo.name), func.count(DetectionRecord.id))
        .outerjoin(DetectionRecord, DetectionRecord.model_id == ModelInfo.id)
        .filter(ModelInfo.is_deleted.is_(False))
        .group_by(ModelInfo.id)
        .order_by(func.count(DetectionRecord.id).desc())
        .limit(10)
        .all()
    )
    model_call_ranking = [{"model": row[0], "count": int(row[1])} for row in model_rows]

    ai_rows = (
        db.query(func.date(AIChatLog.created_at), func.count(AIChatLog.id))
        .filter(AIChatLog.created_at >= datetime.combine(start_date, datetime.min.time()))
        .group_by(func.date(AIChatLog.created_at))
        .all()
    )
    ai_count_by_date = {str(row[0]): int(row[1]) for row in ai_rows}
    ai_call_trend_7d = [{"date": str(day), "count": ai_count_by_date.get(str(day), 0)} for day in date_range]

    data = {
        "total_detections": total,
        "image_count": image_count,
        "video_count": video_count,
        "active_users": active_users,
        "daily_trend_7d": daily_trend,
        "user_detection_trend_7d": user_detection_trend_7d,
        "class_distribution": class_distribution,
        "model_call_ranking": model_call_ranking,
        "ai_call_trend_7d": ai_call_trend_7d,
        "top_detected_classes": [
            {"class": row[0], "class_zh": translate_class(db, row[0]), "count": int(row[1])} for row in top_rows
        ],
    }
    if current_user and current_user.is_superuser:
        user_rows = (
            db.query(User.id, User.username, func.count(DetectionRecord.id).label("count"))
            .outerjoin(DetectionRecord, DetectionRecord.user_id == User.id)
            .group_by(User.id, User.username)
            .order_by(func.count(DetectionRecord.id).desc())
            .limit(10)
            .all()
        )
        data["admin"] = {
            "total_users": db.query(User).count(),
            "total_models": db.query(ModelInfo).filter(ModelInfo.is_deleted.is_(False)).count(),
            "abnormal_logs": db.query(SystemLog).filter(SystemLog.level.in_(["warning", "error", "critical"])).count(),
            "ai_call_count": db.query(AIChatLog).count(),
            "user_detection_stats": [
                {"user_id": row[0], "username": row[1], "count": int(row[2])} for row in user_rows
            ],
            "system_status": get_system_status(),
        }
    return data
