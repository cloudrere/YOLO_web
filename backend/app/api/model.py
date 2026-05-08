from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.model import ClassMappingUpdateRequest, DeviceSwitchRequest, ModelCreateRequest, ModelDisplayNameRequest, ModelOut
from app.services.log_service import create_log
from app.services.model_service import (
    activate_model,
    active_model_state,
    create_model,
    delete_model,
    device_state,
    list_models,
    switch_active_device,
    update_model_class_mapping,
    update_model_display_name,
    upload_model,
)

router = APIRouter(prefix="/models", tags=["models"])


def serialize_active_state(data: dict) -> dict:
    active = data.pop("active_model")
    data["active_model"] = ModelOut.model_validate(active).model_dump() if active else None
    return data


@router.get("")
def get_models(db: Session = Depends(get_db), _: User = Depends(require_permission("model:read"))):
    return success({"items": [ModelOut.model_validate(item).model_dump() for item in list_models(db)]})


@router.post("")
def post_model(payload: ModelCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_permission("model:manage"))):
    item = create_model(db, payload.name, payload.path, payload.version, payload.class_names)
    return success(ModelOut.model_validate(item).model_dump(), "created")


@router.post("/upload")
def upload_model_api(
    file: UploadFile = File(...),
    name: str | None = Form(None),
    version: str = Form(""),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("model:manage")),
):
    item = upload_model(db, file, name, version)
    return success(ModelOut.model_validate(item).model_dump(), "uploaded")


@router.get("/devices")
def get_model_devices(db: Session = Depends(get_db), _: User = Depends(require_permission("model:read"))):
    data = {"active_model": active_model_state(db)["active_model"], **device_state()}
    return success(serialize_active_state(data))


@router.post("/device")
def switch_model_device_api(
    payload: DeviceSwitchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("model:manage")),
):
    data = switch_active_device(db, payload.device)
    create_log(db, "model", f"Switched model device to {payload.device}", module="model", user_id=current_user.id)
    return success(serialize_active_state(data))


@router.get("/active")
def active_model_api(db: Session = Depends(get_db), _: User = Depends(require_permission("model:read"))):
    return success(serialize_active_state(active_model_state(db)))


@router.post("/{model_id}/activate")
def activate_model_api(
    model_id: int,
    payload: DeviceSwitchRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("model:manage")),
):
    item = activate_model(db, model_id, payload.device if payload else None)
    create_log(db, "model", f"Activated model {item.name}", module="model", user_id=current_user.id)
    return success(ModelOut.model_validate(item).model_dump())


@router.patch("/{model_id}/display-name")
def patch_model_display_name(
    model_id: int,
    payload: ModelDisplayNameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("model:manage")),
):
    item = update_model_display_name(db, model_id, payload.display_name)
    create_log(db, "model", f"Updated model display name {model_id}", module="model", user_id=current_user.id)
    return success(ModelOut.model_validate(item).model_dump())


@router.patch("/{model_id}/class-mapping")
def patch_model_class_mapping(
    model_id: int,
    payload: ClassMappingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("model:manage")),
):
    item = update_model_class_mapping(db, model_id, payload.mapping)
    create_log(db, "model", f"Updated model class mapping {model_id}", module="model", user_id=current_user.id)
    return success(ModelOut.model_validate(item).model_dump())


@router.delete("/{model_id}")
def delete_model_api(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("model:manage")),
):
    delete_model(db, model_id)
    create_log(db, "model", f"Deleted model {model_id}", module="model", user_id=current_user.id)
    return success({"deleted": True})
