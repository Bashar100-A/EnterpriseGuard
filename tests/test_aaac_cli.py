import json
import os
from unittest.mock import MagicMock, patch

import pytest

from enterpriseguard.security import aaac_cli


def test_load_existing_trace_ids_nonexistent(tmp_path, monkeypatch):
    test_path = tmp_path / "nonexistent.jsonl"
    monkeypatch.setattr(aaac_cli, "RING_STORAGE_PATH", test_path)
    assert aaac_cli.load_existing_trace_ids() == set()


def test_load_existing_trace_ids_valid_and_invalid(tmp_path, monkeypatch):
    test_path = tmp_path / "ring_storage.jsonl"
    content = (
        '{"trace_id": "tr-101"}\n'
        '\n'
        'invalid json line\n'
        '{"other_key": "val"}\n'
        '{"trace_id": "tr-102"}\n'
    )
    test_path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(aaac_cli, "RING_STORAGE_PATH", test_path)

    res = aaac_cli.load_existing_trace_ids()
    assert res == {"tr-101", "tr-102"}


def test_load_existing_trace_ids_oserror(tmp_path, monkeypatch):
    test_path = tmp_path / "unreadable.jsonl"
    monkeypatch.setattr(aaac_cli, "RING_STORAGE_PATH", test_path)
    with patch("builtins.open", side_effect=OSError("Read error")):
        assert aaac_cli.load_existing_trace_ids() == set()


def test_append_event_to_ring_storage(tmp_path, monkeypatch):
    test_path = tmp_path / "sub" / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_cli, "RING_STORAGE_PATH", test_path)

    event = {"trace_id": "tr-1", "action": "login"}
    with patch("os.fsync"):
        aaac_cli.append_event_to_ring_storage(event)

    assert test_path.exists()
    lines = test_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == event


def test_main_fetch_exception(monkeypatch):
    monkeypatch.setattr(aaac_cli, "unified_fetch", MagicMock(side_effect=Exception("Connection error")))
    assert aaac_cli.main() == 1


def test_main_no_events(monkeypatch):
    monkeypatch.setattr(aaac_cli, "unified_fetch", MagicMock(return_value=[]))
    assert aaac_cli.main() == 0


def test_main_success(tmp_path, monkeypatch):
    test_path = tmp_path / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_cli, "RING_STORAGE_PATH", test_path)
    monkeypatch.setenv("AAAC_TRACE_SOURCE", "custom_src")
    monkeypatch.setenv("AAAC_FETCH_LIMIT", "5")

    events = [
        {"trace_id": "tr-1", "data": "old"},
        {"trace_id": "tr-2", "data": "new"},
    ]
    monkeypatch.setattr(aaac_cli, "unified_fetch", MagicMock(return_value=events))
    monkeypatch.setattr(aaac_cli, "load_existing_trace_ids", MagicMock(return_value={"tr-1"}))
    monkeypatch.setattr(aaac_cli, "enrich_event_with_compliance", lambda e: {**e, "enriched": True})

    fake_innocence = MagicMock()
    fake_innocence.generate_ring.return_value = {"ring_hash": "1234567890abcdef123"}
    fake_innocence.verify_chain.return_value = True
    monkeypatch.setitem(os.sys.modules, "tools.innocence_chain", fake_innocence)

    with patch("os.fsync"):
        exit_code = aaac_cli.main()

    assert exit_code == 0
    assert test_path.exists()


def test_main_ring_generation_failure(tmp_path, monkeypatch):
    test_path = tmp_path / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_cli, "RING_STORAGE_PATH", test_path)
    monkeypatch.setattr(aaac_cli, "unified_fetch", MagicMock(return_value=[{"trace_id": "tr-1"}]))
    monkeypatch.setattr(aaac_cli, "load_existing_trace_ids", MagicMock(return_value=set()))
    monkeypatch.setattr(aaac_cli, "enrich_event_with_compliance", lambda e: e)

    fake_innocence = MagicMock()
    fake_innocence.generate_ring.side_effect = Exception("Ring error")
    monkeypatch.setitem(os.sys.modules, "tools.innocence_chain", fake_innocence)

    with patch("os.fsync"):
        assert aaac_cli.main() == 2


def test_main_chain_verification_failure(tmp_path, monkeypatch):
    test_path = tmp_path / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_cli, "RING_STORAGE_PATH", test_path)
    monkeypatch.setattr(aaac_cli, "unified_fetch", MagicMock(return_value=[{"trace_id": "tr-1"}]))
    monkeypatch.setattr(aaac_cli, "load_existing_trace_ids", MagicMock(return_value=set()))
    monkeypatch.setattr(aaac_cli, "enrich_event_with_compliance", lambda e: e)

    fake_innocence = MagicMock()
    fake_innocence.generate_ring.return_value = {"ring_hash": "1234567890"}
    fake_innocence.verify_chain.return_value = False
    monkeypatch.setitem(os.sys.modules, "tools.innocence_chain", fake_innocence)

    with patch("os.fsync"):
        assert aaac_cli.main() == 3
