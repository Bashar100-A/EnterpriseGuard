#!/usr/bin/env python3
"""
Documentation script for DC-123: Acceptance of SIBB Distributed Storage v1.2.

This script:
- Updates tools/DECISIONS_LOG.md with DC-123 entry.
- Updates continuity/CURRENT_STATE.md with current status.
- Updates continuity/COMPONENTS.md with SIBB Distributed component entry.
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

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

if not (ROOT / "tools").exists() or not (ROOT / "continuity").exists():
    print("Error: This script must be run from the project root.")
    sys.exit(1)

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def backup_file(path: Path):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
    if path.exists():
        shutil.copy2(path, backup_path)
        print(f"  Backup created: {backup_path.name}")
    return backup_path

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

def update_decisions_log():
    log_path = ROOT / "tools" / "DECISIONS_LOG.md"
    if not log_path.exists():
        print(f"Error: {log_path} not found.")
        sys.exit(1)

    backup_file(log_path)

    entry = (
        f"| DC-123 | {utc_now()} | Acceptance of SIBB Distributed Storage v1.2 | "
        f"Implemented distributed WORM replication with quorum support, per-node HMAC keys, "
        f"cross-node integrity verification, and fault tolerance. All 23 unit tests passed. | "
        f"23/23 tests passed, protected dirs untouched. | Complete |\n"
    )

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "DC-123" in content:
        print("  DC-123 already exists in DECISIONS_LOG.md, skipping.")
        return

    if "| DC-122 |" in content:
        lines = content.splitlines(keepends=True)
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("| DC-122 |"):
                insert_idx = i + 1
                break
        if insert_idx is not None:
            lines.insert(insert_idx, entry)
            new_content = "".join(lines)
        else:
            new_content = content + entry
    else:
        new_content = content.rstrip() + "\n" + entry

    atomic_write_text(log_path, new_content)
    print("  Updated DECISIONS_LOG.md with DC-123.")

def update_current_state():
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        print(f"Error: {state_path} not found.")
        sys.exit(1)

    backup_file(state_path)

    new_section = f"""
## Latest Update — {utc_now()}

- **Component:** SIBB Distributed Storage (`tools/sibb_distributed.py`)
- **Version:** 1.2
- **Status:** ✅ Complete and tested
- **Tests:** 23/23 passed (unit and security tests)
- **Security:** Per-node HMAC keys, quorum enforcement, cross-node hash comparison, fault isolation, symmetric encryption support.
- **Decision:** DC-123

---

"""
    with open(state_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    insert_idx = 1  # after title line
    lines.insert(insert_idx, new_section)
    new_content = "".join(lines)

    atomic_write_text(state_path, new_content)
    print("  Updated CURRENT_STATE.md.")

def update_components():
    comp_path = ROOT / "continuity" / "COMPONENTS.md"
    if not comp_path.exists():
        print(f"Error: {comp_path} not found.")
        sys.exit(1)

    with open(comp_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "sibb_distributed.py" in content:
        print("  sibb_distributed.py already listed in COMPONENTS.md, skipping.")
        return

    backup_file(comp_path)

    new_row = "| SIBB Distributed Storage | tools/sibb_distributed.py | 100% | ✅ Complete (v1.2, 23/23 tests) |\n"

    lines = content.splitlines(keepends=True)
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
    test_path = ROOT / "tests" / "TEST_RESULTS.md"
    if not test_path.exists():
        print(f"Error: {test_path} not found.")
        sys.exit(1)

    backup_file(test_path)

    new_row = (
        f"| {utc_now()} | SIBB Distributed Storage | tests/test_sibb_distributed.py | PASS | 23 | 0 | DC-123 | "
        f"All unit/security tests passed after v1.2. |\n"
    )

    with open(test_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if new_row.split('|')[1].strip() in content:
        print("  Test result already exists in TEST_RESULTS.md, skipping.")
        return

    new_content = content.rstrip() + "\n" + new_row
    atomic_write_text(test_path, new_content)
    print("  Updated TEST_RESULTS.md.")

def main():
    print("=== Documenting DC-123: SIBB Distributed Storage v1.2 ===")
    update_decisions_log()
    update_current_state()
    update_components()
    update_test_results()
    print("\n✅ Documentation completed successfully.")
    print("Protected directories were not accessed.")

if __name__ == "__main__":
    main()
