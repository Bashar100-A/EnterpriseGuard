#!/usr/bin/env python3
"""
Documentation script for DC-127: Shift to chattr +i + SELinux/AppArmor instead of eBPF.

This script:
- Updates DECISIONS_LOG.md with DC-127 entry.
- Updates CURRENT_STATE.md with new protection strategy.
- Updates COMPONENTS.md if needed.
- Updates TEST_RESULTS.md if needed.
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
        f"| DC-127 | {utc_now()} | Shift to chattr +i and SELinux/AppArmor for kernel-level WORM protection | "
        f"After eBPF prototype encountered compatibility issues, adopted standard chattr +i with CAP_LINUX_IMMUTABLE restriction via SELinux/AppArmor. "
        f"eBPF development is deferred indefinitely. | "
        f"Decision made, protected dirs untouched. | Complete |\n"
    )
    with open(log_path, 'r') as f:
        content = f.read()
    if "DC-127" in content:
        logger.warning("DC-127 already exists. Skipping.")
        return
    # Insert after DC-126
    if "| DC-126 |" in content:
        lines = content.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith("| DC-126 |"):
                lines.insert(i+1, entry)
                break
        new_content = "".join(lines)
    else:
        new_content = content.rstrip() + "\n" + entry
    atomic_write_text(log_path, new_content)
    logger.info("Updated DECISIONS_LOG.md with DC-127.")

def update_current_state():
    state_path = ROOT / "continuity" / "CURRENT_STATE.md"
    if not state_path.exists():
        logger.error("CURRENT_STATE.md not found")
        sys.exit(1)
    backup_file(state_path)
    new_section = (
        f"\n## Protection Strategy Update — {utc_now()}\n\n"
        f"- **Decision:** DC-127\n"
        f"- **Kernel-level WORM:** Using `chattr +i` combined with SELinux/AppArmor to restrict `CAP_LINUX_IMMUTABLE`.\n"
        f"- **eBPF prototype status:** Deferred due to compatibility issues; all eBPF files kept under `tools/ebpf/` for future reference.\n"
        f"- **Immediate action:** Apply `chattr -R +i` to SIBB storage paths and configure mandatory access control.\n\n"
    )
    with open(state_path, 'r') as f:
        content = f.read()
    # Insert after first title
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
    logger.info("=== Documenting DC-127: Shift to chattr+i + SELinux/AppArmor ===")
    update_decisions_log()
    update_current_state()
    append_activity("documentation", {
        "decision": "DC-127",
        "summary": "chattr +i with SELinux/AppArmor protection"
    })
    logger.info("✅ Documentation completed successfully.")

if __name__ == "__main__":
    main()
