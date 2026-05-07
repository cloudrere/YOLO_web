from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import utc_now


class DetectionResult(Base):
    __tablename__ = "detection_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("detection_records.id", ondelete="CASCADE"), index=True)
    class_name: Mapped[str] = mapped_column(nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)
    x1: Mapped[float] = mapped_column(nullable=False)
    y1: Mapped[float] = mapped_column(nullable=False)
    x2: Mapped[float] = mapped_column(nullable=False)
    y2: Mapped[float] = mapped_column(nullable=False)
    frame_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)

    record: Mapped[DetectionRecord] = relationship("DetectionRecord", back_populates="results")
