from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(default="", nullable=False)

    roles: Mapped[list[Role]] = relationship("Role", secondary="role_permissions", back_populates="permissions")
