from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    status: str
    progress: float
    user_id: int | None
    record_id: int | None
    result_json: str
    retry_count: int
    max_retries: int
    error_message: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
