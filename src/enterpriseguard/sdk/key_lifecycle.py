"""UTC-aware key lifecycle validation for ADIE provenance records."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Protocol


class KeyLifecycleRecord(Protocol):
    valid_from: datetime | str
    effective_end: datetime | str
    revocation_time: datetime | str | None


_UTC_ISO8601 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|\+00:00)$"
)


def _field(key: KeyLifecycleRecord | Mapping[str, object], name: str) -> object:
    if isinstance(key, Mapping):
        try:
            return key[name]
        except KeyError as exc:
            raise ValueError(f"Key lifecycle record is missing {name!r}") from exc

    try:
        return getattr(key, name)
    except AttributeError as exc:
        raise ValueError(f"Key lifecycle record is missing {name!r}") from exc


def _utc_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, str):
        if not _UTC_ISO8601.fullmatch(value):
            raise ValueError(
                f"{field_name} must be a UTC ISO-8601 timestamp ending in Z or +00:00"
            )
        value = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    if not isinstance(value, datetime):
        raise ValueError(
            f"{field_name} must be a timezone-aware datetime or UTC ISO-8601 string"
        )

    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if offset != timedelta(0):
        raise ValueError(f"{field_name} must use UTC")
    return value.astimezone(timezone.utc)


def _is_valid_at(key: KeyLifecycleRecord | Mapping[str, object], timestamp: object) -> bool:
    valid_from = _utc_datetime(_field(key, "valid_from"), "valid_from")
    effective_end = _utc_datetime(_field(key, "effective_end"), "effective_end")
    checked_at = _utc_datetime(timestamp, "timestamp")
    revocation_value = (
        _field(key, "revocation_time")
        if isinstance(key, Mapping) and "revocation_time" in key
        else getattr(key, "revocation_time", None)
    )

    if effective_end < valid_from:
        raise ValueError("effective_end must not precede valid_from")
    if revocation_value is not None:
        revocation_time = _utc_datetime(revocation_value, "revocation_time")
        return valid_from <= checked_at < effective_end and checked_at < revocation_time
    return valid_from <= checked_at < effective_end


def is_historically_valid_for(
    key: KeyLifecycleRecord | Mapping[str, object],
    signing_timestamp: datetime | str,
) -> bool:
    """Return whether the key was active and unrevoked at signing time."""
    return _is_valid_at(key, signing_timestamp)


def is_model_trusted_for_inference(
    key: KeyLifecycleRecord | Mapping[str, object],
    current_timestamp: datetime | str,
) -> bool:
    """Return whether the key is active and unrevoked at inference time."""
    return _is_valid_at(key, current_timestamp)