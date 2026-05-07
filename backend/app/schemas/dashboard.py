from pydantic import BaseModel, Field


class DailyTrendItem(BaseModel):
    date: str
    count: int


class TopClassItem(BaseModel):
    class_name: str = Field(serialization_alias="class", alias="class")
    count: int


class DashboardMetrics(BaseModel):
    total_detections: int
    image_count: int
    video_count: int
    active_users: int
    daily_trend_7d: list[DailyTrendItem]
    top_detected_classes: list[TopClassItem]
