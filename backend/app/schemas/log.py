from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    level: str
    module: str
    message: str
    user_id: int | None
    request_id: str
    created_at: datetime


class LogListResponse(BaseModel):
    items: list[LogOut]
    total: int
    page: int
    page_size: int


class LogCleanupRequest(BaseModel):
    before_days: int = 30
