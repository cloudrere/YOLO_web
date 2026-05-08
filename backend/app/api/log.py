from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.system_log import SystemLog
from app.models.user import User
from app.schemas.log import LogBatchDeleteRequest, LogCleanupRequest, LogDateDeleteRequest
from app.services.log_i18n_service import decorate_log
from app.services.log_service import delete_log, delete_logs, delete_logs_by_date, list_logs

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
            "items": [decorate_log(item) for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.delete("/batch/delete")
def delete_logs_batch_api(
    payload: LogBatchDeleteRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log:read")),
):
    return success({"deleted": delete_logs(db, payload.ids)})


@router.delete("/by-date")
def delete_logs_by_date_api(
    payload: LogDateDeleteRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log:read")),
):
    return success({"deleted": delete_logs_by_date(db, payload.start_date, payload.end_date)})


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


@router.delete("/{log_id}")
def delete_log_api(
    log_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("log:read")),
):
    return success({"deleted": delete_log(db, log_id)})
