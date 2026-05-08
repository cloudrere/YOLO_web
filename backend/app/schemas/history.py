from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.detect import AIAnalysisOut, DetectionResultOut


class HistoryClassSummary(BaseModel):
    class_name: str
    class_zh: str
    count: int
    avg_confidence: float = 0.0


class DetectionRecordListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    username: str = ""
    model_id: int | None
    model_name: str = ""
    source_type: str
    file_name: str
    file_path: str
    original_path: str = ""
    result_path: str = ""
    original_url: str = ""
    result_url: str = ""
    status: str
    duration_ms: int
    created_at: datetime
    result_count: int = 0
    classes: list[HistoryClassSummary] = []
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.7
    save_history: bool = True
    device: str = ""
    parameters: dict = {}


class DetectionRecordDetail(BaseModel):
    id: int
    user_id: int | None
    username: str = ""
    model_id: int | None
    model_name: str = ""
    source_type: str
    file_name: str
    file_path: str
    original_path: str = ""
    result_path: str
    original_url: str = ""
    result_url: str = ""
    status: str
    duration_ms: int
    created_at: datetime
    result_count: int = 0
    classes: list[HistoryClassSummary] = []
    results: list[DetectionResultOut]
    analysis: AIAnalysisOut
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.7
    save_history: bool = True
    device: str = ""
    parameters: dict = {}


class BatchDeleteRequest(BaseModel):
    ids: list[int]
