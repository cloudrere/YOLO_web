from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DetectionResultOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_name: str = Field(serialization_alias="class", alias="class")
    confidence: float
    bbox: tuple[float, float, float, float]
    frame_id: int | None = None


class ClassDistributionItem(BaseModel):
    class_name: str = Field(serialization_alias="class", alias="class")
    count: int
    avg_confidence: float
    ratio: float


class AIAnalysisOut(BaseModel):
    summary: str
    class_distribution: list[ClassDistributionItem]
    anomaly_tips: list[str]


class ImageDetectResponse(BaseModel):
    record_id: int
    results: list[DetectionResultOut]
    analysis: AIAnalysisOut
    duration_ms: int


class BatchItemResponse(BaseModel):
    file_name: str
    status: str
    record_id: int | None = None
    results: list[DetectionResultOut] = []
    analysis: AIAnalysisOut | None = None
    error: str = ""


class BatchDetectResponse(BaseModel):
    items: list[BatchItemResponse]


class VideoTaskResponse(BaseModel):
    task_id: int
    record_id: int
    status: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    status: str
    progress: float
    record_id: int | None = None
    retry_count: int
    max_retries: int
    error_message: str
    result_json: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
