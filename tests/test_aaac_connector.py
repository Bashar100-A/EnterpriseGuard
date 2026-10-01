import json
import os
import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from enterpriseguard.security import aaac_connector


def test_load_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Comment line\n"
        "LANGFUSE_PUBLIC_KEY=pk-123\n"
        'LANGFUSE_SECRET_KEY="sk-456"\n'
        "LANGFUSE_BASE_URL='https://custom.langfuse.com'\n"
        "INVALID_LINE_WITHOUT_EQUALS\n"
        "  SPACED_KEY = spaced_val \n",
        encoding="utf-8",
    )
    res = aaac_connector.load_env(env_file)
    assert res["LANGFUSE_PUBLIC_KEY"] == "pk-123"
    assert res["LANGFUSE_SECRET_KEY"] == "sk-456"
    assert res["LANGFUSE_BASE_URL"] == "https://custom.langfuse.com"
    assert res["SPACED_KEY"] == "spaced_val"
    assert "INVALID_LINE_WITHOUT_EQUALS" not in res


def test_load_env_nonexistent(tmp_path):
    nonexistent = tmp_path / "nonexistent.env"
    assert aaac_connector.load_env(nonexistent) == {}


def test_get_headers(monkeypatch):
    monkeypatch.setattr(aaac_connector, "PUBLIC_KEY", "test_pk")
    monkeypatch.setattr(aaac_connector, "SECRET_KEY", "test_sk")
    headers = aaac_connector.get_headers()
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Basic ")


def test_fetch_observations(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": [{"id": "obs-1", "traceId": "tr-1"}]}
    mock_resp.raise_for_status.return_value = None

    monkeypatch.setattr("requests.get", MagicMock(return_value=mock_resp))
    monkeypatch.setattr(aaac_connector, "BASE_URL", "https://test.langfuse.com")

    res = aaac_connector.fetch_observations(limit=5)
    assert len(res) == 1
    assert res[0]["id"] == "obs-1"


def test_fetch_trace(monkeypatch):
    mock_resp_ok = MagicMock()
    mock_resp_ok.status_code = 200
    mock_resp_ok.json.return_value = {"id": "tr-1", "input": "hello"}

    mock_resp_404 = MagicMock()
    mock_resp_404.status_code = 404

    mock_get = MagicMock(side_effect=[mock_resp_ok, mock_resp_404])
    monkeypatch.setattr("requests.get", mock_get)

    assert aaac_connector.fetch_trace("tr-1") == {"id": "tr-1", "input": "hello"}
    assert aaac_connector.fetch_trace("tr-2") == {}


def test_sanitize():
    assert aaac_connector.sanitize(123) == ""
    raw = "my api_key is secret and password is token"
    sanitized = aaac_connector.sanitize(raw)
    assert "api_key" not in sanitized
    assert "secret" not in sanitized
    assert "password" not in sanitized
    assert "token" not in sanitized
    assert sanitized.count("***") == 4

    long_str = "a" * 250
    assert len(aaac_connector.sanitize(long_str)) == 200


def test_normalize_observation():
    obs = {
        "startTime": "2026-09-23T10:00:00Z",
        "traceId": "tr-100",
        "id": "run-1",
        "name": "cmd_test",
        "latency": 150,
    }
    trace_data = {
        "metadata": {"agent_id": "agent-007"},
        "input": "input data",
        "output": "output data",
    }

    res = aaac_connector.normalize_observation(obs, trace_data)
    assert res["timestamp"] == "2026-09-23T10:00:00Z"
    assert res["agent_id"] == "agent-007"
    assert res["trace_id"] == "tr-100"
    assert res["run_id"] == "run-1"
    assert res["command"] == "cmd_test"
    assert res["actor_type"] == "agent"
    assert res["input_summary"] == "input data"
    assert res["output_summary"] == "output data"
    assert res["latency_ms"] == 150

    res_none = aaac_connector.normalize_observation(obs, None)
    assert res_none["agent_id"] == "unknown"


def test_load_existing_trace_ids(tmp_path, monkeypatch):
    ring_file = tmp_path / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_connector, "RING_STORAGE_PATH", ring_file)

    assert aaac_connector.load_existing_trace_ids() == set()

    content = (
        '{"trace_id": "tr-1"}\n'
        "\n"
        "invalid json\n"
        '{"other": "data"}\n'
        '{"trace_id": "tr-2"}\n'
    )
    ring_file.write_text(content, encoding="utf-8")
    assert aaac_connector.load_existing_trace_ids() == {"tr-1", "tr-2"}


def test_load_existing_trace_ids_oserror(tmp_path, monkeypatch):
    ring_file = tmp_path / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_connector, "RING_STORAGE_PATH", ring_file)

    with patch("builtins.open", side_effect=OSError("Read error")):
        assert aaac_connector.load_existing_trace_ids() == set()


def test_save_event_to_ring_storage(tmp_path, monkeypatch):
    ring_file = tmp_path / "sub" / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_connector, "RING_STORAGE_PATH", ring_file)

    event = {"trace_id": "tr-1", "data": "test"}
    with patch("os.fsync"):
        aaac_connector.save_event_to_ring_storage(event)

    assert ring_file.exists()
    lines = ring_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == event


def test_main_block_with_events(monkeypatch, capsys):
    real_ring_path = Path("tools/ring_storage.jsonl")
    real_ring_path.parent.mkdir(parents=True, exist_ok=True)

    original_content = real_ring_path.read_text(encoding="utf-8") if real_ring_path.exists() else None

    try:
        real_ring_path.write_text(json.dumps({"trace_id": "tr-1"}) + "\n", encoding="utf-8")

        obs_payload = {"data": [{"traceId": "tr-1", "id": "obs-1"}, {"traceId": "tr-2", "id": "obs-2"}]}
        trace_payload = {"id": "tr-2", "input": "test"}

        mock_resp_obs = MagicMock()
        mock_resp_obs.json.return_value = obs_payload
        mock_resp_obs.raise_for_status.return_value = None

        mock_resp_trace = MagicMock()
        mock_resp_trace.status_code = 200
        mock_resp_trace.json.return_value = trace_payload

        def mock_get(url, **kwargs):
            if "observations" in url:
                return mock_resp_obs
            return mock_resp_trace

        monkeypatch.setattr("requests.get", mock_get)

        with patch("os.fsync"):
            runpy.run_path(aaac_connector.__file__, run_name="__main__")

        captured = capsys.readouterr()
        assert "تم جلب 2 ملاحظة" in captured.out
        assert "تم حفظ 1 حدث" in captured.out
    finally:
        if original_content is not None:
            real_ring_path.write_text(original_content, encoding="utf-8")
        elif real_ring_path.exists():
            real_ring_path.unlink()


def test_main_block_no_events(tmp_path, monkeypatch, capsys):
    ring_file = tmp_path / "ring_storage.jsonl"
    monkeypatch.setattr(aaac_connector, "RING_STORAGE_PATH", ring_file)

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": []}
    mock_resp.raise_for_status.return_value = None
    monkeypatch.setattr("requests.get", MagicMock(return_value=mock_resp))

    runpy.run_path(aaac_connector.__file__, run_name="__main__")

    captured = capsys.readouterr()
    assert "لا توجد ملاحظات حديثة." in captured.out
