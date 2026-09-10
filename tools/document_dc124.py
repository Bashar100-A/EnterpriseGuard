#!/usr/bin/env python3
"""
Documentation script for DC-124: Acceptance of SIBB Key Management v1.0.3.

This script:
- Updates tools/DECISIONS_LOG.md with DC-124 entry.
- Updates continuity/CURRENT_STATE.md with current status.
- Updates continuity/COMPONENTS.md with SIBB Key Management component entry.
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
        f"| DC-124 | {utc_now()} | Acceptance of SIBB Key Management v1.0.3 | "
        f"Implemented Shamir secret sharing with AES-GCM encryption, HMAC integrity, access control, "
        f"lockout mechanism, and secure file handling. All 29 unit tests passed. | "
        f"29/29 tests passed, protected dirs untouched. | Complete |\n"
    )

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "DC-124" in content:
        print("  DC-124 already exists in DECISIONS_LOG.md, skipping.")
        return

    if "| DC-123 |" in content:
        lines = content.splitlines(keepends=True)
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("| DC-123 |"):
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
    print("  Updated DECISIONS_LOG.md with DC-124.")

def update_current_state():
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        print(f"Error: {state_path} not found.")
        sys.exit(1)

    backup_file(state_path)

    new_section = f"""
## Latest Update — {utc_now()}

- **Component:** SIBB Key Management (`tools/sibb_keys.py`)
- **Version:** 1.0.3
- **Status:** ✅ Complete and tested
- **Tests:** 29/29 passed (unit and security tests)
- **Security:** AES-GCM encryption, HMAC integrity, Shamir secret sharing, access control, lockout mechanism, secure file permissions.
- **Decision:** DC-124

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

    if "sibb_keys.py" in content:
        print("  sibb_keys.py already listed in COMPONENTS.md, skipping.")
        return

    backup_file(comp_path)

    new_row = "| SIBB Key Management | tools/sibb_keys.py | 100% | ✅ Complete (v1.0.3, 29/29 tests) |\n"

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
        f"| {utc_now()} | SIBB Key Management | tests/test_sibb_keys.py | PASS | 29 | 0 | DC-124 | "
        f"All unit/security tests passed after v1.0.3. |\n"
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
    print("=== Documenting DC-124: SIBB Key Management v1.0.3 ===")
    update_decisions_log()
    update_current_state()
    update_components()
    update_test_results()
    print("\n✅ Documentation completed successfully.")
    print("Protected directories were not accessed.")

if __name__ == "__main__":
    main()
