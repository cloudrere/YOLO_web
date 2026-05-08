from pydantic import BaseModel, ConfigDict, Field


class TrainingAnalysisFileOut(BaseModel):
    id: int | None = None
    name: str
    path: str
    rows: int
    best_epoch: int | None = None
    best_map50: float | None = None
    best_map5095: float | None = None
    file_size: int = 0
    created_at: str = ""


class TrainingAnalysisSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    path: str
    epochs: list[int]
    train_box_loss: list[float]
    train_cls_loss: list[float]
    train_dfl_loss: list[float]
    precision: list[float]
    recall: list[float]
    map50: list[float]
    map5095: list[float]
    val_box_loss: list[float]
    val_cls_loss: list[float]
    val_dfl_loss: list[float]
    lr_pg0: list[float]
    lr_pg1: list[float]
    lr_pg2: list[float]
    radar: list[dict[str, float | str]]
    bar_metrics: list[dict[str, float | str]]
    best_epoch: int | None = None
    best_map50: float | None = None
    best_map5095: float | None = None
    final_metrics: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class TrainingAnalysisReportRequest(BaseModel):
    name: str
    summary: dict


class TrainingAnalysisUploadResponse(BaseModel):
    file: TrainingAnalysisFileOut
    summary: TrainingAnalysisSummaryOut
