#!/usr/bin/env python3
"""
Dimensional State - Central state store for Dimensional Intersection Engine.
Uses centralized path from tools.paths_config for dimensional_state.json.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import DIMENSIONAL_STATE_PATH

STATE_FILE = DIMENSIONAL_STATE_PATH


def _now_iso() -> str:
    """Return current UTC timestamp as ISO 8601 with Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write_json(data: dict, path: Path) -> None:
    """Write JSON atomically using mkstemp + os.replace, with owner-only permissions."""
    fd, tmp_path = tempfile.mkstemp(prefix=".dimensional_state_", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
        os.chmod(path, 0o600)  # owner read/write only
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


class DimensionalState:
    """Central state object for dimension scores."""
    def __init__(self, path: Path = STATE_FILE):
        self.path = path
        if not self.path.exists():
            self._init_empty()

    def _init_empty(self):
        """Create an empty state file if it does not exist."""
        data = {
            "updated_at": _now_iso(),
            "dimensions": {}
        }
        _atomic_write_json(data, self.path)

    def load(self) -> dict:
        """Load state from file, or return empty if missing/corrupt."""
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                # Corrupted state: treat as empty
                return {"updated_at": _now_iso(), "dimensions": {}}
        return {"updated_at": _now_iso(), "dimensions": {}}

    def save(self, data: dict) -> None:
        """Save state to file atomically."""
        data["updated_at"] = _now_iso()
        _atomic_write_json(data, self.path)

    def report(self, dimension_name: str, score: float, details: dict = None) -> None:
        """Record a dimension score."""
        data = self.load()
        data["dimensions"][dimension_name] = {
            "score": score,
            "details": details or {},
            "checked_at": _now_iso()
        }
        self.save(data)

    @property
    def current_tick_data(self) -> dict:
        """Return the current tick data: all dimensions and scores."""
        data = self.load()
        return {
            "updated_at": data.get("updated_at"),
            "dimensions": data.get("dimensions", {})
        }

    def get_dimension(self, name: str) -> dict | None:
        """Return dimension data if exists."""
        data = self.load()
        return data["dimensions"].get(name)

    def get_all_dimensions(self) -> dict:
        """Return all dimensions."""
        data = self.load()
        return data["dimensions"]


if __name__ == "__main__":
    # Self-test (not part of normal operation)
    state = DimensionalState()
    state.report("spatial", 1.0, {"source": "integrity_monitor --check"})
    print(json.dumps(state.current_tick_data, indent=2))
