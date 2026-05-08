from datetime import datetime, timezone

LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def local_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(LOCAL_TIMEZONE)


def format_datetime_second(value: datetime | None) -> str:
    local_value = local_datetime(value)
    if local_value is None:
        return ""
    return local_value.strftime("%Y-%m-%d %H:%M:%S")
