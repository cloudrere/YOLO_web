from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import utc_now


class ModelInfo(Base):
    __tablename__ = "model_infos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(default="", nullable=False)
    path: Mapped[str] = mapped_column(nullable=False)
    version: Mapped[str] = mapped_column(default="", nullable=False)
    class_names_json: Mapped[str] = mapped_column(default="[]", nullable=False)
    class_mapping_json: Mapped[str] = mapped_column(default="{}", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    device: Mapped[str] = mapped_column(default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now, nullable=False)

    records: Mapped[list[DetectionRecord]] = relationship("DetectionRecord", back_populates="model")
