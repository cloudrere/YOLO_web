from sqlalchemy.orm import Session, selectinload

from app.core.response import AppException
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User


def list_users(db: Session, keyword: str | None = None) -> tuple[list[User], int]:
    query = db.query(User).options(selectinload(User.roles).selectinload(Role.permissions)).order_by(User.id.asc())
    if keyword:
        query = query.filter(User.username.contains(keyword.strip()))
    return query.all(), query.count()


def update_user(
    db: Session,
    user_id: int,
    password: str | None = None,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    role_ids: list[int] | None = None,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppException(40401, "User not found", 404)
    if password:
        user.password_hash = get_password_hash(password)
    if is_active is not None:
        user.is_active = is_active
    if is_superuser is not None:
        user.is_superuser = is_superuser
    if role_ids is not None:
        user.roles = db.query(Role).filter(Role.id.in_(role_ids)).all() if role_ids else []
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise AppException(40401, "User not found", 404)
    db.delete(user)
    db.commit()
