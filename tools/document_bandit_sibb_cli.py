#!/usr/bin/env python3
"""
Documentation script for Bandit result on SIBB CLI.

This script appends a note to continuity/CURRENT_STATE.md documenting that Bandit
was run on tools/sibb_cli.py and no High/Medium issues were found.
Only one Low issue (try_except_pass) was reported, which is benign.

Improvements:
- Global file lock to prevent concurrent executions
- Atomic audit fallback with 0600 permissions
- Backup failure aborts operation
- Insert note after first main title instead of at end
- Removed os.access, rely on mkstemp
- Unified timestamp
- Improved duplicate detection
"""

import os
import sys
import json
import logging
import tempfile
import shutil
import fcntl
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Optional audit chain integration
try:
    from tools.audit_chain import append_activity
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False
    def append_activity(event_type, details):
        # Atomic audit fallback with 0600 permissions
        fallback_path = ROOT / "tools" / "audit_fallback.jsonl"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({
            "event": event_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }) + "\n"
        fd, tmp = tempfile.mkstemp(dir=fallback_path.parent, prefix=".audit.", suffix=".tmp")
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(record)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp, 0o600)
            # Append atomically by reading existing content
            if fallback_path.exists():
                existing = fallback_path.read_text(encoding='utf-8')
                with open(tmp, 'a') as f:
                    f.write(existing)  # no, this is wrong: we want to append new record to old content
                # Correct approach: read old, write old+new to tmp, then replace
                with open(tmp, 'w') as f:
                    f.write(existing + record)
            else:
                with open(tmp, 'w') as f:
                    f.write(record)
            os.replace(tmp, fallback_path)
        except Exception as e:
            logger.error(f"Failed to write audit fallback: {e}")
            try:
                os.unlink(tmp)
            except Exception:
                pass
        else:
            try:
                os.unlink(tmp)
            except Exception:
                pass

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def backup_file(path: Path):
    """Create a timestamped backup. Raises if fails."""
    if path.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = path.with_name(f"{path.name}.bak_{timestamp}")
        try:
            shutil.copy2(path, backup, follow_symlinks=False)
            logger.info(f"Backup created: {backup.name}")
            return backup
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    else:
        logger.warning(f"Source file does not exist: {path}")
        return path

def atomic_write_text(path: Path, content: str):
    """Write text atomically with directory fsync."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

        # fsync directory
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise

def note_exists(content: str, target: str) -> bool:
    # Use unique marker consisting of target and "Bandit"
    return f"## Static Analysis Note" in content and f"- **Target:** `{target}`" in content

def main():
    # Acquire global lock to prevent concurrent execution
    lock_path = ROOT / "tools" / ".document_bandit.lock"
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        state_path = ROOT / "continuity" / "CURRENT_STATE.md"
        if not state_path.exists():
            logger.error("CURRENT_STATE.md not found")
            sys.exit(1)

        target = "tools/sibb_cli.py"
        note = (
            f"## Static Analysis Note — {utc_now()}\n\n"
            f"- **Tool:** Bandit\n"
            f"- **Target:** `{target}`\n"
            f"- **Result:** No High or Medium severity issues found.\n"
            f"- **Details:** One Low issue: `try_except_pass` (benign).\n"
            f"- **Status:** ✅ Accepted\n"
        )

        with open(state_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if note_exists(content, target):
            logger.warning("Note already exists in CURRENT_STATE.md. Skipping.")
            return

        # Create backup (will raise if fails)
        backup_file(state_path)

        # Insert note after first main title
        lines = content.splitlines(keepends=True)
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_idx = i + 1
                break
        if insert_idx is None:
            insert_idx = 0

        # Ensure blank line after title
        if insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1

        note_block = "\n" + note + "\n"
        lines.insert(insert_idx, note_block)
        new_content = "".join(lines)

        atomic_write_text(state_path, new_content)
        logger.info("Updated CURRENT_STATE.md with Bandit result.")

        # Audit log
        append_activity("documentation", {
            "file": str(state_path),
            "target": target,
            "tool": "Bandit",
            "result": "No High/Medium issues",
            "timestamp": utc_now()
        })

    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)

if __name__ == "__main__":
    main()
