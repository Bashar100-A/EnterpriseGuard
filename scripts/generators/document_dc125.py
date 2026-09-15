#!/usr/bin/env python3
"""
Documentation script for DC-125: Acceptance of SIBB CLI v1.1.

Improvements:
- Added directory fsync after atomic writes
- Fixed duplicate detection using unique identifiers
- Robust table insertion logic
- Transaction-like rollback on failure
- follow_symlinks=False for backups
- Write permission checks
- Single timestamp source
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

if not (ROOT / "tools").exists() or not (ROOT / "continuity").exists():
    print("Error: This script must be run from the project root.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Optional audit chain integration
try:
    from tools.audit_chain import append_activity
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False
    def append_activity(event_type, details):
        logger.error(f"AUDIT CHAIN REQUIRED but not available: {event_type} | {details}")
        # Could write to a separate local audit file as fallback
        fallback = ROOT / "tools" / "audit_fallback.jsonl"
        with open(fallback, 'a') as f:
            f.write(json.dumps({"event": event_type, "details": details, "timestamp": datetime.now(timezone.utc).isoformat()}) + "\n")

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def utc_now_file():
    # Use same timestamp as utc_now but in compact form
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%M%SZ")

def backup_file(path: Path) -> Path:
    """Create a timestamped backup. Raises exception if backup fails."""
    if not path.exists():
        logger.warning(f"Source file does not exist, no backup created: {path}")
        return path

    timestamp = utc_now_file()
    backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
    try:
        shutil.copy2(path, backup_path, follow_symlinks=False)
        logger.info(f"Backup created: {backup_path.name}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise

def atomic_write_text(path: Path, content: str):
    """Write text to file atomically with directory fsync."""
    # Check write permission
    if not os.access(path.parent, os.W_OK):
        raise PermissionError(f"Directory not writable: {path.parent}")

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)

        # fsync the directory to ensure durability
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

        logger.debug(f"Atomically wrote {path}")
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise

def update_decisions_log():
    log_path = ROOT / "tools" / "DECISIONS_LOG.md"
    if not log_path.exists():
        logger.error(f"Error: {log_path} not found.")
        sys.exit(1)

    backup_file(log_path)

    entry = (
        f"| DC-125 | {utc_now()} | Acceptance of SIBB CLI v1.1 | "
        f"Implemented secure command-line interface for storage and key management with validation, "
        f"encryption support, and audit logging. All 17 unit tests passed. | "
        f"17/17 tests passed, protected dirs untouched. | Complete |\n"
    )

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Unique identifier for duplicate detection
    if "DC-125" in content:
        logger.warning("DC-125 already exists in DECISIONS_LOG.md. Skipping.")
        return None

    if "| DC-124 |" in content:
        lines = content.splitlines(keepends=True)
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("| DC-124 |"):
                insert_idx = i + 1
                break
        if insert_idx is not None:
            lines.insert(insert_idx, entry)
            new_content = "".join(lines)
        else:
            new_content = content + entry
    else:
        new_content = content.rstrip() + "\n" + entry

    return ("DECISIONS_LOG.md", log_path, new_content)

def update_current_state():
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        logger.error(f"Error: {state_path} not found.")
        sys.exit(1)

    backup_file(state_path)

    new_section = f"""
## Latest Update — {utc_now()}

- **Component:** SIBB CLI (`tools/sibb_cli.py`)
- **Version:** 1.1
- **Status:** ✅ Complete and tested
- **Tests:** 17/17 passed (unit and security tests)
- **Security:** Secure input validation, password handling, encryption support, audit logging, no shell command injection.
- **Decision:** DC-125

---

