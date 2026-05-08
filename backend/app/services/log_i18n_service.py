import re

LEVEL_ZH = {
    "debug": "调试",
    "info": "信息",
    "warning": "警告",
    "error": "错误",
    "critical": "严重",
}

MODULE_ZH = {
    "system": "系统",
    "auth": "认证",
    "detect": "检测",
    "model": "模型",
    "task": "任务",
    "history": "历史",
    "admin": "用户权限",
    "assistant": "AI助手",
}

TYPE_ZH = {
    "auth": "认证事件",
    "detect": "检测事件",
    "model": "模型事件",
    "task": "任务事件",
    "history": "历史事件",
    "admin": "管理事件",
    "assistant": "AI助手事件",
    "system": "系统事件",
}


MESSAGE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^User (.+) logged in$"), "用户 \\1 已登录"),
    (re.compile(r"^User (.+) registered$"), "用户 \\1 已注册"),
    (re.compile(r"^Password reset for user (.+)$"), "用户 \\1 已重置密码"),
    (re.compile(r"^AI assistant question completed$"), "AI 助手问答已完成"),
    (re.compile(r"^Image detection completed without history$"), "单图检测已完成，未写入历史记录"),
    (re.compile(r"^Image detection completed for record (\d+)$"), "单图检测已完成，记录编号 \\1"),
    (re.compile(r"^Batch detection completed for (\d+) files$"), "批量检测已完成，共处理 \\1 个文件"),
    (re.compile(r"^Video detection task (\d+) created$"), "视频检测任务 \\1 已创建"),
    (re.compile(r"^Video detection task (\d+) cancelled$"), "视频检测任务 \\1 已取消"),
    (re.compile(r"^Video detection task (\d+) completed$"), "视频检测任务 \\1 已完成"),
    (re.compile(r"^Switched model device to (.+)$"), "模型推理设备已切换为 \\1"),
    (re.compile(r"^Activated model (.+)$"), "模型 \\1 已激活"),
    (re.compile(r"^Updated model display name (\d+)$"), "模型 \\1 的显示名称已更新"),
    (re.compile(r"^Updated model class mapping (\d+)$"), "模型 \\1 的类别映射已更新"),
    (re.compile(r"^Deleted model (\d+)$"), "模型 \\1 已删除"),
]


def translate_message(message: str) -> str:
    for pattern, replacement in MESSAGE_PATTERNS:
        if pattern.match(message or ""):
            return pattern.sub(replacement, message)
    return message or ""


def zh_value(mapping: dict[str, str], value: str) -> str:
    return mapping.get((value or "").lower(), value or "")


def decorate_log(item) -> dict:
    return {
        "id": item.id,
        "type": item.type,
        "type_zh": zh_value(TYPE_ZH, item.type),
        "level": item.level,
        "level_zh": zh_value(LEVEL_ZH, item.level),
        "module": item.module,
        "module_zh": zh_value(MODULE_ZH, item.module),
        "message": translate_message(item.message),
        "message_raw": item.message,
        "user_id": item.user_id,
        "request_id": item.request_id,
        "created_at": item.created_at,
    }


def normalize_level(value: str | None) -> str | None:
    return _reverse(LEVEL_ZH, value)


def normalize_module(value: str | None) -> str | None:
    return _reverse(MODULE_ZH, value)


def normalize_type(value: str | None) -> str | None:
    return _reverse(TYPE_ZH, value)


def _reverse(mapping: dict[str, str], value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    for key, text in mapping.items():
        if stripped == text:
            return key
    return stripped
