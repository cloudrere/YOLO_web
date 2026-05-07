import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def safe_filename(filename: str) -> str:
    name = Path(filename or "upload.bin").name
    stem = Path(name).stem.replace(" ", "_") or "file"
    suffix = Path(name).suffix.lower()
    return f"{stem}_{uuid4().hex[:12]}{suffix}"


def save_upload_file(file: UploadFile, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe_filename(file.filename or "upload.bin")
    with target.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return target


def remove_file(path: str) -> None:
    target = Path(path)
    if target.exists() and target.is_file():
        target.unlink()
