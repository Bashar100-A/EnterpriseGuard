#!/usr/bin/env python3
"""
Documentation script for DC-122: Acceptance of SIBB Storage v7.2.

This script:
- Updates tools/DECISIONS_LOG.md with DC-122 entry.
- Updates continuity/CURRENT_STATE.md with current status.
- Updates continuity/COMPONENTS.md with SIBB component entry.
- Updates tests/TEST_RESULTS.md with the latest test results.

All modifications follow project rules:
- Timestamped backup before modification.
- Atomic writes using tempfile.mkstemp and os.replace.
- Protected directories (adie/, intelligence/) are never accessed.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Ensure no bytecode is written
sys.dont_write_bytecode = True

# Project root (parent of tools/ directory)
ROOT = Path(__file__).resolve().parent.parent

# Ensure we are in the correct directory
if not (ROOT / "tools").exists() or not (ROOT / "continuity").exists():
    print("Error: This script must be run from the project root.")
    sys.exit(1)

def utc_now():
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def backup_file(path: Path):
    """Create a timestamped backup of a file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
    if path.exists():
        shutil.copy2(path, backup_path)
        print(f"  Backup created: {backup_path.name}")
    return backup_path

def atomic_write_text(path: Path, content: str):
    """Write text to a file atomically using tempfile + os.replace."""
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

def update_decisions_log():
    """Append DC-122 entry to DECISIONS_LOG.md."""
    log_path = ROOT / "tools" / "DECISIONS_LOG.md"
    if not log_path.exists():
        print(f"Error: {log_path} not found.")
        sys.exit(1)

    backup_file(log_path)

    entry = (
        f"| DC-122 | {utc_now()} | Acceptance of SIBB Storage v7.2 | "
        f"Implemented cross-platform WORM storage with metadata HMAC, encryption, access control, "
        f"orphan handling, and thread-safe locking. All 19 unit tests passed. | "
        f"19/19 tests passed, protected dirs untouched. | Complete |\n"
    )

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if DC-122 already exists
    if "DC-122" in content:
        print("  DC-122 already exists in DECISIONS_LOG.md, skipping.")
        return

    # Insert before any existing table end or just append at end of file
    if "| DC-121 |" in content:
        # Insert after last DC-121 line
        lines = content.splitlines(keepends=True)
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("| DC-121 |"):
                insert_idx = i + 1
                break
        if insert_idx is not None:
            lines.insert(insert_idx, entry)
            new_content = "".join(lines)
        else:
            new_content = content + entry
    else:
        # Append to end
        new_content = content.rstrip() + "\n" + entry

    atomic_write_text(log_path, new_content)
    print("  Updated DECISIONS_LOG.md with DC-122.")

def update_current_state():
    """Update continuity/CURRENT_STATE.md with latest status."""
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        print(f"Error: {state_path} not found.")
        sys.exit(1)

    backup_file(state_path)

    new_section = f"""
## Latest Update — {utc_now()}

- **Component:** SIBB Storage (`tools/sibb_storage.py`)
- **Version:** 7.2
- **Status:** ✅ Complete and tested
- **Tests:** 19/19 passed (unit and security tests)
- **Security:** Metadata HMAC, encryption (optional), access key enforcement, orphan file handling, thread-safe locking, cross-platform support.
- **Decision:** DC-122

---

"""
    with open(state_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Insert new section after the first line (title)
    lines = content.splitlines(keepends=True)
    insert_idx = 1  # after title line
    lines.insert(insert_idx, new_section)
    new_content = "".join(lines)

    atomic_write_text(state_path, new_content)
    print("  Updated CURRENT_STATE.md.")

def update_components():
    """Add SIBB Storage component to COMPONENTS.md if not present."""
    comp_path = ROOT / "continuity" / "COMPONENTS.md"
    if not comp_path.exists():
        print(f"Error: {comp_path} not found.")
        sys.exit(1)

    with open(comp_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "sibb_storage.py" in content:
        print("  sibb_storage.py already listed in COMPONENTS.md, skipping.")
        return

    backup_file(comp_path)

    new_row = "| SIBB Storage | tools/sibb_storage.py | 100% | ✅ Complete (v7.2, 19/19 tests) |\n"

    # Append row at the end of the table (before any trailing text)
    lines = content.splitlines(keepends=True)
    # Find the last table row that starts with '|'
    last_table_idx = None
    for i, line in enumerate(lines):
        if line.startswith("|"):
            last_table_idx = i
    if last_table_idx is not None:
        lines.insert(last_table_idx + 1, new_row)
    else:
        lines.append(new_row)

    new_content = "".join(lines)
    atomic_write_text(comp_path, new_content)
    print("  Updated COMPONENTS.md.")

def update_test_results():
    """Append latest test results to TEST_RESULTS.md."""
    test_path = ROOT / "tests" / "TEST_RESULTS.md"
    if not test_path.exists():
        print(f"Error: {test_path} not found.")
        sys.exit(1)

    backup_file(test_path)

    new_row = (
        f"| {utc_now()} | SIBB Storage | tests/test_sibb_storage.py | PASS | 19 | 0 | DC-122 | "
        f"All unit/security tests passed after v7.2 fixes. |\n"
    )

    with open(test_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Append to the markdown table
    if new_row.split('|')[1].strip() in content:
        print("  Test result already exists in TEST_RESULTS.md, skipping.")
        return

    # Simple append at end of file
    new_content = content.rstrip() + "\n" + new_row
    atomic_write_text(test_path, new_content)
    print("  Updated TEST_RESULTS.md.")

def main():
    print("=== Documenting DC-122: SIBB Storage v7.2 ===")
    update_decisions_log()
    update_current_state()
    update_components()
    update_test_results()
    print("\n✅ Documentation completed successfully.")
    print("Protected directories were not accessed.")

if __name__ == "__main__":
    main()
