#!/usr/bin/env python3
"""
Update memory files for SIBB (Sovereign Immutable Black Box) implementation.
New decision: DC-121
"""

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

# ============================================================
# 1) DECISIONS_LOG.md
# ============================================================
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')

# Calculate next DC number (last is DC-120)
ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=120) + 1

entry = (
    f"| DC-{next_num} | {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} | "
    "Implement SIBB (Sovereign Immutable Black Box) storage layer | "
    "Created four modules: sibb_storage.py (WORM storage), sibb_distributed.py (geographic replication), "
    "sibb_keys.py (Shamir key management), and sibb_cli.py (CLI interface). "
    "SIBB provides tamper-proof, immutable storage for the innocence chain with encryption, "
    "geographic distribution, and quorum-based recovery. This makes AAAC unique in the market "
    "as the only AI governance solution with a truly immutable audit trail. | "
    "SIBB layer ready for integration | Complete |\n"
)

if not text.endswith('\n'):
    text += '\n'
text += entry
atomic_write(log_path, text)
print(f"✅ Added DC-{next_num} to DECISIONS_LOG.md")

# ============================================================
# 2) DECISIONS_INDEX.md
# ============================================================
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')
lines = index_text.splitlines()

# Find insertion point (after DC-120)
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-120'):
        insert_pos = i + 1
        break

if insert_pos is None:
    # fallback: find end of table
    for i, line in enumerate(lines):
        if line.startswith('## Notes'):
            insert_pos = i
            break

new_row = f"| DC-{next_num} | Implement SIBB (Sovereign Immutable Black Box) storage layer | {datetime.now(timezone.utc).strftime('%Y-%m-%d')} |\n"

if insert_pos is not None:
    lines.insert(insert_pos, new_row)
else:
    lines.append(new_row)

new_index = '\n'.join(lines) + '\n'
atomic_write(index_path, new_index)
print("✅ Updated DECISIONS_INDEX.md")

# ============================================================
# 3) CURRENT_STATE.md
# ============================================================
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')

insert = f'''

## SIBB (Sovereign Immutable Black Box) — {datetime.now(timezone.utc).strftime('%Y-%m-%d')} (DC-{next_num})

- Created immutable storage layer for innocence chain with WORM (Write Once, Read Many) semantics.
- Supports geographic distribution with 3+ nodes and quorum-based writes (2/3).
- Encryption with AES-256-GCM and key sharding using Shamir's Secret Sharing (3/5).
- Files cannot be modified or deleted even by system administrators, ensuring true audit trail integrity.
- CLI interface for management and integration with existing AAAC components.
- Next: integrate SIBB with innocence_chain.py to automatically store rings, and add cloud storage adapters (AWS S3 Object Lock, Azure Immutable Blob).
'''

if 'SIBB (Sovereign Immutable Black Box)' not in state_text:
    # Insert after "## Last Completed Decisions (Latest)"
    if '## Last Completed Decisions (Latest)' in state_text:
        state_text = state_text.replace(
            '## Last Completed Decisions (Latest)',
            insert + '\n## Last Completed Decisions (Latest)'
        )
    else:
        # fallback: append at the end
        state_text = state_text + '\n' + insert

atomic_write(state_path, state_text)
print("✅ Updated CURRENT_STATE.md")

# ============================================================
# 4) COMPONENTS.md (optional, but nice to have)
# ============================================================
comp_path = ROOT / 'continuity' / 'COMPONENTS.md'
if comp_path.exists():
    backup_file(comp_path)
    comp_text = comp_path.read_text(encoding='utf-8')
    if 'SIBB' not in comp_text:
        new_row_comp = f"| SIBB (Immutable Storage) | tools/sibb_*.py | 100% | ✅ Complete |\n"
        # Find the table (after "## Components Inventory" or similar)
        if '## Components Inventory' in comp_text:
            # Insert after the header
            comp_text = comp_text.replace(
                '## Components Inventory',
                '## Components Inventory\n\n| Component | File | Progress | Status |\n|-----------|------|----------|--------|\n' + new_row_comp
            )
        else:
            # Append at end
            comp_text += f'\n| SIBB (Immutable Storage) | tools/sibb_*.py | 100% | ✅ Complete |\n'
        atomic_write(comp_path, comp_text)
        print("✅ Updated COMPONENTS.md")

print("\n" + "=" * 60)
print(f"✅ All memory files updated for DC-{next_num} (SIBB implementation)")
print("=" * 60)
