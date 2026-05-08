from datetime import datetime
from typing import Any

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


class DeviceSwitchRequest(BaseModel):
    device: str


class DeviceOptionOut(BaseModel):
    value: str
    label: str
    type: str
    available: bool = True
    total_memory: int | None = None


class ActiveModelOut(BaseModel):
    active_model: ModelOut | None
    engine_loaded: bool
    device: str
    requested_device: str = "auto"
    available_devices: list[dict[str, Any]] = []
    cuda_available: bool
    cuda_name: str = ""
    model_path: str
    warmup_status: str = "idle"
    warmup_error: str = ""
