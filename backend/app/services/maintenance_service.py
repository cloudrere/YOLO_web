from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.init_db import ensure_storage_dirs, init_db
from app.models.detection_record import DetectionRecord
from app.models.detection_result import DetectionResult
from app.models.model_info import ModelInfo
from app.models.task import Task
from app.models.system_log import SystemLog
from app.services.system_status_service import get_system_status


def get_maintenance_status(db: Session) -> dict:
    system_status = get_system_status()
    return {
        "gpu": build_gpu_status(system_status),
        "model": build_model_status(db),
        "database": build_database_status(),
        "filesystem": build_filesystem_status(),
    }


def build_gpu_status(system_status: dict) -> dict:
    devices = system_status.get("gpu_devices") or []
    return {
        "cuda_available": bool(system_status.get("cuda_available")),
        "torch_available": bool(system_status.get("torch_version")),
        "torch_version": system_status.get("torch_version") or "",
        "torch_cuda_version": system_status.get("torch_cuda_version") or "",
        "device_count": int(system_status.get("cuda_device_count") or 0),
        "gpu_name": devices[0].get("name", "") if devices else "",
        "memory_total": devices[0].get("total_memory", 0) if devices else 0,
        "memory_reserved": devices[0].get("reserved_memory", 0) if devices else 0,
        "memory_allocated": devices[0].get("allocated_memory", 0) if devices else 0,
        "diagnostics": system_status.get("diagnostics", {}).get("checks", []),
    }


def build_model_status(db: Session) -> dict:
    active = db.query(ModelInfo).filter(ModelInfo.is_active.is_(True), ModelInfo.is_deleted.is_(False)).first()
    model_path = Path(active.path) if active else None
    return {
        "active_model_id": active.id if active else None,
        "active_model_name": (active.display_name or active.name) if active else "",
        "active_model_path": str(model_path) if model_path else "",
        "active_model_exists": bool(model_path and model_path.exists() and model_path.is_file()),
        "active_model_size": model_path.stat().st_size if model_path and model_path.exists() and model_path.is_file() else 0,
        "total_models": db.query(ModelInfo).filter(ModelInfo.is_deleted.is_(False)).count(),
    }


def build_database_status() -> dict:
    required_tables = {
        "users",
        "roles",
        "permissions",
        "model_infos",
        "detection_records",
        "detection_results",
        "system_logs",
        "tasks",
        "class_name_mappings",
        "ai_chat_logs",
        "training_analysis_records",
    }
    try:
        inspector = inspect(db_engine())
        tables = set(inspector.get_table_names())
        missing = sorted(required_tables - tables)
        with db_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"connected": True, "tables_ok": not missing, "missing_tables": missing, "table_count": len(tables)}
    except Exception as exc:
        return {"connected": False, "tables_ok": False, "missing_tables": sorted(required_tables), "table_count": 0, "error": str(exc)}


def db_engine():
    from app.db.session import engine

    return engine


def build_filesystem_status() -> dict:
    ensure_storage_dirs()
    paths = {
        "storage": settings.backend_root.parent / "storage",
        "uploads": settings.uploads_path,
        "results": settings.results_path,
        "models": settings.models_path,
        "logs": settings.backend_root / "logs",
    }
    usage_root = settings.backend_root.anchor or str(settings.backend_root)
    usage = shutil.disk_usage(usage_root)
    return {
        "paths": {name: {"path": str(path), "exists": path.exists(), "is_dir": path.is_dir()} for name, path in paths.items()},
        "disk": {"total": usage.total, "used": usage.used, "free": usage.free},
    }


def clear_detection_history(db: Session) -> int:
    count = db.query(DetectionRecord).count()
    db.query(DetectionResult).delete(synchronize_session=False)
    db.query(Task).filter(Task.record_id.is_not(None)).delete(synchronize_session=False)
    db.query(DetectionRecord).delete(synchronize_session=False)
    db.commit()
    clear_directory(settings.uploads_path)
    clear_directory(settings.results_path, keep_names={"training_analysis"})
    ensure_storage_dirs()
    return count


def clear_logs(db: Session) -> int:
    count = db.query(SystemLog).count()
    db.query(SystemLog).delete(synchronize_session=False)
    db.commit()
    clear_directory(settings.backend_root / "logs")
    return count


def clear_models(db: Session) -> int:
    active_models = db.query(ModelInfo).filter(ModelInfo.is_active.is_(True), ModelInfo.is_deleted.is_(False)).all()
    active_ids = {item.id for item in active_models}
    active_paths = {Path(item.path).resolve() for item in active_models if item.path}
    rows = db.query(ModelInfo).filter(ModelInfo.is_deleted.is_(False), ModelInfo.id.notin_(active_ids) if active_ids else True).all()
    deleted = 0
    for row in rows:
        delete_model_file_if_safe(row.path, active_paths)
        db.delete(row)
        deleted += 1
    db.commit()
    settings.models_path.mkdir(parents=True, exist_ok=True)
    return deleted


def restore_initial_state(db: Session) -> dict:
    active_before = db.query(ModelInfo).filter(ModelInfo.is_active.is_(True), ModelInfo.is_deleted.is_(False)).first()
    active_id = active_before.id if active_before else None
    init_db(db)
    if active_id is not None:
        active_after = db.get(ModelInfo, active_id)
        if active_after is not None and not active_after.is_deleted:
            db.query(ModelInfo).update({ModelInfo.is_active: False})
            active_after.is_active = True
            db.commit()
    active = db.query(ModelInfo).filter(ModelInfo.is_active.is_(True), ModelInfo.is_deleted.is_(False)).first()
    if active is None:
        default_model = db.query(ModelInfo).filter(ModelInfo.is_deleted.is_(False)).order_by(ModelInfo.id.asc()).first()
        if default_model is not None:
            default_model.is_active = True
            db.commit()
    return {"restored": True}


def delete_model_file_if_safe(value: str, protected_paths: set[Path]) -> None:
    if not value:
        return
    path = Path(value).resolve()
    model_root = settings.models_path.resolve()
    if model_root not in path.parents and path != model_root:
        return
    if path in protected_paths:
        return
    if path.exists() and path.is_file():
        path.unlink(missing_ok=True)


def clear_directory(path: Path, keep_names: set[str] | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    keep_names = keep_names or set()
    for child in path.iterdir():
        if child.name in keep_names:
            continue
        if child.is_dir():
            clear_directory(child)
        else:
            child.unlink(missing_ok=True)
