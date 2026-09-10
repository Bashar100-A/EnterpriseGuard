import sys
from datetime import datetime, timedelta, timezone

sys.dont_write_bytecode = True


def parse_utc_timestamp(s: str) -> datetime:
    """Parse a timestamp string into a timezone-aware UTC datetime."""
    if not isinstance(s, str):
        raise TypeError(f"Expected a timestamp string, got {type(s).__name__}")

    value = s.strip()
    if not value:
        raise ValueError("Timestamp string is empty")

    if value.endswith("Z"):
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%SZ"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    if value.endswith("+00:00"):
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z"):
            try:
                return datetime.strptime(value, fmt).astimezone(timezone.utc)
            except ValueError:
                continue

    if value.endswith(" UTC") or value.endswith(" GMT"):
        base = value.rsplit(" ", 1)[0]
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(base, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    try:
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Unsupported timestamp format: {s}") from exc


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def safe_subtract(a: datetime, b: datetime) -> timedelta:
    return ensure_aware(a) - ensure_aware(b)
