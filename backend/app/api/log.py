from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.system_log import SystemLog
from app.models.user import User
from app.schemas.log import LogCleanupRequest, LogOut
from app.services.log_service import list_logs

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    level: str | None = None,
    module: str | None = None,
    log_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log:read")),
):
    items, total = list_logs(db, page, page_size, level, module, log_type)
    return success(
        {
            "items": [LogOut.model_validate(item).model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.delete("/cleanup")
def cleanup_logs(
    payload: LogCleanupRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log:read")),
):
    before = datetime.utcnow() - timedelta(days=payload.before_days)
    deleted = db.query(SystemLog).filter(SystemLog.created_at < before).delete(synchronize_session=False)
    db.commit()
    return success({"deleted": deleted})
