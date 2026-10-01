"""Boundary tests for ADIE key lifecycle time semantics."""

from datetime import datetime, timezone

import pytest

from enterpriseguard.sdk.key_lifecycle import (
    is_historically_valid_for,
    is_model_trusted_for_inference,
)


def make_key(**overrides):
    record = {
        "valid_from": "2026-09-29T12:00:00.000Z",
        "effective_end": "2026-09-29T13:00:00.000Z",
        "revocation_time": None,
    }
    record.update(overrides)
    return record


def test_valid_from_inclusive_at_exact_millisecond():
    key = make_key()

    assert is_historically_valid_for(key, "2026-09-29T12:00:00.000Z")
    assert is_model_trusted_for_inference(key, "2026-09-29T12:00:00.000Z")


def test_effective_end_exclusive_at_exact_millisecond():
    key = make_key()

    assert not is_historically_valid_for(key, "2026-09-29T13:00:00.000Z")
    assert not is_model_trusted_for_inference(key, "2026-09-29T13:00:00.000Z")


def test_revocation_is_effective_at_its_exact_timestamp():
    key = make_key(revocation_time="2026-09-29T12:30:00.000Z")

    assert is_historically_valid_for(key, "2026-09-29T12:29:59.999Z")
    assert not is_historically_valid_for(key, "2026-09-29T12:30:00.000Z")
    assert not is_model_trusted_for_inference(key, "2026-09-29T12:30:00.000Z")


def test_historical_validity_survives_later_revocation():
    key = make_key(revocation_time="2026-09-29T12:30:00.000Z")

    assert is_historically_valid_for(key, "2026-09-29T12:15:00.000Z")
    assert not is_model_trusted_for_inference(key, "2026-09-29T12:45:00.000Z")


def test_equivalent_utc_datetime_and_iso_timestamps_are_timezone_neutral():
    key = {
        "valid_from": datetime(2026, 9, 29, 12, tzinfo=timezone.utc),
        "effective_end": "2026-09-29T13:00:00+00:00",
    }

    assert is_historically_valid_for(
        key, datetime.fromisoformat("2026-09-29T12:00:00+00:00")
    )
    assert is_model_trusted_for_inference(key, "2026-09-29T12:00:00Z")


@pytest.mark.parametrize(
    "timestamp",
    [datetime(2026, 9, 29, 12), "2026-09-29T12:00:00"],
)
def test_timezone_naive_timestamps_are_rejected(timestamp):
    with pytest.raises(ValueError, match="timezone-aware|UTC ISO-8601"):
        is_historically_valid_for(make_key(), timestamp)


def test_non_utc_timestamp_offsets_are_rejected():
    with pytest.raises(ValueError, match="UTC ISO-8601"):
        is_model_trusted_for_inference(make_key(), "2026-09-29T14:00:00+02:00")