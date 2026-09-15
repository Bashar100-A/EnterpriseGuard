#!/usr/bin/env python3
"""Update memory files for DC-119: Key backup system using age."""

import re
import sys
import shutil
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True
ROOT = Path('.')

def backup_file(path):
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    b = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, b)
    return b

def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

# 1) DECISIONS_LOG.md
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')
ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=118) + 1

entry = f"| DC-{next_num} | {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} | Implement key backup system using age | Created tools/backup_keys.py for encrypting signing keys with age. Supports --backup, --restore, and --list. Keys are encrypted with age recipient from ~/.enterpriseguard/backup_key.txt and stored in backups/keys_encrypted/. | Key backup system ready | Complete |\n"
if not text.endswith('\n'):
    text += '\n'
text += entry
atomic_write(log_path, text)
print(f"Added DC-{next_num} to DECISIONS_LOG.md")

# 2) DECISIONS_INDEX.md
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')
lines = index_text.splitlines()
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-'):
        insert_pos = i + 1
if insert_pos is not None:
    lines.insert(insert_pos, f"| DC-{next_num} | Implement key backup system using age | {datetime.now(timezone.utc).strftime('%Y-%m-%d')} |")
    new_index = '\n'.join(lines) + '\n'
else:
    new_index = index_text
atomic_write(index_path, new_index)
print("Updated DECISIONS_INDEX.md")

# 3) CURRENT_STATE.md
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')
insert = f'''

## Key Backup System — {datetime.now(timezone.utc).strftime('%Y-%m-%d')} (DC-{next_num})

- Implemented `tools/backup_keys.py` for encrypting and backing up signing keys using `age`.
- Supports `--backup`, `--restore`, and `--list` commands.
- Keys are encrypted with the recipient in `~/.enterpriseguard/backup_key.txt` and saved to `backups/keys_encrypted/`.
- Next: Proceed with standalone open_verifier and ECDSA migration.
'''
if 'Key Backup System' not in state_text:
    state_text = state_text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, state_text)
print("Updated CURRENT_STATE.md")

# 4) Regenerate baselines
print("Regenerating baselines...")
import subprocess
subprocess.run(["python3", "tools/integrity_monitor.py", "--generate-baseline"], check=True)
subprocess.run(["python3", "tools/integrity_monitor.py", "--check"], check=True)
print("Baselines updated successfully.")
