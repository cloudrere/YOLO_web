from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.training_analysis import TrainingAnalysisReportRequest
from app.services.log_service import create_log
from app.services.training_analysis_service import ai_training_report, list_training_files, summarize_results_csv, upload_results_csv

router = APIRouter(prefix="/training-analysis", tags=["training-analysis"])


@router.post("/upload")
def upload_training_results(
    file: UploadFile = File(...),
    _: User = Depends(require_permission("history:read")),
):
    return success(upload_results_csv(file))


@router.get("/files")
def get_training_files(_: User = Depends(require_permission("history:read"))):
    return success({"items": list_training_files()})


@router.get("/summary")
def get_training_summary(name: str, _: User = Depends(require_permission("history:read"))):
    return success(summarize_results_csv(name))


@router.post("/ai-report")
def get_training_ai_report(
    payload: TrainingAnalysisReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assistant:use")),
):
    report = ai_training_report(payload.summary)
    create_log(db, "assistant", "训练分析 AI 报告已生成", module="assistant", user_id=current_user.id)
    return success(report)
