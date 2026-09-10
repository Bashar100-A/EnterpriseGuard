#!/usr/bin/env python3
"""
Documentation script for Bandit result on SIBB Distributed Storage.

This script appends a note to continuity/CURRENT_STATE.md documenting that Bandit
was run on tools/sibb_distributed.py and no High/Medium issues were found.
Only one 'assert_used' (Low) in the self-test section was reported, which is acceptable.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def backup_file(path: Path):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
    if path.exists():
        shutil.copy2(path, backup_path)
        print(f"  Backup created: {backup_path.name}")

def atomic_write_text(path: Path, content: str):
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise

def update_current_state():
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        print(f"Error: {state_path} not found.")
        sys.exit(1)

    backup_file(state_path)

    note = (
        f"\n---\n\n"
        f"## Static Analysis Note — {utc_now()}\n\n"
        f"- **Tool:** Bandit\n"
        f"- **Target:** `tools/sibb_distributed.py`\n"
        f"- **Result:** No High or Medium severity issues found.\n"
        f"- **Details:** One Low issue: `assert_used` in the self-test block (not production code).\n"
        f"- **Status:** ✅ Accepted\n\n"
    )

    with open(state_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Append note at the end of file
    new_content = content.rstrip() + "\n" + note
    atomic_write_text(state_path, new_content)
    print("  Updated CURRENT_STATE.md with Bandit result.")

def main():
    print("=== Documenting Bandit result for SIBB Distributed Storage ===")
    update_current_state()
    print("✅ Documentation completed.")

if __name__ == "__main__":
    main()
