#!/usr/bin/env python3
"""
Documentation script for DC-128: Kernel protection strategy decision.

This script:
- Adds DC-128 to DECISIONS_LOG.md
- Updates CURRENT_STATE.md with kernel protection summary
- Does NOT modify COMPONENTS.md or TEST_RESULTS.md unless necessary.
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

# Optional audit fallback
try:
    from tools.audit_chain import append_activity
except ImportError:
    def append_activity(event_type, details):
        fallback_path = ROOT / "tools" / "audit_fallback.jsonl"
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({"event": event_type, "details": details,
                             "timestamp": datetime.now(timezone.utc).isoformat()}) + "\n"
        with open(fallback_path, 'a') as f:
            f.write(record)

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def backup_file(path):
    if path.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = path.with_name(f"{path.name}.bak_{timestamp}")
        shutil.copy2(path, backup, follow_symlinks=False)
        logger.info(f"Backup created: {backup.name}")

def atomic_write_text(path, content):
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

def update_decisions_log():
    log_path = ROOT / "tools" / "DECISIONS_LOG.md"
    if not log_path.exists():
        logger.error("DECISIONS_LOG.md not found")
        sys.exit(1)
    backup_file(log_path)
    entry = (
        f"| DC-128 | {utc_now()} | Kernel protection strategy decision | "
        f"Adopted chattr +i as the primary kernel-level WORM protection. "
        f"Documented that root can bypass via CAP_LINUX_IMMUTABLE, and that full protection requires SELinux or eBPF in a dedicated environment. "
        f"AppArmor and eBPF attempts deferred. | "
        f"Decision documented, protected dirs untouched. | Complete |\n"
    )
    with open(log_path, 'r') as f:
        content = f.read()
    if "DC-128" in content:
        logger.warning("DC-128 already exists. Skipping.")
        return
    if "| DC-127 |" in content:
        lines = content.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith("| DC-127 |"):
                lines.insert(i+1, entry)
                break
        new_content = "".join(lines)
    else:
        new_content = content.rstrip() + "\n" + entry
    atomic_write_text(log_path, new_content)
    logger.info("Updated DECISIONS_LOG.md with DC-128.")

def update_current_state():
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        logger.error("CURRENT_STATE.md not found")
        sys.exit(1)
    backup_file(state_path)
    new_section = (
        f"\n## Kernel Protection Strategy — {utc_now()}\n\n"
        f"- **Decision:** DC-128\n"
        f"- **Primary mechanism:** `chattr +i` on SIBB storage paths.\n"
        f"- **Limitation:** root with CAP_LINUX_IMMUTABLE can remove immutability.\n"
        f"- **Full root-proof protection:** requires SELinux or eBPF in a dedicated environment.\n"
        f"- **Next step:** test kernel_lockdown in a VM, then consider production rollout.\n\n"
    )
    with open(state_path, 'r') as f:
        content = f.read()
    lines = content.splitlines(keepends=True)
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_idx = i+1
            break
    lines.insert(insert_idx, new_section)
    new_content = "".join(lines)
    atomic_write_text(state_path, new_content)
    logger.info("Updated CURRENT_STATE.md.")

def main():
    logger.info("=== Documenting DC-128: Kernel protection strategy ===")
    update_decisions_log()
    update_current_state()
    append_activity("documentation", {"decision": "DC-128", "summary": "chattr +i adopted as primary"})
    logger.info("✅ Documentation completed successfully.")

if __name__ == "__main__":
    main()
