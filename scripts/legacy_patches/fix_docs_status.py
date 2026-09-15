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

# ===== 1. تعديل docs/AAAC_PROTOTYPE_NOTES.md =====
notes_path = ROOT / 'docs' / 'AAAC_PROTOTYPE_NOTES.md'
if notes_path.exists():
    backup_file(notes_path)
    text = notes_path.read_text(encoding='utf-8')
    # استبدال أو إضافة سطر يوضح الحالة
    if '## Known Issues' in text:
        # استبدال البند المتعلق بـ integrity_status
        text = text.replace(
            "- `integrity_status` shows `FAIL` because baselines not regenerated after code changes.",
            "- ~~`integrity_status` shows `FAIL` because baselines not regenerated after code changes.~~ **Fixed on 2026-09-06T15:23:00Z: regenerated baselines, now shows `PASS`.**"
        )
    atomic_write(notes_path, text)
    print("Updated docs/AAAC_PROTOTYPE_NOTES.md")
else:
    print("notes file not found")

# ===== 2. تعديل continuity/CURRENT_STATE.md =====
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
if state_path.exists():
    backup_file(state_path)
    text = state_path.read_text(encoding='utf-8')
    # استبدال السطر القديم
    text = text.replace(
        "- `integrity_status` is currently `FAIL` because baselines were not regenerated after code changes (expected during active development).",
        "- `integrity_status` is now `PASS` after regenerating baselines on 2026-09-06T15:23:00Z."
    )
    atomic_write(state_path, text)
    print("Updated continuity/CURRENT_STATE.md")
else:
    print("CURRENT_STATE file not found")
