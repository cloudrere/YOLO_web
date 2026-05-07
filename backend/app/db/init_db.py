from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import Base, engine
from app.models import ModelInfo, Permission, Role, User

PERMISSIONS = [
    ("detect:run", "Run detection", "Upload and run image or video detection"),
    ("history:read", "Read history", "Read detection history"),
    ("history:manage", "Manage history", "Delete detection history"),
    ("model:read", "Read models", "Read model information"),
    ("model:manage", "Manage models", "Upload, register, and activate models"),
    ("log:read", "Read logs", "Read system logs"),
    ("admin:user", "Manage users", "Manage users, roles, and permissions"),
]


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_storage_dirs() -> None:
    for path in (settings.uploads_path, settings.results_path, settings.models_path):
        path.mkdir(parents=True, exist_ok=True)


def init_permissions(db: Session) -> list[Permission]:
    permissions: list[Permission] = []
    for code, name, description in PERMISSIONS:
        permission = db.query(Permission).filter(Permission.code == code).first()
        if permission is None:
            permission = Permission(code=code, name=name, description=description)
            db.add(permission)
        permissions.append(permission)
    db.flush()
    return permissions


def init_roles(db: Session, permissions: list[Permission]) -> Role:
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if admin_role is None:
        admin_role = Role(name="admin", description="System administrator")
        db.add(admin_role)
    admin_role.permissions = permissions

    operator_role = db.query(Role).filter(Role.name == "operator").first()
    if operator_role is None:
        operator_role = Role(name="operator", description="Detection operator")
        db.add(operator_role)
    operator_role.permissions = [p for p in permissions if p.code in {"detect:run", "history:read", "model:read"}]
    db.flush()
    return admin_role


def init_admin_user(db: Session, admin_role: Role) -> None:
    admin = db.query(User).filter(User.username == settings.admin_username).first()
    if admin is None:
        admin = User(
            username=settings.admin_username,
            password_hash=get_password_hash(settings.admin_password),
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
    admin.roles = [admin_role]


def init_default_model(db: Session) -> None:
    if not settings.default_model_path:
        return
    model_path = Path(settings.default_model_path)
    if not model_path.is_absolute():
        model_path = settings.models_path / model_path
    if not model_path.exists():
        return
    existing = db.query(ModelInfo).filter(ModelInfo.path == str(model_path)).first()
    if existing is None:
        db.query(ModelInfo).update({ModelInfo.is_active: False})
        db.add(ModelInfo(name=model_path.stem, path=str(model_path), is_active=True))


def init_db(db: Session) -> None:
    ensure_storage_dirs()
    permissions = init_permissions(db)
    admin_role = init_roles(db, permissions)
    init_admin_user(db, admin_role)
    init_default_model(db)
    db.commit()
