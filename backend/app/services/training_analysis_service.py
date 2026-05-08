import csv
from io import BytesIO
from pathlib import Path
from shutil import copyfileobj

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import AppException
from app.models.training_analysis_record import TrainingAnalysisRecord
from app.services.assistant_service import request_chat_completion
from app.utils.time import format_datetime_second, utc_now

REQUIRED_COLUMNS = [
    "epoch",
    "train/box_loss",
    "train/cls_loss",
    "train/dfl_loss",
    "metrics/precision(B)",
    "metrics/recall(B)",
    "metrics/mAP50(B)",
    "metrics/mAP50-95(B)",
    "val/box_loss",
    "val/cls_loss",
    "val/dfl_loss",
    "lr/pg0",
    "lr/pg1",
    "lr/pg2",
]

COLUMN_ALIASES = {
    "train_box_loss": "train/box_loss",
    "train_cls_loss": "train/cls_loss",
    "train_dfl_loss": "train/dfl_loss",
    "precision": "metrics/precision(B)",
    "recall": "metrics/recall(B)",
    "map50": "metrics/mAP50(B)",
    "map5095": "metrics/mAP50-95(B)",
    "val_box_loss": "val/box_loss",
    "val_cls_loss": "val/cls_loss",
    "val_dfl_loss": "val/dfl_loss",
    "lr_pg0": "lr/pg0",
    "lr_pg1": "lr/pg1",
    "lr_pg2": "lr/pg2",
}


def training_analysis_dir() -> Path:
    path = settings.results_path / "training_analysis"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_csv_name(name: str) -> str:
    filename = Path(name or "results.csv").name
    if not filename.lower().endswith(".csv"):
        raise AppException(40070, "Only results.csv files are supported")
    return filename


def resolve_training_csv(name: str) -> Path:
    filename = safe_csv_name(name)
    path = (training_analysis_dir() / filename).resolve()
    root = training_analysis_dir().resolve()
    if root not in path.parents and path != root:
        raise AppException(40370, "Training analysis file is outside storage", 403)
    if not path.exists() or not path.is_file():
        raise AppException(40470, "Training results.csv not found", 404)
    return path


def upload_results_csv(db: Session, file: UploadFile, user_id: int | None = None) -> dict:
    filename = safe_csv_name(file.filename or "results.csv")
    target = training_analysis_dir() / filename
    with target.open("wb") as buffer:
        copyfileobj(file.file, buffer)
    summary = summarize_results_csv(filename)
    record = upsert_training_record(db, target, summary, user_id)
    return {"file": record_info(record), "summary": summary}


def upsert_training_record(db: Session, path: Path, summary: dict, user_id: int | None = None) -> TrainingAnalysisRecord:
    item = db.query(TrainingAnalysisRecord).filter(TrainingAnalysisRecord.name == path.name).first()
    if item is None:
        item = TrainingAnalysisRecord(name=path.name, path=str(path), user_id=user_id)
        db.add(item)
    item.path = str(path)
    item.rows = len(summary["epochs"])
    item.best_epoch = summary.get("best_epoch")
    item.best_map50 = summary.get("best_map50")
    item.best_map5095 = summary.get("best_map5095")
    item.file_size = path.stat().st_size if path.exists() else 0
    item.updated_at = utc_now()
    db.commit()
    db.refresh(item)
    return item


def sync_existing_training_files(db: Session) -> None:
    for path in training_analysis_dir().glob("*.csv"):
        exists = db.query(TrainingAnalysisRecord).filter(TrainingAnalysisRecord.name == path.name).first()
        if exists is not None:
            continue
        try:
            summary = summarize_results_csv(path.name)
            upsert_training_record(db, path, summary)
        except AppException:
            item = TrainingAnalysisRecord(name=path.name, path=str(path), rows=0, file_size=path.stat().st_size)
            db.add(item)
            db.commit()


def list_training_files(db: Session) -> list[dict]:
    sync_existing_training_files(db)
    rows = db.query(TrainingAnalysisRecord).order_by(TrainingAnalysisRecord.updated_at.desc()).all()
    return [record_info(row) for row in rows]


def record_info(record: TrainingAnalysisRecord) -> dict:
    return {
        "id": record.id,
        "name": record.name,
        "path": record.path,
        "rows": record.rows,
        "best_epoch": record.best_epoch,
        "best_map50": record.best_map50,
        "best_map5095": record.best_map5095,
        "file_size": record.file_size,
        "created_at": format_datetime_second(record.created_at),
    }


def summarize_results_csv(name: str) -> dict:
    path = resolve_training_csv(name)
    rows = read_results_rows(path)
    data = {key: values(rows, column) for key, column in COLUMN_ALIASES.items()}
    epochs = [int(value) for value in values(rows, "epoch")]
    map50 = data["map50"]
    map5095 = data["map5095"]
    best_index = max(range(len(map50)), key=lambda index: map50[index]) if map50 else None
    best_epoch = epochs[best_index] if best_index is not None else None
    final_metrics = {key: series[-1] for key, series in data.items() if series}
    radar = [
        {"name": "Precision", "value": final_metrics.get("precision", 0.0)},
        {"name": "Recall", "value": final_metrics.get("recall", 0.0)},
        {"name": "mAP50", "value": final_metrics.get("map50", 0.0)},
        {"name": "mAP50-95", "value": final_metrics.get("map5095", 0.0)},
    ]
    bar_metrics = [
        {"name": "Train Box Loss", "value": final_metrics.get("train_box_loss", 0.0)},
        {"name": "Train Cls Loss", "value": final_metrics.get("train_cls_loss", 0.0)},
        {"name": "Train DFL Loss", "value": final_metrics.get("train_dfl_loss", 0.0)},
        {"name": "Val Box Loss", "value": final_metrics.get("val_box_loss", 0.0)},
        {"name": "Val Cls Loss", "value": final_metrics.get("val_cls_loss", 0.0)},
        {"name": "Val DFL Loss", "value": final_metrics.get("val_dfl_loss", 0.0)},
    ]
    warnings = training_warnings(data)
    return {
        "name": path.name,
        "path": str(path),
        "epochs": epochs,
        "best_epoch": best_epoch,
        "best_map50": map50[best_index] if best_index is not None else None,
        "best_map5095": map5095[best_index] if best_index is not None and map5095 else None,
        "final_metrics": final_metrics,
        "radar": radar,
        "bar_metrics": bar_metrics,
        "warnings": warnings,
        **data,
    }


