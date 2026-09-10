#!/usr/bin/env python3
"""
Documentation script for DC-126: Acceptance of SIBB-Innocence Integration v1.3.

This script:
- Updates tools/DECISIONS_LOG.md with DC-126 entry.
- Updates continuity/CURRENT_STATE.md with current status.
- Updates continuity/COMPONENTS.md with integration component entry.
- Updates tests/TEST_RESULTS.md with the latest test results.

All modifications follow project rules:
- Timestamped backup before modification.
- Atomic writes using tempfile.mkstemp and os.replace.
- Protected directories (adie/, intelligence/) are never accessed.
- Prevents duplicate entries.
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

if not (ROOT / "tools").exists() or not (ROOT / "continuity").exists():
    print("Error: This script must be run from the project root.")
    sys.exit(1)

# Configure logging
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

def backup_file(path: Path) -> Path:
    """Create a timestamped backup. Raises exception if backup fails."""
    timestamp = utc_now_file()
    backup_path = path.with_name(f"{path.name}.bak_{timestamp}")
    if path.exists():
        try:
            shutil.copy2(path, backup_path, follow_symlinks=False)
            logger.info(f"Backup created: {backup_path.name}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    else:
        logger.warning(f"Source file does not exist, no backup created: {path}")
        return backup_path

def atomic_write_text(path: Path, content: str):
    """Write text to file atomically with directory fsync."""
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)

        # fsync directory
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
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
        f"| DC-126 | {utc_now()} | Acceptance of SIBB-Innocence Integration v1.3 | "
        f"Implemented integration layer storing innocence chain rings in SIBB with chain continuity enforcement, "
        f"signature verification, encryption support, and audit logging. All 15 unit tests passed. | "
        f"15/15 tests passed, protected dirs untouched. | Complete |\n"
    )

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if "DC-126" in content:
        logger.warning("DC-126 already exists in DECISIONS_LOG.md. Skipping.")
        return None

    # Insert after DC-125
    if "| DC-125 |" in content:
        lines = content.splitlines(keepends=True)
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("| DC-125 |"):
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

- **Component:** SIBB-Innocence Integration (`tools/sibb_innocence_integration.py`)
- **Version:** 1.3
- **Status:** ✅ Complete and tested
- **Tests:** 15/15 passed (unit and security tests)
- **Security:** Chain continuity enforcement, signature verification, encryption support, WORM integration, audit logging.
- **Decision:** DC-126

---

"""
    with open(state_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Unique detection
    if "SIBB-Innocence Integration (`tools/sibb_innocence_integration.py`)" in content:
        logger.warning("SIBB-Innocence Integration section already exists in CURRENT_STATE.md. Skipping.")
        return None

    # Insert after first main title
    lines = content.splitlines(keepends=True)
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_idx = i + 1
            break
    if insert_idx is None:
        insert_idx = 0

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

    # Unique detection
    if "sibb_innocence_integration.py" in content:
        logger.warning("sibb_innocence_integration.py already listed in COMPONENTS.md. Skipping.")
        return None

    backup_file(comp_path)

    new_row = "| SIBB-Innocence Integration | tools/sibb_innocence_integration.py | 100% | ✅ Complete (v1.3, 15/15 tests) |\n"

    # Find components table
    lines = content.splitlines(keepends=True)
    table_start = None
    table_end = None
    for i, line in enumerate(lines):
        if line.startswith("| Component | File | Progress | Status |"):
            table_start = i
            for j in range(i+1, len(lines)):
                if lines[j].startswith("|---"):
                    continue
                if lines[j].startswith("|"):
                    table_end = j
                else:
                    break
            break

    if table_start is None:
        new_content = content.rstrip() + "\n" + new_row
    else:
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
        f"| {utc_now()} | SIBB-Innocence Integration | tests/test_sibb_innocence_integration.py | PASS | 15 | 0 | DC-126 | "
        f"All unit/security tests passed after v1.3. |\n"
    )

    with open(test_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Unique detection
    if "DC-126" in content and "SIBB-Innocence Integration" in content:
        logger.warning("Test result already exists in TEST_RESULTS.md. Skipping.")
        return None

    new_content = content.rstrip() + "\n" + new_row
    return ("TEST_RESULTS.md", test_path, new_content)

def main():
    logger.info("=== Documenting DC-126: SIBB-Innocence Integration v1.3 ===")

    # Collect updates
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

    # Write all updates atomically
    try:
        for name, path, content in updates:
            atomic_write_text(path, content)
            logger.info(f"Updated {name}.")
    except Exception as e:
        logger.error(f"Failed during write phase: {e}")
        # Attempt rollback
        for name, path, _ in updates:
            backups = sorted(path.parent.glob(f"{path.name}.bak_*"), reverse=True)
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
        "decision": "DC-126",
        "component": "tools/sibb_innocence_integration.py",
        "tests": "15/15",
        "timestamp": utc_now()
    })

if __name__ == "__main__":
    main()
