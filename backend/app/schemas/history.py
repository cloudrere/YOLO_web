from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.detect import AIAnalysisOut, DetectionResultOut


class DetectionRecordListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    model_id: int | None
    source_type: str
    file_name: str
    file_path: str
    status: str
    duration_ms: int
    created_at: datetime
    result_count: int = 0


class DetectionRecordDetail(BaseModel):
    id: int
    user_id: int | None
    model_id: int | None
    source_type: str
    file_name: str
    file_path: str
    result_path: str
    status: str
    duration_ms: int
    created_at: datetime
    results: list[DetectionResultOut]
    analysis: AIAnalysisOut
    result_url: str = ""


class BatchDeleteRequest(BaseModel):
    ids: list[int]
