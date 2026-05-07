from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    path: str
    version: str
    class_names_json: str
    is_active: bool
    device: str
    created_at: datetime
    updated_at: datetime


class ModelCreateRequest(BaseModel):
    name: str
    path: str
    version: str = ""
    class_names: list[str] = []


class ActiveModelOut(BaseModel):
    active_model: ModelOut | None
    engine_loaded: bool
    device: str
    cuda_available: bool
    model_path: str
