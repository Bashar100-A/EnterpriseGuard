import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.time_utils import utc_now
from tools.audit_chain import append_activity as audit_append_activity
from tools.paths_config import ACTIVITY_LOG_PATH as _CENTRAL_ACTIVITY_LOG
from tools.paths_config import ERROR_LOG_PATH as _CENTRAL_ERROR_LOG

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
CONTRACTS_PATH = PROJECT_ROOT / "CONTRACTS.md"
DECISIONS_LOG_PATH = TOOLS_DIR / "DECISIONS_LOG.md"
ACTIVITY_LOG_PATH = _CENTRAL_ACTIVITY_LOG
ERROR_LOG_PATH = _CENTRAL_ERROR_LOG
COMMAND_CENTER_PATH = TOOLS_DIR / "command_center.py"
EPHEMERAL_ARCHIVER_PATH = TOOLS_DIR / "ephemeral_archiver.py"
HARDWARE_IDENTITY_PATH = TOOLS_DIR / "hardware_identity.json"
GENESIS_BASELINE_PATH = TOOLS_DIR / "genesis_baseline.json"
RELATIONAL_MEMORY_PATH = TOOLS_DIR / "relational_memory.py"
DISTRIBUTED_PROOF_PATH = TOOLS_DIR / "distributed_proof.py"
INNOCENCE_CHAIN_PATH = TOOLS_DIR / "innocence_chain.py"
DISCIPLINE_PATH = TOOLS_DIR / "discipline.py"
RAG_SYSTEM_PATH = TOOLS_DIR / "rag_system.py"
HYBRID_RETRIEVAL_PATH = TOOLS_DIR / "hybrid_retrieval.py"
REQUIREMENTS_LOCK_PATH = TOOLS_DIR / "requirements.lock.txt"

PROTECTED_DIRS = ["adie", "intelligence"]
SUSPICIOUS_SUFFIXES = (".bak", ".tmp", ".orig", ".swp")

def utc_timestamp() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")

def ensure_tools_dir() -> None:
    TOOLS_DIR.mkdir(exist_ok=True, parents=True)

def append_activity(event: str, path: Path | str | None = None) -> None:
    ensure_tools_dir()
    target_path = Path(path) if path is not None else ACTIVITY_LOG_PATH
    try:
        audit_append_activity(
            {
                "activity_type": "checklist",
                "event": event,
                "details": event,
                "status": "success",
            },
            target_path,
        )
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

def check_file_exists(path: Path, label: str, critical: bool = True) -> dict:
    exists = path.exists()
    status = "SUCCESS" if exists else ("WARNING" if not critical else "FAILURE")
    return {
        "name": label,
        "status": status,
        "detail": f"{label} {'found' if exists else 'missing'} at {path}",
        "critical": critical,
    }

def check_optional_file(path: Path, label: str) -> dict:
    return check_file_exists(path, label, critical=False)

