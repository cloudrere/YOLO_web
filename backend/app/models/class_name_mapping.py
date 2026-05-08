from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.utils.time import utc_now


class ClassNameMapping(Base):
    __tablename__ = "class_name_mappings"
    __table_args__ = (UniqueConstraint("model_id", "class_name", name="uq_model_class_mapping"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("model_infos.id", ondelete="CASCADE"), nullable=True, index=True)
    class_name: Mapped[str] = mapped_column(nullable=False, index=True)
    class_name_zh: Mapped[str] = mapped_column(default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now, nullable=False)
