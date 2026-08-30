#!/usr/bin/env python3
"""EnterpriseGuard project compliance and health checklist.

This script validates the repository's governance files, checks for structural
anomalies, logs verification activity, and exits non-zero when a critical check
fails.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
CONTRACTS_PATH = PROJECT_ROOT / "CONTRACTS.md"
DECISIONS_LOG_PATH = TOOLS_DIR / "DECISIONS_LOG.md"
ACTIVITY_LOG_PATH = TOOLS_DIR / "activity_log.json"
ERROR_LOG_PATH = TOOLS_DIR / "errors.log"
COMMAND_CENTER_PATH = TOOLS_DIR / "command_center.py"
DISCIPLINE_PATH = TOOLS_DIR / "discipline.py"
RAG_SYSTEM_PATH = TOOLS_DIR / "rag_system.py"

PROTECTED_DIRS = ["adie", "intelligence"]
SUSPICIOUS_SUFFIXES = (".bak", ".tmp", ".orig", ".swp")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_tools_dir() -> None:
    TOOLS_DIR.mkdir(exist_ok=True, parents=True)


def append_activity(event: str) -> None:
    ensure_tools_dir()
    try:
        if ACTIVITY_LOG_PATH.exists():
            with ACTIVITY_LOG_PATH.open("r", encoding="utf-8") as handle:
                try:
                    payload = json.load(handle)
                except json.JSONDecodeError:
                    payload = []
        else:
            payload = []

        if not isinstance(payload, list):
            payload = []

        payload.append({"timestamp": utc_timestamp(), "event": event})
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(ACTIVITY_LOG_PATH.parent), delete=False
        ) as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            temp_path = Path(handle.name)
        os.replace(temp_path, ACTIVITY_LOG_PATH)
    except Exception:
        pass


def log_error(message: str) -> None:
    ensure_tools_dir()
    try:
        existing = ERROR_LOG_PATH.read_text(encoding="utf-8") if ERROR_LOG_PATH.exists() else ""
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(ERROR_LOG_PATH.parent), delete=False
        ) as handle:
            handle.write(existing)
            handle.write(f"[{utc_timestamp()}] {message}\n")
            temp_path = Path(handle.name)
        os.replace(temp_path, ERROR_LOG_PATH)
    except Exception:
        pass


def activity_entries_for_scan(payload) -> list[dict]:
    """Return activity entries eligible for checklist analysis.

    RAG execution records are operational telemetry and are intentionally
    excluded from compliance anomaly scans while other activity records remain
    available for inspection.
    """
    if isinstance(payload, dict):
        entries = payload.get("activities", [])
    elif isinstance(payload, list):
        entries = payload
    else:
        entries = []
    return [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("activity_type") != "rag_run"
    ]


def check_file_exists(path: Path, label: str) -> dict:
    exists = path.exists()
    return {
        "name": label,
        "status": "SUCCESS" if exists else "FAILURE",
        "detail": f"{label} {'found' if exists else 'missing'} at {path}",
        "critical": True,
    }


def check_rag_system() -> dict:
    """Verify that the local RAG utility exists, is readable, and compiles."""
    if not RAG_SYSTEM_PATH.exists():
        return {
            "name": "tools/rag_system.py",
            "status": "FAILURE",
            "detail": f"tools/rag_system.py missing at {RAG_SYSTEM_PATH}",
            "critical": True,
        }
    if not os.access(RAG_SYSTEM_PATH, os.R_OK):
        return {
            "name": "tools/rag_system.py",
            "status": "FAILURE",
            "detail": f"tools/rag_system.py is not readable at {RAG_SYSTEM_PATH}",
            "critical": True,
        }
    try:
        source = RAG_SYSTEM_PATH.read_text(encoding="utf-8")
        compile(source, str(RAG_SYSTEM_PATH), "exec")
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return {
            "name": "tools/rag_system.py",
            "status": "FAILURE",
            "detail": f"tools/rag_system.py failed compile validation: {exc}",
            "critical": True,
        }
    return {
        "name": "tools/rag_system.py",
        "status": "SUCCESS",
        "detail": f"tools/rag_system.py found, readable, and compile-valid at {RAG_SYSTEM_PATH}",
        "critical": True,
    }


def scan_structural_anomalies(root: Path) -> list[dict]:
    findings: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", ".mypy_cache"}]
        current = Path(dirpath)

        if any(part in PROTECTED_DIRS for part in current.parts):
            continue

        for name in filenames:
            if name.startswith(".") and name not in {".gitignore"}:
                findings.append(
                    {
                        "name": f"hidden_file::{name}",
                        "status": "WARNING",
                        "detail": f"Hidden or anomalous file detected: {current / name}",
                        "critical": False,
                    }
                )
            if name.endswith(SUSPICIOUS_SUFFIXES):
                findings.append(
                    {
                        "name": f"suspicious_suffix::{name}",
                        "status": "WARNING",
                        "detail": f"Suspicious backup/temporary file detected: {current / name}",
                        "critical": False,
                    }
                )

    return findings


def check_protected_dirs(root: Path) -> list[dict]:
    results = []
    for protected in PROTECTED_DIRS:
        protected_path = root / protected
        if protected_path.exists():
            results.append(
                {
                    "name": f"protected_dir::{protected}",
                    "status": "SUCCESS",
                    "detail": f"Protected directory is present and controlled: {protected_path}",
                    "critical": True,
                }
            )
        else:
            results.append(
                {
                    "name": f"protected_dir::{protected}",
                    "status": "WARNING",
                    "detail": f"Protected directory {protected_path} is not present; this is acceptable only when intentionally absent.",
                    "critical": False,
                }
            )
    return results


def check_streamlit_runtime() -> dict:
    present = importlib.util.find_spec("streamlit") is not None
    return {
        "name": "streamlit_runtime",
        "status": "SUCCESS" if present else "WARNING",
        "detail": "Streamlit runtime available" if present else "Streamlit not installed in the current environment; UI features will not run until installed.",
        "critical": False,
    }


def run_checks() -> list[dict]:
    checks = []
    checks.append(check_file_exists(CONTRACTS_PATH, "CONTRACTS.md"))
    checks.append(check_file_exists(DECISIONS_LOG_PATH, "tools/DECISIONS_LOG.md"))
    checks.append(check_file_exists(ACTIVITY_LOG_PATH, "tools/activity_log.json"))
    checks.append(check_file_exists(ERROR_LOG_PATH, "tools/errors.log"))
    checks.append(check_file_exists(COMMAND_CENTER_PATH, "tools/command_center.py"))
    checks.append(check_file_exists(DISCIPLINE_PATH, "tools/discipline.py"))
    checks.append(check_rag_system())
    checks.extend(check_protected_dirs(PROJECT_ROOT))
    checks.append(check_streamlit_runtime())
    checks.extend(scan_structural_anomalies(PROJECT_ROOT))
    return checks


def print_summary(checks: list[dict]) -> tuple[int, int, int]:
    success = sum(1 for item in checks if item["status"] == "SUCCESS")
    warning = sum(1 for item in checks if item["status"] == "WARNING")
    failure = sum(1 for item in checks if item["status"] == "FAILURE")

    print("\n=== EnterpriseGuard Verification Summary ===")
    print(f"SUCCESS: {success}")
    print(f"WARNING: {warning}")
    print(f"FAILURE: {failure}")
    print("-------------------------------------------")

    for item in checks:
        print(f"[{item['status']}] {item['name']} - {item['detail']}")

    print("===========================================\n")
    return success, warning, failure


def main() -> int:
    ensure_tools_dir()
    checks = run_checks()
    success, warning, failure = print_summary(checks)

    verdict = "SUCCESS"
    if failure > 0:
        verdict = "FAILURE"
    elif warning > 0:
        verdict = "WARNING"

    append_activity(f"Checklist verification run: {verdict} (success={success}, warning={warning}, failure={failure})")

    if failure > 0:
        log_error(f"Checklist verification failed with {failure} critical failures.")
        print("\nVerification failed: critical compliance checks did not pass.")
        return 1

    if warning > 0:
        print("\nVerification completed with warnings; project is operational but some non-critical checks should be reviewed.")
        return 0

    print("\nVerification completed successfully. EnterpriseGuard is in compliance with the active governance baseline.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        log_error(f"Unexpected checklist execution error: {exc}")
        append_activity("Checklist verification run: FAILURE (unexpected script error)")
        print(f"\nUnexpected error: {exc}")
        raise SystemExit(1)
