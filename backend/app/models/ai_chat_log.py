from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.utils.time import utc_now


class AIChatLog(Base):
    __tablename__ = "ai_chat_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(default="openai-compatible", nullable=False)
    model: Mapped[str] = mapped_column(default="", nullable=False)
    question: Mapped[str] = mapped_column(default="", nullable=False)
    answer: Mapped[str] = mapped_column(default="", nullable=False)
    status: Mapped[str] = mapped_column(default="success", nullable=False, index=True)
    error_message: Mapped[str] = mapped_column(default="", nullable=False)
    duration_ms: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False, index=True)
