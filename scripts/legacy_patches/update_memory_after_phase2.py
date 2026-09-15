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
    backup = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, backup)
    return backup

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

# ===== 1. DECISIONS_LOG.md: إضافة قرارات جديدة =====
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')

ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1

new_entries = []
# DC-82: Fix RFC3161 dynamic TSA
new_entries.append(
    f"| DC-{next_num} | 2026-09-06T20:30:00Z | Fix RFC3161 timestamp with dynamic TSA and tsa_provider | "
    "Updated get_rfc3161_timestamp to use openssl ts -query and send proper ASN.1 request to configured TSA (default http://time.certum.pl). "
    "Added tsa_provider field to each ring. Fixed missing run_integrity_check function caused by earlier edits. "
    "Verified chain VERIFIED_OK after regenerating baselines. | Timestamp token now real DER data | Complete |\n"
)
next_num += 1

# DC-83: Dashboard auth bypass for local testing
new_entries.append(
    f"| DC-{next_num} | 2026-09-06T20:35:00Z | Temporary dashboard auth bypass for local testing | "
    "Modified sovereign_http_server.py to allow /dashboard without X-ADIE-Key for local development. "
    "This is temporary and must be reverted before any production or demo to external parties. "
    "Other endpoints remain protected. | Dashboard displays agents and events | Complete |\n"
)
next_num += 1

# DC-84: Open verifier
new_entries.append(
    f"| DC-{next_num} | 2026-09-06T20:40:00Z | Create open-source verifier (MIT) | "
    "Created tools/open_verifier.py under MIT license. It imports verification functions from innocence_chain to ensure consistency. "
    "Initially had hex conversion issue, resolved by importing original functions. Tested: VALID: chain is authentic. "
    "Aimed at investors and third-party auditors. | open_verifier.py works | Complete |\n"
)
next_num += 1

if not text.endswith('\n'):
    text += '\n'
text += ''.join(new_entries)
atomic_write(log_path, text)
print(f"Added decisions up to DC-{next_num-1}")

# ===== 2. DECISIONS_INDEX.md: إضافة الصفوف الجديدة =====
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')

# نضيف الصفوف بعد آخر صف موجود
rows_to_add = [
    "| DC-82 | Fix RFC3161 timestamp with dynamic TSA and tsa_provider | 2026-09-06 |\n",
    "| DC-83 | Temporary dashboard auth bypass for local testing | 2026-09-06 |\n",
    "| DC-84 | Create open-source verifier (MIT) | 2026-09-06 |\n",
]
# نبحث عن موضع الإدراج بعد آخر صف يبدأ بـ | DC-
lines = index_text.splitlines()
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-'):
        insert_pos = i + 1
if insert_pos is not None:
    for row in reversed(rows_to_add):
        lines.insert(insert_pos, row)
    new_text = '\n'.join(lines) + '\n'
else:
    # إذا لم نجد صفوف DC، نضيف قبل Notes
    insert_pos = next((i for i,l in enumerate(lines) if l.startswith('## Notes')), len(lines))
    for row in reversed(rows_to_add):
        lines.insert(insert_pos, row)
    new_text = '\n'.join(lines) + '\n'

atomic_write(index_path, new_text)
print("Updated DECISIONS_INDEX.md")

# ===== 3. CURRENT_STATE.md: إضافة تحديث المرحلة =====
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')

if '## Phase 2 Additions — RFC3161, Dashboard, Open Verifier' not in state_text:
    insert = '''
## Phase 2 Additions — RFC3161, Dashboard, Open Verifier

- RFC3161 timestamp fixed: now sends proper ASN.1 query to dynamic TSA (default http://time.certum.pl). `tsa_provider` recorded in each ring.
- `/dashboard` temporarily accessible without auth for local testing (to be reverted before production).
- Created `tools/open_verifier.py` (MIT) that imports verification functions from innocence_chain; tested `VALID: chain is authentic`.
- `integrity_monitor --check` remains `PASS`.
- Next: update memory files, then prepare EU AI Act compliance guide and legal use case.
'''
    state_text = state_text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, state_text)
print("Updated CURRENT_STATE.md")

# ===== 4. COMPONENTS.md: إضافة سطر =====
comp_path = ROOT / 'continuity' / 'COMPONENTS.md'
backup_file(comp_path)
comp_text = comp_path.read_text(encoding='utf-8')
if 'open_verifier.py' not in comp_text:
    comp_text = comp_text.replace(
        '> New in prototype:',
        '> New: open_verifier.py (MIT), rfc3161 dynamic TSA, dashboard.\n> New in prototype:'
    )
atomic_write(comp_path, comp_text)
print("Updated COMPONENTS.md")

# ===== 5. TESTING_NOTES_2026-09-06.md: إضافة =====
notes_path = ROOT / 'docs' / 'TESTING_NOTES_2026-09-06.md'
backup_file(notes_path)
notes_text = notes_path.read_text(encoding='utf-8')
addition = '''

## Phase 2 Later Fixes (2026-09-06 evening)
- RFC3161 timestamp: fixed, now returns valid DER token from Certum.
- Dashboard: accessible via /dashboard without auth (temporary).
- Open verifier: created and tested `VALID: chain is authentic`.
- Integrity check: PASS.
'''
notes_text += addition
atomic_write(notes_path, notes_text)
print("Updated TESTING_NOTES")
