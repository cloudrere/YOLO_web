import json
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import AppException
from app.core.yolo_engine import yolo_engine
from app.models.model_info import ModelInfo
from app.utils.files import save_upload_file


def list_models(db: Session) -> list[ModelInfo]:
    return db.query(ModelInfo).order_by(ModelInfo.created_at.desc()).all()


def get_active_model(db: Session) -> ModelInfo | None:
    return db.query(ModelInfo).filter(ModelInfo.is_active.is_(True)).first()


def create_model(db: Session, name: str, path: str, version: str = "", class_names: list[str] | None = None) -> ModelInfo:
    model_path = Path(path)
    if not model_path.is_absolute():
        model_path = settings.models_path / model_path
    if not model_path.exists():
        raise AppException(40001, f"Model file not found: {model_path}")
    item = ModelInfo(
        name=name,
        path=str(model_path),
        version=version,
        class_names_json=json.dumps(class_names or [], ensure_ascii=False),
        is_active=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def upload_model(db: Session, file: UploadFile, name: str | None = None, version: str = "") -> ModelInfo:
    saved = save_upload_file(file, settings.models_path)
    item = ModelInfo(name=name or saved.stem, path=str(saved), version=version, class_names_json="[]", is_active=False)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def activate_model(db: Session, model_id: int) -> ModelInfo:
    item = db.get(ModelInfo, model_id)
    if item is None:
        raise AppException(40403, "Model not found", 404)
    yolo_engine.switch_model(item.path)
    db.query(ModelInfo).update({ModelInfo.is_active: False})
    item.is_active = True
    item.device = yolo_engine.device
    item.class_names_json = json.dumps(yolo_engine.class_names, ensure_ascii=False)
    db.commit()
    db.refresh(item)
    return item


def ensure_active_model_loaded(db: Session) -> ModelInfo:
    active = get_active_model(db)
    if active is None:
        raise AppException(40003, "No active model configured")
    if not yolo_engine.is_loaded or yolo_engine.model_path != active.path:
        yolo_engine.load_model(active.path)
        active.device = yolo_engine.device
        active.class_names_json = json.dumps(yolo_engine.class_names, ensure_ascii=False)
        db.commit()
    return active


def active_model_state(db: Session) -> dict:
    return {"active_model": get_active_model(db), **yolo_engine.state()}
