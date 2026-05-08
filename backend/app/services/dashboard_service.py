from datetime import datetime, timedelta

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


def get_metrics(db: Session, current_user: User | None = None) -> dict:
    total = db.query(DetectionRecord).count()
    image_count = db.query(DetectionRecord).filter(DetectionRecord.source_type.in_(["image", "batch_image"])).count()
    video_count = db.query(DetectionRecord).filter(DetectionRecord.source_type == "video").count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=6)
    rows = (
        db.query(func.date(DetectionRecord.created_at), func.count(DetectionRecord.id))
        .filter(DetectionRecord.created_at >= datetime.combine(start_date, datetime.min.time()))
        .group_by(func.date(DetectionRecord.created_at))
        .all()
    )
    count_by_date = {str(row[0]): int(row[1]) for row in rows}
    daily_trend = [
        {"date": str(start_date + timedelta(days=offset)), "count": count_by_date.get(str(start_date + timedelta(days=offset)), 0)}
        for offset in range(7)
    ]

    top_rows = (
        db.query(DetectionResult.class_name, func.count(DetectionResult.id).label("count"))
        .group_by(DetectionResult.class_name)
        .order_by(func.count(DetectionResult.id).desc())
        .limit(10)
        .all()
    )
    data = {
        "total_detections": total,
        "image_count": image_count,
        "video_count": video_count,
        "active_users": active_users,
        "daily_trend_7d": daily_trend,
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
