from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.response import success
from app.db.session import get_db
from app.models.user import User
from app.schemas.training_analysis import TrainingAnalysisReportRequest
from app.services.log_service import create_log
from app.services.training_analysis_service import (
    ai_training_report,
    clear_training_analyses,
    delete_training_analysis,
    export_training_report,
    list_training_files,
    summarize_results_csv,
    upload_results_csv,
)

router = APIRouter(prefix="/training-analysis", tags=["training-analysis"])


@router.post("/upload")
def upload_training_results(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("history:read")),
):
    return success(upload_results_csv(db, file, current_user.id))


@router.get("/files")
def get_training_files(db: Session = Depends(get_db), _: User = Depends(require_permission("history:read"))):
    return success({"items": list_training_files(db)})


@router.get("/summary")
def get_training_summary(name: str, _: User = Depends(require_permission("history:read"))):
    return success(summarize_results_csv(name))


@router.get("/export")
def export_training_analysis(name: str = Query(...), _: User = Depends(require_permission("history:read"))):
    buffer, filename = export_training_report(name)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(buffer, media_type="text/plain; charset=utf-8", headers=headers)


@router.delete("/clear")
def clear_training_analysis_records(db: Session = Depends(get_db), current_user: User = Depends(require_permission("history:manage"))):
    count = clear_training_analyses(db)
    create_log(db, "system", f"训练分析已清空，共 {count} 条记录", module="training_analysis", user_id=current_user.id)
    return success({"deleted": count})


@router.delete("/{name}")
def delete_training_analysis_record(name: str, db: Session = Depends(get_db), current_user: User = Depends(require_permission("history:manage"))):
    deleted = delete_training_analysis(db, name)
    create_log(db, "system", f"训练分析已删除：{name}", module="training_analysis", user_id=current_user.id)
    return success({"deleted": deleted})


@router.post("/ai-report")
def get_training_ai_report(
    payload: TrainingAnalysisReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assistant:use")),
):
    report = ai_training_report(payload.summary)
    create_log(db, "assistant", "训练分析 AI 报告已生成", module="assistant", user_id=current_user.id)
    return success(report)
