from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import utc_now


class DetectionRecord(Base):
    __tablename__ = "detection_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("model_infos.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(default="", nullable=False)
    file_path: Mapped[str] = mapped_column(nullable=False)
    original_path: Mapped[str] = mapped_column(default="", nullable=False)
    result_path: Mapped[str] = mapped_column(default="", nullable=False)
    status: Mapped[str] = mapped_column(default="done", nullable=False, index=True)
    duration_ms: Mapped[int] = mapped_column(default=0, nullable=False)
    confidence_threshold: Mapped[float] = mapped_column(default=0.25, nullable=False)
    iou_threshold: Mapped[float] = mapped_column(default=0.7, nullable=False)
    save_history: Mapped[bool] = mapped_column(default=True, nullable=False)
    model_name: Mapped[str] = mapped_column(default="", nullable=False)
    device: Mapped[str] = mapped_column(default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False, index=True)

    user: Mapped[User | None] = relationship("User", back_populates="records")
    model: Mapped[ModelInfo | None] = relationship("ModelInfo", back_populates="records")
    results: Mapped[list[DetectionResult]] = relationship(
        "DetectionResult", back_populates="record", cascade="all, delete-orphan"
    )
