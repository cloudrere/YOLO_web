from sqlalchemy.orm import Session

from app.models.system_log import SystemLog


def create_log(
    db: Session,
    log_type: str,
    message: str,
    level: str = "info",
    module: str = "system",
    user_id: int | None = None,
    request_id: str = "",
) -> SystemLog:
    item = SystemLog(type=log_type, level=level, module=module, message=message, user_id=user_id, request_id=request_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_logs(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    level: str | None = None,
    module: str | None = None,
    log_type: str | None = None,
) -> tuple[list[SystemLog], int]:
    query = db.query(SystemLog)
    if level:
        query = query.filter(SystemLog.level == level)
    if module:
        query = query.filter(SystemLog.module == module)
    if log_type:
        query = query.filter(SystemLog.type == log_type)
    total = query.count()
    items = query.order_by(SystemLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total
