#!/usr/bin/env python3
"""
EnterpriseGuard ADIE - Centralized paths configuration (Production-Ready).

Supports three categories:
- DATA_DIR : dynamic files written during runtime
- LOG_DIR  : log files (errors.log, etc.)
- STATIC_DIR: governance/critical files (baselines, identity, decisions)

Environment overrides:
- ENTERPRISEGUARD_DATA_DIR
- ENTERPRISEGUARD_LOG_DIR
- ENTERPRISEGUARD_STATIC_DIR

If DATA_DIR is set but LOG_DIR is not, LOG_DIR follows DATA_DIR.
If STATIC_DIR is not set, it remains ROOT/tools (install prefix/tools in production).
"""

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

# Development defaults
DEV_DATA_DIR = (ROOT / "tools").resolve()
DEV_LOG_DIR = (ROOT / "tools").resolve()
DEV_STATIC_DIR = (ROOT / "tools").resolve()


def _to_abs(value: str | None) -> Path | None:
    """Return absolute Path or None."""
    if not value:
        return None
    return Path(value).resolve()


_env_data = _to_abs(os.environ.get("ENTERPRISEGUARD_DATA_DIR"))
_env_log = _to_abs(os.environ.get("ENTERPRISEGUARD_LOG_DIR"))
_env_static = _to_abs(os.environ.get("ENTERPRISEGUARD_STATIC_DIR"))

if _env_data is not None:
    DATA_DIR = _env_data
    LOG_DIR = _env_log if _env_log is not None else _env_data
else:
    DATA_DIR = DEV_DATA_DIR
    LOG_DIR = DEV_LOG_DIR

if _env_static is not None:
    STATIC_DIR = _env_static
else:
    STATIC_DIR = DEV_STATIC_DIR

# ------------------------------------------------------------
# Dynamic paths (written during operation)
# ------------------------------------------------------------
ACTIVITY_LOG_PATH = DATA_DIR / "activity_log.json"
ERROR_LOG_PATH = LOG_DIR / "errors.log"
REALTIME_EVENTS_PATH = DATA_DIR / "realtime_events.jsonl"
INNOCENCE_CHAIN_PATH = DATA_DIR / "innocence_chain.json"
RELATIONAL_MEMORY_PATH = DATA_DIR / "relational_memory.json"
DIMENSIONAL_STATE_PATH = DATA_DIR / "dimensional_state.json"
DIMENSIONAL_HISTORY_PATH = DATA_DIR / "dimensional_history.jsonl"

# ------------------------------------------------------------
# Static / governance paths (not moved to /var/lib)
# ------------------------------------------------------------
TRUSTED_BASELINE_PATH = STATIC_DIR / "TRUSTED_BASELINE.json"
TRUSTED_BASELINE_SENTINEL_PATH = STATIC_DIR / "TRUSTED_BASELINE_SENTINEL.json"
INTEGRITY_BASELINE_PATH = STATIC_DIR / "integrity_baseline.json"
INTEGRITY_BASELINE_SENTINEL_PATH = STATIC_DIR / "integrity_baseline_sentinel.json"
HARDWARE_IDENTITY_PATH = STATIC_DIR / "hardware_identity.json"
GENESIS_BASELINE_PATH = STATIC_DIR / "genesis_baseline.json"
DECISIONS_LOG_PATH = STATIC_DIR / "DECISIONS_LOG.md"


def ensure_dirs() -> None:
    """Create data/log/static directories if missing. Call explicitly."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)


def validate_paths() -> bool:
    """
    Check that directories exist and are writable/readable as needed.
    Returns True if all basic requirements are met.
    """
    for d in (DATA_DIR, LOG_DIR, STATIC_DIR):
        if not d.exists() or not d.is_dir():
            return False
        if not os.access(d, os.R_OK):
            return False

    # Writable only for data/log, not necessarily static
    if not os.access(DATA_DIR, os.W_OK):
        return False
    if not os.access(LOG_DIR, os.W_OK):
        return False

    return True
