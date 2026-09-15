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

index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
text = index_path.read_text(encoding='utf-8')

# إضافة الإدخالات الجديدة قبل السطر الذي يبدأ بـ "---" في نهاية الجدول (سنضيفها بعد آخر صف)
# نبحث عن آخر صف في الجدول (DC-077) ونضيف بعده
rows = [
    "| DC-78 | Adoption of AAAC as Proof Layer and Launch of Customer Discovery Plan | 2026-09-06 |\n",
    "| DC-79 | AAAC MVP Connector and Chain Integration (Working Prototype) | 2026-09-06 |\n",
    "| DC-80 | Fixed /agents endpoint to read agents from ring_storage.jsonl | 2026-09-06 |\n",
    "| DC-81 | Phase 2 Improvements: duplicate avoidance, RFC3161 field, dashboard | 2026-09-06 |\n",
]
# إيجاد نهاية الجدول (آخر سطر يبدأ بـ | DC-)
lines = text.splitlines()
insert_idx = None
for i, line in enumerate(lines):
    if line.startswith('| DC-077'):
        insert_idx = i + 1
        break
if insert_idx is None:
    # fallback: append before Notes
    insert_idx = next((i for i,l in enumerate(lines) if l.startswith('## Notes')), len(lines))
for row in reversed(rows):
    lines.insert(insert_idx, row)
new_text = '\n'.join(lines) + '\n'
atomic_write(index_path, new_text)
print("Updated DECISIONS_INDEX.md")
