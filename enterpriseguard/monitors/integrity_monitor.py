#!/usr/bin/env python3
"""Self-Doubting Core integrity monitor.

This module creates and validates SHA-256 baselines for a small, curated set
of project files under the tools/ directory. It intentionally remains
self-contained and does not import any project modules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

sys.dont_write_bytecode = True

MONITORED_GOVERNANCE_FILES = [
    "DECISIONS_LOG.md",
    "activity_log.json",
    "errors.log",
    "TRUSTED_BASELINE.json",
    "TRUSTED_BASELINE_SENTINEL.json",
    "requirements.lock.txt",
    "dimensional_history.jsonl",
]


def utc_now_iso() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 with a Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_file_sha256(path: Path) -> str:
    """Compute a SHA-256 digest for the supplied file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_monitored_files(root_path: Union[Path, List[Path]]) -> List[Path]:
    """Return the file set that is in scope for integrity tracking."""
    if isinstance(root_path, (list, tuple)):
        return list(root_path)

    tools_dir = root_path / "tools"
    if not tools_dir.exists():
        return []
    monitored: List[Path] = []
    for child in sorted(tools_dir.iterdir(), key=lambda p: p.name):
        if not child.is_file():
            continue
        name = child.name
        if name.startswith("."):
            continue
        if ".bak_" in name:
            continue
        if name.endswith(".tmp") or ("tmp" in name.lower() and name.startswith(".")):
            continue
        if name in {"activity_log.json", "errors.log", "DECISIONS_LOG.md", "dimensional_history.jsonl"}:
            continue
        if name.endswith(".py") or name in MONITORED_GOVERNANCE_FILES:
            monitored.append(child)
    return monitored


def generate_baseline(
    root_path: Union[Path, List[Path]],
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> dict:
    """Generate a SHA-256 baseline for the monitored file set."""
    target_path = output_path or baseline_path
    if target_path is None:
        if isinstance(root_path, Path):
            target_path = root_path / "tools" / "integrity_baseline.json"
        else:
            target_path = Path("tools/integrity_baseline.json")

    monitored_files = collect_monitored_files(root_path)
    
    if isinstance(root_path, (list, tuple)):
        base_path = root_path[0].parent if root_path else Path(".")
    else:
        base_path = root_path

    timestamp = utc_now_iso()
    baseline = {
        "schema_version": "1.0",
        "algorithm": "sha256",
        "generated_at": timestamp,
        "files": [],
    }
    for file_path in monitored_files:
        try:
            rel_path = file_path.relative_to(base_path).as_posix()
        except ValueError:
            rel_path = file_path.name
        baseline["files"].append(
            {
                "path": rel_path,
                "size": file_path.stat().st_size,
                "sha256": compute_file_sha256(file_path),
            }
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.", suffix=".tmp", dir=str(target_path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(baseline, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, target_path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return baseline


def load_baseline(baseline_path: Path) -> Optional[dict]:
    """Load and validate the integrity baseline if it exists."""
    if not baseline_path.exists():
        return None
    try:
        with baseline_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed baseline JSON: {baseline_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Baseline must be a JSON object: {baseline_path}")
    if "files" not in data or not isinstance(data["files"], list):
        raise ValueError(f"Baseline missing required 'files' list: {baseline_path}")
    return data


def check_integrity(
    root_path: Union[Path, List[Path]],
    baseline_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> dict:
    """Compare the current monitored files against the stored baseline."""
    target_path = output_path or baseline_path
    if target_path is None:
        if isinstance(root_path, Path):
            target_path = root_path / "tools" / "integrity_baseline.json"
        else:
            target_path = Path("tools/integrity_baseline.json")

    baseline = load_baseline(target_path)
    if baseline is None:
        return {"status": "MISSING", "errors": ["baseline missing"], "warnings": []}

    baseline_map: Dict[str, Dict[str, Any]] = {}
    for entry in baseline.get("files", []):
        if not isinstance(entry, dict):
            raise ValueError("Malformed baseline entry: expected object")
        path = entry.get("path")
        if path:
            baseline_map[path] = entry

    if isinstance(root_path, (list, tuple)):
        base_path = root_path[0].parent if root_path else Path(".")
    else:
        base_path = root_path

    current_files = {}
    for file_path in collect_monitored_files(root_path):
        try:
            rel_path = file_path.relative_to(base_path).as_posix()
        except ValueError:
            rel_path = file_path.name
        current_files[rel_path] = {
            "size": file_path.stat().st_size,
            "sha256": compute_file_sha256(file_path),
        }

    errors: List[str] = []
    warnings: List[str] = []
    for path, expected in baseline_map.items():
        current = current_files.get(path)
        if current is None:
            errors.append(path)
            continue
        if expected.get("size") != current["size"] or expected.get("sha256") != current["sha256"]:
            errors.append(path)

    for path in sorted(current_files):
        if path not in baseline_map:
            warnings.append(path)

    status = "PASS"
    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"

    return {"status": status, "errors": errors, "warnings": warnings}


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project integrity monitor")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--generate-baseline", action="store_true", help="Generate a new integrity baseline")
    group.add_argument("--check", action="store_true", help="Compare current monitored files against the baseline")
    return parser


def main() -> int:
    parser = build_cli_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    baseline_path = repo_root / "tools" / "integrity_baseline.json"

    if args.generate-baseline:
        result = generate_baseline(repo_root, baseline_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.check:
        result = check_integrity(repo_root, baseline_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] in {"PASS", "WARN"} else 1

    parser.print_usage(sys.stderr)
    print(f"{parser.prog}: error: one of --generate-baseline or --check is required", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
