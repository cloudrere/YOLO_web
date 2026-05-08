from sqlalchemy.orm import Session, selectinload

from app.core.response import AppException
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.role import Role
from app.models.user import User
from app.utils.time import utc_now


def collect_permissions(user: User) -> list[str]:
    permissions = sorted({permission.code for role in user.roles for permission in role.permissions})
    return permissions


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).options(selectinload(User.roles).selectinload(Role.permissions)).filter(User.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        raise AppException(40102, "Invalid username or password", 401)
    if not user.is_active:
        raise AppException(40103, "User is disabled", 403)
    user.last_login_at = utc_now()
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, username: str, password: str) -> dict:
    user = authenticate_user(db, username, password)
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer", "user": user, "permissions": collect_permissions(user)}


def create_user(
    db: Session,
    username: str,
    password: str,
    is_active: bool = True,
    is_superuser: bool = False,
    role_ids: list[int] | None = None,
    role_names: list[str] | None = None,
) -> User:
    username = username.strip()
    password = password.strip()
    if not username or not password:
        raise AppException(40010, "Username and password are required")
    if db.query(User).filter(User.username == username).first() is not None:
        raise AppException(40010, "Username already exists")
    roles = []
    if role_ids:
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    elif role_names:
        roles = db.query(Role).filter(Role.name.in_(role_names)).all()
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        is_active=is_active,
        is_superuser=is_superuser,
        roles=roles,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_user(db: Session, username: str, password: str) -> User:
    return create_user(db, username, password, True, False, role_names=["operator"])


def reset_password(db: Session, username: str, new_password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise AppException(40401, "User not found", 404)
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user
