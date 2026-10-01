import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from enterpriseguard.monitors import alerts_monitor


def test_utc_timestamp():
    ts = alerts_monitor.utc_timestamp()
    assert isinstance(ts, str)
    assert len(ts) > 0


def test_append_activity_success_and_exception(tmp_path, monkeypatch):
    activity_file = tmp_path / "activity_log.json"
    alerts_monitor.append_activity("Test event", activity_file)

    with patch("enterpriseguard.monitors.alerts_monitor.audit_append_activity", side_effect=Exception("Audit fail")):
        alerts_monitor.append_activity("Test event fail", activity_file)


def test_log_error_success_and_exception(tmp_path, monkeypatch):
    err_file = tmp_path / "errors.log"
    monkeypatch.setattr(alerts_monitor, "ERROR_LOG_PATH", err_file)

    alerts_monitor.log_error("Sample error message")
    assert err_file.exists()
    assert "Sample error message" in err_file.read_text(encoding="utf-8")

    with patch("pathlib.Path.open", side_effect=OSError("Write error")):
        alerts_monitor.log_error("Unwritable error")


def test_parse_timestamp():
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    parsed = alerts_monitor.parse_timestamp(now_str)
    assert parsed is not None

    assert alerts_monitor.parse_timestamp("invalid-date-format") is None


def test_read_activity_log(tmp_path, monkeypatch):
    act_file = tmp_path / "activity_log.json"
    monkeypatch.setattr(alerts_monitor, "ACTIVITY_LOG_PATH", act_file)

    assert alerts_monitor.read_activity_log() == []

    data = [{"event": "login"}, {"event": "logout"}]
    act_file.write_text(json.dumps(data), encoding="utf-8")
    assert alerts_monitor.read_activity_log() == data

    act_file.write_text(json.dumps({"key": "val"}), encoding="utf-8")
    assert alerts_monitor.read_activity_log() == []

    act_file.write_text("invalid json", encoding="utf-8")
    assert alerts_monitor.read_activity_log() == []


def test_read_error_log(tmp_path, monkeypatch):
    err_file = tmp_path / "errors.log"
    monkeypatch.setattr(alerts_monitor, "ERROR_LOG_PATH", err_file)

    assert alerts_monitor.read_error_log() == []

    err_file.write_text("[2026-09-23 10:00:00 UTC] Err 1\n\n[2026-09-23 11:00:00 UTC] Err 2\n", encoding="utf-8")
    logs = alerts_monitor.read_error_log()
    assert len(logs) == 2


def test_summarize_activity():
    summary = alerts_monitor.summarize_activity([])
    assert summary["total_events"] == 0
    assert summary["latest_event"] == "No activity recorded"

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entries = [
        {"event": "login", "timestamp": now_str},
        {"event": "login", "timestamp": now_str},
        {"event": "export", "timestamp": "invalid_ts"},
    ]
    summary = alerts_monitor.summarize_activity(entries)
    assert summary["total_events"] == 3
    assert summary["recent_24h"] == 2
    assert summary["events_last_7d"] == 2
    assert summary["latest_event"] == "export"
    assert summary["event_types"]["login"] == 2


def test_summarize_errors():
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"[{now_str}] Error line 1",
        "Line without timestamp match",
        "[invalid-time] Error line 2",
    ]
    summary = alerts_monitor.summarize_errors(lines)
    assert summary["total_errors"] == 3
    assert summary["recent_24h"] == 1
    assert len(summary["recent_occurrences"]) == 1


def test_determine_severity():
    assert alerts_monitor.determine_severity({"total_errors": 10, "recent_24h": 0}, {"recent_24h": 5}) == "ALERT"
    assert alerts_monitor.determine_severity({"total_errors": 0, "recent_24h": 5}, {"recent_24h": 5}) == "ALERT"

    assert alerts_monitor.determine_severity({"total_errors": 3, "recent_24h": 0}, {"recent_24h": 5}) == "NOTICE"
    assert alerts_monitor.determine_severity({"total_errors": 0, "recent_24h": 2}, {"recent_24h": 5}) == "NOTICE"
    assert alerts_monitor.determine_severity({"total_errors": 0, "recent_24h": 0}, {"recent_24h": 0}) == "NOTICE"

    assert alerts_monitor.determine_severity({"total_errors": 1, "recent_24h": 0}, {"recent_24h": 5}) == "HEALTHY"


def test_build_and_print_report(capsys):
    report = alerts_monitor.build_report()
    assert "severity" in report
    assert "activity_summary" in report

    alerts_monitor.print_report({
        "severity": "ALERT",
        "generated_at": "2026-09-23 12:00:00 UTC",
        "activity_summary": {
            "total_events": 5,
            "recent_24h": 2,
            "events_last_7d": 4,
            "latest_event": "check",
            "event_types": {"check": 5},
        },
        "error_summary": {
            "total_errors": 12,
            "recent_24h": 6,
            "recent_occurrences": ["[2026-09-23 11:00:00 UTC] Critical failure"],
        },
    })
    captured = capsys.readouterr()
    assert "EnterpriseGuard Alert Monitor" in captured.out
    assert "Top event types:" in captured.out


def test_main_executions(tmp_path, monkeypatch):
    monkeypatch.setattr(alerts_monitor, "ensure_tools_dir", lambda: None)
    monkeypatch.setattr(alerts_monitor, "append_activity", lambda *args: None)
    monkeypatch.setattr(alerts_monitor, "log_error", lambda *args: None)

    with patch("enterpriseguard.monitors.alerts_monitor.determine_severity", return_value="ALERT"):
        assert alerts_monitor.main() == 1

    with patch("enterpriseguard.monitors.alerts_monitor.determine_severity", return_value="NOTICE"):
        assert alerts_monitor.main() == 0

    with patch("enterpriseguard.monitors.alerts_monitor.determine_severity", return_value="HEALTHY"):
        assert alerts_monitor.main() == 0
