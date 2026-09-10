#!/usr/bin/env python3
"""Archive expired activity-log entries without deleting them permanently."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


def parse_utc_iso(value: str) -> datetime | None:
    """Parse a UTC ISO 8601 timestamp with a Z suffix into a timezone-aware datetime."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_activity_log(path: Path) -> tuple[list, str]:
    """Return the activity entries and the original root kind for the log file."""
    if not path.exists():
        return [], "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, TypeError):
        raise ValueError(f"Could not read JSON activity log: {path}") from None

    if isinstance(payload, list):
        return payload, "list"
    if isinstance(payload, dict):
        activities = payload.get("activities")
        if isinstance(activities, list):
            return activities, "dict"
    raise ValueError(f"Unsupported activity log structure in {path}: expected list or dict with 'activities'")


def write_activity_log(entries: list, path: Path, root_kind: str) -> None:
    """Write entries back to disk while preserving the original root structure."""
    if root_kind == "list":
        payload: Any = entries
    else:
        payload = {"activities": entries}

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def partition_by_expiry(entries: list, now_utc: datetime) -> tuple[list, list]:
    """Split entries into active and expired based on each entry's expires_at field."""
    active: list = []
    expired: list = []
    for entry in entries:
        if not isinstance(entry, dict):
            active.append(entry)
            continue
        expires_at = entry.get("expires_at")
        if not expires_at:
            active.append(entry)
            continue
        expiry_dt = parse_utc_iso(str(expires_at))
        if expiry_dt is None:
            active.append(entry)
            continue
        if expiry_dt < now_utc:
            expired.append(entry)
        else:
            active.append(entry)
    return active, expired


def archive_entries(entries: list, archive_path: Path, root_kind: str = "dict") -> None:
    """Write the expired entries to a GZIP-compressed JSON archive using atomic replace."""
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    payload: Any = entries if root_kind == "list" else {"activities": entries}
    tmp_path = archive_path.parent / f".{archive_path.name}.tmp"
    try:
        with gzip.open(tmp_path, "wt", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_path, archive_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _coerce_path(raw: str | None, repo_root: Path, default_name: str | None = None) -> Path | None:
    if raw is None:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = repo_root / path
    if default_name and path.name == default_name and path.parent == repo_root:
        return path
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive expired activity-log entries to GZIP while preserving active entries.")
    parser.add_argument("--archive-dir", default="tools/archive", help="Directory for generated .gz archive files")
    parser.add_argument("--output-log", default=None, help="Optional path for a cleaned active log; if omitted, no cleaned log is written")
    parser.add_argument("--max-entries-per-run", type=int, default=1000, help="Maximum number of expired entries to archive in one run")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without writing archives or cleaned logs")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    source_path = repo_root / "tools" / "activity_log.json"
    archive_dir = Path(args.archive_dir)
    if not archive_dir.is_absolute():
        archive_dir = repo_root / archive_dir
    output_log = _coerce_path(args.output_log, repo_root) if args.output_log else None

    try:
        entries, root_kind = load_activity_log(source_path)
    except ValueError as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}, sort_keys=True, indent=2))
        return 1

    now_utc = datetime.now(timezone.utc)
    active_entries, expired_entries = partition_by_expiry(entries, now_utc)

    max_entries = max(0, int(args.max_entries_per_run))
    truncated = False
    if max_entries and len(expired_entries) > max_entries:
        expired_entries = expired_entries[:max_entries]
        truncated = True

    archive_path: Path | None = None
    summary: dict[str, Any] = {
        "status": "OK",
        "source_path": str(source_path),
        "root_kind": root_kind,
        "total_entries": len(entries),
        "active_count": len(active_entries),
        "expired_count": len(expired_entries),
        "dry_run": args.dry_run,
        "max_entries_per_run": max_entries,
        "archive_path": None,
        "output_log": str(output_log) if output_log else None,
        "truncated": truncated,
    }

    if expired_entries and not args.dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"activity_log_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.gz"
        archive_entries(expired_entries, archive_path, root_kind=root_kind)
        summary["archive_path"] = str(archive_path)

    if output_log is not None:
        if output_log == source_path:
            summary["status"] = "WARNING"
            summary["message"] = "Refusing to overwrite the original activity log; output-log matches the source path."
        elif not args.dry_run:
            write_activity_log(active_entries, output_log, root_kind)
            summary["output_log"] = str(output_log)

    if args.dry_run:
        summary["status"] = "DRY_RUN"
        summary["message"] = "No archive or cleaned log was written because --dry-run was specified."

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
