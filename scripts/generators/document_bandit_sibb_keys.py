#!/usr/bin/env python3
"""
Documentation script for Bandit result on SIBB Key Management.

This script appends a note to continuity/CURRENT_STATE.md documenting that Bandit
was run on tools/sibb_keys.py and no High/Medium issues were found.
Only Low issues (try_except_pass, hardcoded_password_funcarg, assert_used) were reported,
all of which are benign or in self-test code.

Improvements:
- Prevents duplicate notes for the same target file.
- Fails if backup cannot be created.
- Uses ISO 8601 UTC timestamps.
- Logs the documentation action to audit chain via append_activity (if available).
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Optional audit chain integration
try:
    from tools.audit_chain import append_activity
except ImportError:
    def append_activity(event_type, details):
        logger.warning(f"Audit chain not available, event not logged: {event_type} | {details}")

def utc_now():
    """Return current UTC timestamp in ISO 8601 format with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def utc_now_file():
    """Return timestamp for backup filename (compact)."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def backup_file(path: Path) -> Path:
    """Create a timestamped backup. Raises exception if backup fails."""
    timestamp = utc_now_file()
    backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
    if path.exists():
        try:
            shutil.copy2(path, backup_path)
            logger.info(f"Backup created: {backup_path.name}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    else:
        logger.warning(f"Source file does not exist, no backup created: {path}")
        return backup_path

def atomic_write_text(path: Path, content: str):
    """Write text to file atomically using tempfile + os.replace."""
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        logger.debug(f"Atomically wrote {path}")
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise

def note_exists(content: str, target_file: str) -> bool:
    """Check if a note for the target file already exists in content."""
    marker = f"- **Target:** `{target_file}`"
    return marker in content

def update_current_state():
    """Append Bandit result note to CURRENT_STATE.md if not already present."""
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        logger.error(f"Error: {state_path} not found.")
        sys.exit(1)

    # Create backup (will raise if fails)
    backup_file(state_path)

    target_file = "tools/sibb_keys.py"
    note = (
        f"## Static Analysis Note — {utc_now()}\n\n"
        f"- **Tool:** Bandit\n"
        f"- **Target:** `{target_file}`\n"
        f"- **Result:** No High or Medium severity issues found.\n"
        f"- **Details:** Low issues: `try_except_pass` (x2), `hardcoded_password_funcarg` (self-test), `assert_used` (self-test).\n"
        f"- **Status:** ✅ Accepted\n"
    )

    with open(state_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Prevent duplicate notes
    if note_exists(content, target_file):
        logger.warning("Note for this target already exists in CURRENT_STATE.md. Skipping.")
        return

    # Append note with a single blank line separation
    new_content = content.rstrip() + "\n\n" + note
    atomic_write_text(state_path, new_content)
    logger.info("Updated CURRENT_STATE.md with Bandit result.")

    # Audit log the documentation action
    append_activity("documentation", {
        "file": str(state_path),
        "target": target_file,
        "tool": "Bandit",
        "result": "No High/Medium issues",
        "timestamp": utc_now()
    })

def main():
    logger.info("=== Documenting Bandit result for SIBB Key Management ===")
    update_current_state()
    logger.info("✅ Documentation completed successfully.")

if __name__ == "__main__":
    main()
