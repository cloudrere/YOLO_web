from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, UserOut
from app.services.auth_service import collect_permissions, login
from app.services.log_service import create_log

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login_api(payload: LoginRequest, db: Session = Depends(get_db)):
    data = login(db, payload.username, payload.password)
    create_log(db, "auth", f"User {payload.username} logged in", module="auth", user_id=data["user"].id)
    data["user"] = UserOut.model_validate(data["user"]).model_dump()
    return success(data)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return success({"user": UserOut.model_validate(current_user).model_dump(), "permissions": collect_permissions(current_user)})


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return success({"username": current_user.username})
