from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.utils.time import utc_now


class TrainingAnalysisRecord(Base):
    __tablename__ = "training_analysis_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    path: Mapped[str] = mapped_column(nullable=False)
    rows: Mapped[int] = mapped_column(default=0, nullable=False)
    best_epoch: Mapped[int | None] = mapped_column(nullable=True)
    best_map50: Mapped[float | None] = mapped_column(nullable=True)
    best_map5095: Mapped[float | None] = mapped_column(nullable=True)
    file_size: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now, nullable=False)
