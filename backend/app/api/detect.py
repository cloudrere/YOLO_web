from types import SimpleNamespace

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_user_permissions, require_permission
from app.core.inference_service import (
    create_video_task,
    detect_batch,
    detect_image,
    get_task,
    resolve_record_artifact,
    stream_realtime_source,
    stream_video_frames,
)
from app.core.response import AppException, success
from app.db.session import get_db
from app.models.user import User
from app.schemas.task import TaskOut
from app.services.model_service import ensure_active_model_loaded

router = APIRouter(prefix="/detect", tags=["detect"])


def authorize_query_token(token: str | None, db: Session) -> User:
    if not token:
        raise AppException(40100, "Authorization token is required", 401)
    credentials = SimpleNamespace(credentials=token)
    user = get_current_user(credentials=credentials, db=db)
    permissions = get_user_permissions(user)
    if "detect:run" not in permissions and not user.is_superuser:
        raise AppException(40300, "Permission denied", 403)
    return user


@router.post("/image")
def detect_image_api(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("detect:run")),
):
    return success(detect_image(db, file, current_user))


@router.post("/batch")
def detect_batch_api(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("detect:run")),
):
    return success(detect_batch(db, files, current_user))


@router.post("/video")
def detect_video_api(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("detect:run")),
):
    return success(create_video_task(db, file, current_user))


@router.get("/tasks/{task_id}")
def get_task_api(task_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("detect:run"))):
    task = get_task(db, task_id)
    return success(TaskOut.model_validate(task).model_dump())


@router.get("/artifacts/{record_id}")
def get_artifact_api(
    record_id: int,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    authorize_query_token(token, db)
    path = resolve_record_artifact(db, record_id)
    return FileResponse(path)


@router.get("/video/stream/{task_id}")
def stream_video_api(
    task_id: int,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    authorize_query_token(token, db)
    return StreamingResponse(stream_video_frames(task_id), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/realtime/stream")
def stream_realtime_api(
    source: str = Query(default="0"),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    authorize_query_token(token, db)
    ensure_active_model_loaded(db)
    return StreamingResponse(stream_realtime_source(source), media_type="multipart/x-mixed-replace; boundary=frame")
