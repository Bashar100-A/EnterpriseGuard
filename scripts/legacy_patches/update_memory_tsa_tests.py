import re, sys, shutil, tempfile, os
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

# 1) إضافة قرارين إلى DECISIONS_LOG.md
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')
ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1

entry1 = f"| DC-{next_num} | 2026-09-07T07:35:00Z | Add TSA failover pool | Modified get_rfc3161_timestamp to try multiple TSA providers from AAAC_TSA_URLS (default: Certum, FreeTSA, DFN). Returns (token, provider). generate_ring now records actual provider. Existing chain still VERIFIED_OK. | TSA failover tested indirectly | Complete |\n"
next_num += 1
entry2 = f"| DC-{next_num} | 2026-09-07T07:40:00Z | Add signing backend unit tests | Created tools/test_signing_backend.py with mock and local mode tests. All tests passed using PYTHONPATH=. python3 tools/test_signing_backend.py. | Mock and local signing verified | Complete |\n"

if not text.endswith('\n'):
    text += '\n'
text += entry1 + entry2
atomic_write(log_path, text)
print(f"Added DC-{next_num-1} and DC-{next_num}")

# 2) تحديث DECISIONS_INDEX.md
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')
lines = index_text.splitlines()
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-'):
        insert_pos = i + 1
if insert_pos is not None:
    lines.insert(insert_pos, f"| DC-{next_num-1} | Add TSA failover pool | 2026-09-07 |")
    lines.insert(insert_pos+1, f"| DC-{next_num} | Add signing backend unit tests | 2026-09-07 |")
    new_index = '\n'.join(lines) + '\n'
else:
    new_index = index_text
atomic_write(index_path, new_index)
print("Updated DECISIONS_INDEX.md")

# 3) تحديث CURRENT_STATE.md
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')
insert = f'''

## TSA Failover & Signing Tests — 2026-09-07 (DC-{next_num-1}, DC-{next_num})

- Added TSA failover pool with multiple providers (Certum, FreeTSA, DFN).
- Created signing backend unit tests; all passed.
- Chain remains VERIFIED_OK.
- Next: consider Docker Compose, market validation, or Bandit cleanup.
'''
if 'TSA Failover & Signing Tests' not in state_text:
    state_text = state_text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, state_text)
print("Updated CURRENT_STATE.md")

# 4) إعادة توليد خط الأساس بعد التعديلات
print("Regenerating baselines...")
from tools import integrity_monitor
import subprocess
subprocess.run(["python3", "tools/integrity_monitor.py", "--generate-baseline"], check=True)
subprocess.run(["python3", "tools/integrity_monitor.py", "--check"], check=True)
print("Baselines updated.")
