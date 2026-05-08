import json

from sqlalchemy.orm import Session

from app.constants.coco_classes import default_class_mapping
from app.models.class_name_mapping import ClassNameMapping
from app.models.model_info import ModelInfo


def load_model_mapping(db: Session, model_id: int | None = None) -> dict[str, str]:
    mapping = default_class_mapping()
    if model_id:
        model = db.get(ModelInfo, model_id)
        if model and model.class_mapping_json:
            try:
                mapping.update({str(k): str(v) for k, v in json.loads(model.class_mapping_json).items()})
            except json.JSONDecodeError:
                pass
        rows = db.query(ClassNameMapping).filter(ClassNameMapping.model_id == model_id).all()
        mapping.update({row.class_name: row.class_name_zh or row.class_name for row in rows})
    global_rows = db.query(ClassNameMapping).filter(ClassNameMapping.model_id.is_(None)).all()
    for row in global_rows:
        mapping.setdefault(row.class_name, row.class_name_zh or row.class_name)
    return mapping


def translate_class(db: Session, class_name: str, model_id: int | None = None) -> str:
    return load_model_mapping(db, model_id).get(class_name, class_name)


def decorate_detection(db: Session, item: dict, model_id: int | None = None, frame_id: int | None = None) -> dict:
    class_name = str(item["class"])
    output = {
        "class": class_name,
        "class_zh": translate_class(db, class_name, model_id),
        "confidence": float(item["confidence"]),
        "bbox": tuple(float(v) for v in item["bbox"]),
        "frame_id": item.get("frame_id", frame_id),
    }
    return output


def reverse_lookup_class(db: Session, value: str | None, model_id: int | None = None) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    mapping = load_model_mapping(db, model_id)
    if normalized in mapping:
        return normalized
    for class_name, class_name_zh in mapping.items():
        if normalized == class_name_zh:
            return class_name
    return normalized


def save_model_class_mapping(db: Session, model: ModelInfo, mapping: dict[str, str]) -> ModelInfo:
    model.class_mapping_json = json.dumps(mapping, ensure_ascii=False)
    for class_name, class_name_zh in mapping.items():
        row = db.query(ClassNameMapping).filter(ClassNameMapping.model_id == model.id, ClassNameMapping.class_name == class_name).first()
        if row is None:
            db.add(ClassNameMapping(model_id=model.id, class_name=class_name, class_name_zh=class_name_zh))
        else:
            row.class_name_zh = class_name_zh
    db.commit()
    db.refresh(model)
    return model
