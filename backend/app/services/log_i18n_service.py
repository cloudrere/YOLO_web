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
        "message": item.message,
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
