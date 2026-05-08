from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.services.log_service import create_log
from app.services.maintenance_service import (
    clear_detection_history,
    clear_logs,
    clear_models,
    get_maintenance_status,
    restore_initial_state,
)

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/status")
def maintenance_status(db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    return success(get_maintenance_status(db))


@router.delete("/history")
def clear_history(db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin:user"))):
    count = clear_detection_history(db)
    create_log(db, "system", f"系统维护已清除检测历史，共 {count} 条记录", module="maintenance", user_id=current_user.id)
    return success({"deleted": count})


@router.delete("/logs")
def clear_system_logs(db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    count = clear_logs(db)
    return success({"deleted": count})


@router.delete("/models")
def clear_non_active_models(db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin:user"))):
    count = clear_models(db)
    create_log(db, "system", f"系统维护已清除非激活模型，共 {count} 条记录", module="maintenance", user_id=current_user.id)
    return success({"deleted": count})


@router.post("/restore-initial")
def restore_initial(db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    result = restore_initial_state(db)
    return success(result)
