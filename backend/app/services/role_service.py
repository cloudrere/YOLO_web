from sqlalchemy.orm import Session, selectinload

from app.core.response import AppException
from app.models.permission import Permission
from app.models.role import Role


def list_roles(db: Session) -> tuple[list[Role], int]:
    query = db.query(Role).options(selectinload(Role.permissions)).order_by(Role.id.asc())
    return query.all(), query.count()


def list_permissions(db: Session) -> tuple[list[Permission], int]:
    query = db.query(Permission).order_by(Permission.id.asc())
    return query.all(), query.count()


def create_role(db: Session, name: str, description: str, permission_ids: list[int]) -> Role:
    if db.query(Role).filter(Role.name == name).first() is not None:
        raise AppException(40011, "Role already exists")
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all() if permission_ids else []
    role = Role(name=name, description=description, permissions=permissions)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role_id: int, description: str | None, permission_ids: list[int] | None) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise AppException(40402, "Role not found", 404)
    if description is not None:
        role.description = description
    if permission_ids is not None:
        role.permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all() if permission_ids else []
    db.commit()
    db.refresh(role)
    return role
