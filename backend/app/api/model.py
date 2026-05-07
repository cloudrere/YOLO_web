from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.model import ModelCreateRequest, ModelOut
from app.services.log_service import create_log
from app.services.model_service import activate_model, active_model_state, create_model, list_models, upload_model

router = APIRouter(prefix="/models", tags=["models"])


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


@router.post("/{model_id}/activate")
def activate_model_api(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("model:manage")),
):
    item = activate_model(db, model_id)
    create_log(db, "model", f"Activated model {item.name}", module="model", user_id=current_user.id)
    return success(ModelOut.model_validate(item).model_dump())


@router.get("/active")
def active_model_api(db: Session = Depends(get_db), _: User = Depends(require_permission("model:read"))):
    data = active_model_state(db)
    active = data.pop("active_model")
    data["active_model"] = ModelOut.model_validate(active).model_dump() if active else None
    return success(data)