def check_integrity_baseline() -> dict:
    """Validate the integrity baseline against its sentinel and current monitored files."""
    baseline_path = TOOLS_DIR / "integrity_baseline.json"
    sentinel_path = PROJECT_ROOT / "integrity_baseline_sentinel.json"

    if not baseline_path.exists():
        return {
            "name": "Integrity Baseline",
            "status": "WARNING",
            "detail": "integrity_baseline.json missing",
            "critical": False,
        }
    if not sentinel_path.exists():
        return {
            "name": "Integrity Baseline",
            "status": "WARNING",
            "detail": "integrity_baseline_sentinel.json missing",
            "critical": False,
        }

    try:
        baseline_bytes = baseline_path.read_bytes()
        baseline_data = json.loads(baseline_bytes.decode("utf-8"))
    except Exception:
        return {
            "name": "Integrity Baseline",
            "status": "FAILURE",
            "detail": "integrity_baseline.json malformed",
            "critical": True,
        }

    if not isinstance(baseline_data, dict) or not isinstance(baseline_data.get("files"), list):
        return {
            "name": "Integrity Baseline",
            "status": "FAILURE",
            "detail": "integrity_baseline.json malformed",
            "critical": True,
        }

    try:
        sentinel_data = json.loads(sentinel_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "name": "Integrity Baseline",
            "status": "FAILURE",
            "detail": "integrity_baseline_sentinel.json malformed",
            "critical": True,
        }

    baseline_hash = hashlib.sha256(baseline_bytes).hexdigest()
    sentinel_hash = sentinel_data.get("sha256")
    if sentinel_hash != baseline_hash:
        return {
            "name": "Integrity Baseline",
            "status": "FAILURE",
            "detail": "Sentinel mismatch",
            "critical": True,
        }

    current_by_path = {}
    for file_path in sorted(TOOLS_DIR.iterdir(), key=lambda p: p.name):
        if not file_path.is_file():
            continue
        name = file_path.name
        if name.startswith("."):
            continue
        if ".bak_" in name or name.endswith((".bak", ".tmp", ".orig", ".swp")):
            continue
        if name in {'activity_log.json', 'errors.log', 'DECISIONS_LOG.md', 'dimensional_history.jsonl'}:
            continue
        if name.endswith(".py") or name in {
            "DECISIONS_LOG.md",
            "activity_log.json",
            "errors.log",
            "TRUSTED_BASELINE.json",
            "dimensional_history.jsonl",
            "TRUSTED_BASELINE_SENTINEL.json",
            "requirements.lock.txt",
        }:
            current_by_path[file_path.relative_to(PROJECT_ROOT).as_posix()] = file_path

    baseline_index = {}
    for entry in baseline_data["files"]:
        if isinstance(entry, dict) and "path" in entry:
            baseline_index[entry["path"]] = entry

    missing_files = []
    modified_files = []
    warnings = []
    for entry in baseline_data["files"]:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not path:
            continue
        file_path = PROJECT_ROOT / path
        if not file_path.exists():
            missing_files.append(path)
            continue
        current_size = file_path.stat().st_size
        current_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if entry.get("size") != current_size or entry.get("sha256") != current_hash:
            modified_files.append(path)

    for path, file_path in sorted(current_by_path.items()):
        if path not in baseline_index:
            warnings.append(path)

    if missing_files or modified_files:
        detail_parts = []
        if missing_files:
            detail_parts.append(f"missing={len(missing_files)}:{'; '.join(missing_files[:5])}")
        if modified_files:
            detail_parts.append(f"modified={len(modified_files)}:{'; '.join(modified_files[:5])}")
        return {
            "name": "Integrity Baseline",
            "status": "FAILURE",
            "detail": " | ".join(detail_parts),
            "critical": True,
        }
    if warnings:
        return {
            "name": "Integrity Baseline",
            "status": "WARNING",
            "detail": f"New files detected in monitored scope: {', '.join(warnings[:5])}",
            "critical": False,
        }
    return {
        "name": "Integrity Baseline",
        "status": "SUCCESS",
        "detail": f"Verified {len(baseline_data['files'])} entries against the current monitored file set.",
        "critical": False,
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

def check_innocence_chain() -> dict:
    """Verify that innocence_chain.py exists, is readable, and compiles."""
    if not INNOCENCE_CHAIN_PATH.exists():
        return {
            "name": "tools/innocence_chain.py",
            "status": "FAILURE",
            "detail": f"tools/innocence_chain.py missing at {INNOCENCE_CHAIN_PATH}",
            "critical": True,
        }
    if not os.access(INNOCENCE_CHAIN_PATH, os.R_OK):
        return {
            "name": "tools/innocence_chain.py",
            "status": "FAILURE",
            "detail": f"tools/innocence_chain.py is not readable at {INNOCENCE_CHAIN_PATH}",
            "critical": True,
        }
    try:
        source = INNOCENCE_CHAIN_PATH.read_text(encoding="utf-8")
        compile(source, str(INNOCENCE_CHAIN_PATH), "exec")
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return {
            "name": "tools/innocence_chain.py",
            "status": "FAILURE",
            "detail": f"tools/innocence_chain.py failed compile validation: {exc}",
            "critical": True,
        }
    return {
        "name": "tools/innocence_chain.py",
        "status": "SUCCESS",
        "detail": f"tools/innocence_chain.py found, readable, and compile-valid at {INNOCENCE_CHAIN_PATH}",
        "critical": True,
    }

def scan_structural_anomalies(root: Path) -> list[dict]:
    findings: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", ".mypy_cache"}]
        current = Path(dirpath)

        if any(part in PROTECTED_DIRS for part in current.parts):
            continue
        if "quarantine" in current.parts:
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
    checks.append(check_file_exists(EPHEMERAL_ARCHIVER_PATH, "tools/ephemeral_archiver.py"))
    checks.append(check_file_exists(HARDWARE_IDENTITY_PATH, "tools/hardware_identity.json"))
    checks.append(check_file_exists(GENESIS_BASELINE_PATH, "tools/genesis_baseline.json"))
    checks.append(check_file_exists(RELATIONAL_MEMORY_PATH, "tools/relational_memory.py"))
    checks.append(check_file_exists(DISTRIBUTED_PROOF_PATH, "tools/distributed_proof.py"))
    checks.append(check_innocence_chain())                     # ← Added
    checks.append(check_optional_file(DISCIPLINE_PATH, "tools/discipline.py"))
    checks.append(check_optional_file(HYBRID_RETRIEVAL_PATH, "tools/hybrid_retrieval.py"))
    checks.append(check_optional_file(REQUIREMENTS_LOCK_PATH, "tools/requirements.lock.txt"))
    checks.append(check_rag_system())
    checks.append(check_integrity_baseline())
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

    append_activity(f"Checklist verification run: {verdict} (success={success}, warning={warning}, failure={failure})", ACTIVITY_LOG_PATH)

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
        append_activity("Checklist verification run: FAILURE (unexpected script error)", ACTIVITY_LOG_PATH)
        print(f"\nUnexpected error: {exc}")
        raise SystemExit(1)
