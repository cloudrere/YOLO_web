from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.utils.time import utc_now


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(default="pending", nullable=False, index=True)
    progress: Mapped[float] = mapped_column(default=0.0, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    record_id: Mapped[int | None] = mapped_column(ForeignKey("detection_records.id", ondelete="SET NULL"), nullable=True, index=True)
    payload_json: Mapped[str] = mapped_column(default="{}", nullable=False)
    result_json: Mapped[str] = mapped_column(default="{}", nullable=False)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(default=2, nullable=False)
    error_message: Mapped[str] = mapped_column(default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False, index=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
