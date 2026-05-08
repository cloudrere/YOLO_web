from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, ResetPasswordRequest, UserOut
from app.services.auth_service import collect_permissions, login, register_user, reset_password
from app.services.log_service import create_log

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login_api(payload: LoginRequest, db: Session = Depends(get_db)):
    data = login(db, payload.username, payload.password)
    create_log(db, "auth", f"用户 {payload.username} 已登录", module="auth", user_id=data["user"].id)
    data["user"] = UserOut.model_validate(data["user"]).model_dump()
    return success(data)


@router.post("/register")
def register_api(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, payload.username, payload.password)
    create_log(db, "auth", f"用户 {payload.username} 已注册", module="auth", user_id=user.id)
    return success(UserOut.model_validate(user).model_dump(), "registered")


@router.post("/reset-password")
def reset_password_api(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = reset_password(db, payload.username, payload.new_password)
    create_log(db, "auth", f"用户 {payload.username} 已重置密码", module="auth", user_id=user.id)
    return success({"username": user.username}, "password reset")


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return success({"user": UserOut.model_validate(current_user).model_dump(), "permissions": collect_permissions(current_user)})


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return success({"username": current_user.username})
