from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import RoleCreateRequest, RoleUpdateRequest, UserCreateRequest, UserUpdateRequest
from app.schemas.auth import PermissionOut, RoleOut, UserOut
from app.services.auth_service import create_user
from app.services.role_service import create_role, list_permissions, list_roles, update_role
from app.services.user_service import delete_user, list_users, update_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def get_users(
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:user")),
):
    items, total = list_users(db, keyword)
    return success({"items": [UserOut.model_validate(item).model_dump() for item in items], "total": total})


@router.post("/users")
def post_user(payload: UserCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    item = create_user(db, payload.username, payload.password, payload.is_active, payload.is_superuser, payload.role_ids)
    return success(UserOut.model_validate(item).model_dump(), "created")


@router.put("/users/{user_id}")
def put_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:user")),
):
    item = update_user(db, user_id, payload.password, payload.is_active, payload.is_superuser, payload.role_ids)
    return success(UserOut.model_validate(item).model_dump())


@router.delete("/users/{user_id}")
def remove_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    delete_user(db, user_id)
    return success({"deleted": True})


@router.get("/roles")
def get_roles(db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    items, total = list_roles(db)
    return success({"items": [RoleOut.model_validate(item).model_dump() for item in items], "total": total})


@router.post("/roles")
def post_role(payload: RoleCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    item = create_role(db, payload.name, payload.description, payload.permission_ids)
    return success(RoleOut.model_validate(item).model_dump(), "created")


@router.put("/roles/{role_id}")
def put_role(
    role_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:user")),
):
    item = update_role(db, role_id, payload.description, payload.permission_ids)
    return success(RoleOut.model_validate(item).model_dump())


@router.get("/permissions")
def get_permissions(db: Session = Depends(get_db), _: User = Depends(require_permission("admin:user"))):
    items, total = list_permissions(db)
    return success({"items": [PermissionOut.model_validate(item).model_dump() for item in items], "total": total})
