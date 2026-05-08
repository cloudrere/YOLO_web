from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.history import BatchDeleteRequest
from app.services.export_service import export_history_xlsx
from app.services.history_service import delete_records, get_record, list_records

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str | None = None,
    class_name: str | None = None,
    class_name_zh: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("history:read")),
):
    items, total = list_records(db, page, page_size, source_type, class_name, user_id, class_name_zh, username)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/export")
def export_history(
    source_type: str | None = None,
    class_name: str | None = None,
    class_name_zh: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("history:read")),
):
    buffer = export_history_xlsx(db, source_type, class_name, class_name_zh, user_id, username)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="history.xlsx"'},
    )


@router.delete("/batch/delete")
def delete_history_batch(
    payload: BatchDeleteRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("history:manage")),
):
    count = delete_records(db, payload.ids)
    return success({"deleted": count})


@router.get("/{record_id}")
def get_history_detail(record_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("history:read"))):
    return success(get_record(db, record_id))


@router.delete("/{record_id}")
def delete_history(record_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("history:manage"))):
    count = delete_records(db, [record_id])
    return success({"deleted": count})