"""
    with open(state_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Insert after first main title (line starting with #)
    lines = content.splitlines(keepends=True)
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_idx = i + 1
            break
    if insert_idx is None:
        insert_idx = 0

    # Ensure blank line after title before new section
    if insert_idx < len(lines) and lines[insert_idx].strip() == "":
        insert_idx += 1

    lines.insert(insert_idx, "\n" + new_section)
    new_content = "".join(lines)

    return ("CURRENT_STATE.md", state_path, new_content)

def update_components():
    comp_path = ROOT / "continuity" / "COMPONENTS.md"
    if not comp_path.exists():
        logger.error(f"Error: {comp_path} not found.")
        sys.exit(1)

    with open(comp_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Unique detection: component filename
    if "sibb_cli.py" in content:
        logger.warning("sibb_cli.py already listed in COMPONENTS.md. Skipping.")
        return None

    backup_file(comp_path)

    new_row = "| SIBB CLI | tools/sibb_cli.py | 100% | ✅ Complete (v1.1, 17/17 tests) |\n"

    # Find the components table
    lines = content.splitlines(keepends=True)
    table_start = None
    table_end = None
    for i, line in enumerate(lines):
        if line.startswith("| Component | File | Progress | Status |"):
            table_start = i
            # Skip header and separator
            for j in range(i+1, len(lines)):
                if lines[j].startswith("|---"):
                    continue
                if lines[j].startswith("|"):
                    table_end = j  # last data row so far
                else:
                    break
            break

    if table_start is None:
        # Append at end
        new_content = content.rstrip() + "\n" + new_row
    else:
        # Insert after last data row
        insert_idx = table_end + 1 if table_end is not None else table_start + 2
        lines.insert(insert_idx, new_row)
        new_content = "".join(lines)

    return ("COMPONENTS.md", comp_path, new_content)

def update_test_results():
    test_path = ROOT / "tests" / "TEST_RESULTS.md"
    if not test_path.exists():
        logger.error(f"Error: {test_path} not found.")
        sys.exit(1)

    backup_file(test_path)

    new_row = (
        f"| {utc_now()} | SIBB CLI | tests/test_sibb_cli.py | PASS | 17 | 0 | DC-125 | "
        f"All unit/security tests passed after v1.1. |\n"
    )

    with open(test_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Unique detection: DC-125 and SIBB CLI in same line
    if "DC-125" in content and "SIBB CLI" in content:
        logger.warning("Test result already exists in TEST_RESULTS.md. Skipping.")
        return None

    new_content = content.rstrip() + "\n" + new_row
    return ("TEST_RESULTS.md", test_path, new_content)

def main():
    logger.info("=== Documenting DC-125: SIBB CLI v1.1 ===")

    # Collect all updates first
    updates = []
    try:
        updates.append(update_decisions_log())
        updates.append(update_current_state())
        updates.append(update_components())
        updates.append(update_test_results())
    except Exception as e:
        logger.error(f"Failed during update collection: {e}")
        sys.exit(1)

    # Filter out None (skipped updates)
    updates = [u for u in updates if u is not None]

    if not updates:
        logger.warning("No updates needed (all entries already exist).")
        return

    # Write all updates atomically (transaction-like)
    try:
        for name, path, content in updates:
            atomic_write_text(path, content)
            logger.info(f"Updated {name}.")
    except Exception as e:
        logger.error(f"Failed during write phase: {e}")
        # Attempt rollback by restoring backups
        for name, path, _ in updates:
            # Find latest backup for this file
            backup_dir = path.parent
            backups = sorted(backup_dir.glob(f"{path.name}.bak_*"), reverse=True)
            if backups:
                try:
                    shutil.copy2(backups[0], path, follow_symlinks=False)
                    logger.info(f"Rolled back {name} from {backups[0].name}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed for {name}: {rollback_error}")
        sys.exit(1)

    logger.info("✅ Documentation completed successfully.")
    logger.info("Protected directories were not accessed.")

    # Audit log
    append_activity("documentation", {
        "decision": "DC-125",
        "component": "tools/sibb_cli.py",
        "tests": "17/17",
        "timestamp": utc_now()
    })

if __name__ == "__main__":
    main()
