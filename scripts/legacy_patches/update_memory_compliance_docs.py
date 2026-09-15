import re
import sys
import shutil
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True
ROOT = Path('.')

def backup_file(path: Path):
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    b = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, b)
    return b

def atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fh:
            fh.write(content)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise

# ===== 1. إضافة قرار جديد DC-85 =====
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')

ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1

entry = f"| DC-{next_num} | 2026-09-06T20:45:00Z | Create EU AI Act compliance guide and legal use case | Created docs/AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md and docs/AAAC_LEGAL_USE_CASE.md. Guide maps AAAC capabilities to Articles 12 and 14, with gap analysis and BYO-TSA recommendation. Use case describes credit decision scenario. Documents marked as draft, not legal advice. | Docs created and reviewed internally | Complete |\n"
if not text.endswith('\n'):
    text += '\n'
text += entry
atomic_write(log_path, text)
print(f"Added DC-{next_num}")

# ===== 2. تحديث DECISIONS_INDEX.md =====
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')
# إدراج بعد آخر صف DC
lines = index_text.splitlines()
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-'):
        insert_pos = i + 1
if insert_pos is not None:
    lines.insert(insert_pos, f"| DC-{next_num} | Create EU AI Act compliance guide and legal use case | 2026-09-06 |")
    new_text = '\n'.join(lines) + '\n'
else:
    new_text = index_text  # fallback
atomic_write(index_path, new_text)
print("Updated DECISIONS_INDEX.md")

# ===== 3. تحديث CURRENT_STATE.md =====
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')
insert = '''

## Compliance Documentation — 2026-09-06

- Created `docs/AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md` mapping AAAC to EU AI Act Articles 12 & 14.
- Created `docs/AAAC_LEGAL_USE_CASE.md` with credit decision scenario.
- Both documents are drafts; legal review recommended before external use.
- Next: await customer discovery results (until 2026-09-27) before Go/No-Go decision.
'''
if 'Compliance Documentation — 2026-09-06' not in state_text:
    state_text = state_text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, state_text)
print("Updated CURRENT_STATE.md")

# ===== 4. تحديث TESTING_NOTES =====
notes_path = ROOT / 'docs' / 'TESTING_NOTES_2026-09-06.md'
backup_file(notes_path)
notes_text = notes_path.read_text(encoding='utf-8')
notes_text += "\n## Compliance Docs\n- Created AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md and AAAC_LEGAL_USE_CASE.md (draft).\n"
atomic_write(notes_path, notes_text)
print("Updated TESTING_NOTES")
