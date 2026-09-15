#!/usr/bin/env python3
"""
Documentation script for Bandit result on SIBB-Innocence Integration.

This script appends a note to continuity/CURRENT_STATE.md documenting that Bandit
was run on tools/sibb_innocence_integration.py and no High/Medium issues were found.
Only two Low issues (try_except_pass, try_except_continue) were reported, both benign.
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
            if fallback_path.exists():
                existing = fallback_path.read_text(encoding='utf-8')
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

def utc_now_file():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def backup_file(path: Path):
    if path.exists():
        timestamp = utc_now_file()
        backup = path.with_name(f"{path.name}.bak_{timestamp}")
        shutil.copy2(path, backup, follow_symlinks=False)
        logger.info(f"Backup created: {backup.name}")

def atomic_write_text(path: Path, content: str):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

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
    return f"- **Target:** `{target}`" in content

def main():
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        logger.error("CURRENT_STATE.md not found")
        sys.exit(1)

    target = "tools/sibb_innocence_integration.py"
    note = (
        f"## Static Analysis Note — {utc_now()}\n\n"
        f"- **Tool:** Bandit\n"
        f"- **Target:** `{target}`\n"
        f"- **Result:** No High or Medium severity issues found.\n"
        f"- **Details:** Two Low issues: `try_except_pass`, `try_except_continue` (benign).\n"
        f"- **Status:** ✅ Accepted\n"
    )

    with open(state_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if note_exists(content, target):
        logger.warning("Note already exists in CURRENT_STATE.md. Skipping.")
        return

    backup_file(state_path)

    new_content = content.rstrip() + "\n\n" + note + "\n"
    atomic_write_text(state_path, new_content)
    logger.info("Updated CURRENT_STATE.md with Bandit result.")

    append_activity("documentation", {
        "file": str(state_path),
        "target": target,
        "tool": "Bandit",
        "result": "No High/Medium issues",
        "timestamp": utc_now()
    })

if __name__ == "__main__":
    main()