def read_results_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise AppException(40071, "CSV header is missing")
        normalized_names = {name.strip(): name for name in reader.fieldnames}
        missing = [column for column in REQUIRED_COLUMNS if column not in normalized_names]
        if missing:
            raise AppException(40072, f"CSV missing required columns: {', '.join(missing)}")
        rows = []
        for row in reader:
            rows.append({key.strip(): value for key, value in row.items() if key is not None})
    if not rows:
        raise AppException(40073, "CSV has no training rows")
    return rows


def values(rows: list[dict[str, str]], column: str) -> list[float]:
    output = []
    for row in rows:
        raw = str(row.get(column, "")).strip()
        try:
            output.append(round(float(raw), 6))
        except ValueError as exc:
            raise AppException(40074, f"Invalid numeric value in column {column}: {raw}") from exc
    return output


def training_warnings(data: dict[str, list[float]]) -> list[str]:
    warnings = []
    precision = data.get("precision") or []
    recall = data.get("recall") or []
    map50 = data.get("map50") or []
    val_box = data.get("val_box_loss") or []
    train_box = data.get("train_box_loss") or []
    if precision and recall and abs(precision[-1] - recall[-1]) > 0.2:
        warnings.append("Precision 与 Recall 差距较大，建议检查置信度阈值、类别不均衡或漏标问题。")
    if len(map50) >= 6 and max(map50[-5:]) <= max(map50[:-5]):
        warnings.append("最近 5 个 epoch 的 mAP50 没有继续提升，训练可能进入平台期。")
    if train_box and val_box and val_box[-1] > train_box[-1] * 1.8:
        warnings.append("验证集 box loss 明显高于训练集，可能存在过拟合或验证集分布差异。")
    return warnings


def export_training_report(name: str) -> tuple[BytesIO, str]:
    summary = summarize_results_csv(name)
    final_metrics = summary.get("final_metrics", {})
    lines = [
        "YOLO 训练分析报告",
        f"文件：{summary['name']}",
        f"总 Epoch：{len(summary['epochs'])}",
        f"最佳 Epoch：{summary.get('best_epoch') or '-'}",
        f"最佳 mAP50：{format_percent(summary.get('best_map50'))}",
        f"最佳 mAP50-95：{format_percent(summary.get('best_map5095'))}",
        "",
        "最终指标",
        f"Precision：{format_percent(final_metrics.get('precision'))}",
        f"Recall：{format_percent(final_metrics.get('recall'))}",
        f"mAP50：{format_percent(final_metrics.get('map50'))}",
        f"mAP50-95：{format_percent(final_metrics.get('map5095'))}",
        f"Train Box Loss：{format_number(final_metrics.get('train_box_loss'))}",
        f"Val Box Loss：{format_number(final_metrics.get('val_box_loss'))}",
        "",
        "自动风险提示",
    ]
    warnings = summary.get("warnings") or []
    lines.extend([f"- {item}" for item in warnings] or ["- 当前摘要未发现明显风险提示"])
    buffer = BytesIO("\n".join(lines).encode("utf-8-sig"))
    return buffer, f"{Path(summary['name']).stem}_training_report.txt"


def format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{float(value) * 100:.2f}%"


def format_number(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):.6f}"


def delete_training_analysis(db: Session, name: str) -> int:
    filename = safe_csv_name(name)
    item = db.query(TrainingAnalysisRecord).filter(TrainingAnalysisRecord.name == filename).first()
    path = resolve_optional_training_csv(filename)
    if item is None and path is None:
        raise AppException(40470, "Training analysis record not found", 404)
    if path is not None:
        path.unlink(missing_ok=True)
    if item is not None:
        db.delete(item)
        db.commit()
    return 1


def clear_training_analyses(db: Session) -> int:
    count = db.query(TrainingAnalysisRecord).count()
    for path in training_analysis_dir().glob("*.csv"):
        path.unlink(missing_ok=True)
    db.query(TrainingAnalysisRecord).delete(synchronize_session=False)
    db.commit()
    return count


def resolve_optional_training_csv(name: str) -> Path | None:
    filename = safe_csv_name(name)
    path = (training_analysis_dir() / filename).resolve()
    root = training_analysis_dir().resolve()
    if root not in path.parents and path != root:
        raise AppException(40370, "Training analysis file is outside storage", 403)
    return path if path.exists() and path.is_file() else None


def ai_training_report(summary: dict) -> dict:
    prompt = (
        "请基于以下 YOLO 训练 results.csv 摘要，用中文给出训练质量分析、风险判断和下一步优化建议。"
        "重点关注 Precision、Recall、mAP50、mAP50-95、训练/验证 loss、学习率变化和最佳 epoch。"
        f"\n摘要：{summary}"
    )
    answer = request_chat_completion(prompt)
    return {"answer": answer}
