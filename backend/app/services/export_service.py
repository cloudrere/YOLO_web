from io import BytesIO

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.services.history_service import list_records


def export_history_xlsx(
    db: Session,
    source_type: str | None = None,
    class_name: str | None = None,
    class_name_zh: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
) -> BytesIO:
    rows, _ = list_records(db, 1, 10000, source_type, class_name, user_id, class_name_zh, username)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "检测历史"
    sheet.append(["ID", "用户", "来源", "文件名", "状态", "目标数", "类别", "耗时(ms)", "创建时间"])
    for row in rows:
        sheet.append(
            [
                row.get("id"),
                row.get("username") or row.get("user_id") or "",
                row.get("source_type"),
                row.get("file_name"),
                row.get("status"),
                row.get("result_count"),
                ", ".join(item.get("class_zh") or item.get("class") or "" for item in row.get("classes", [])),
                row.get("duration_ms"),
                str(row.get("created_at") or ""),
            ]
        )
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer
