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

# 1. العثور على أحدث نسخة احتياطية
backups = sorted(ROOT.glob('tools/innocence_chain.py.bak_*'), key=os.path.getmtime, reverse=True)
if not backups:
    print("No backup files found")
    sys.exit(1)
backup_path = backups[0]
print(f"Using backup: {backup_path}")

# 2. قراءة النسخة الاحتياطية والبحث عن الدالة
backup_text = backup_path.read_text(encoding='utf-8')
pattern = r'def run_integrity_check\(\) -> str:.*?(?=\n\n\ndef |\n\n\Z)'
match = re.search(pattern, backup_text, flags=re.DOTALL)
if not match:
    print("Function run_integrity_check not found in backup")
    sys.exit(1)
function_code = match.group(0)
print("Extracted function:\n", function_code)

# 3. قراءة الملف الحالي
current_path = ROOT / 'tools' / 'innocence_chain.py'
backup_file(current_path)
current_text = current_path.read_text(encoding='utf-8')

# 4. التحقق من عدم وجود الدالة مسبقًا
if 'def run_integrity_check' in current_text:
    print("Function already exists in current file, aborting")
    sys.exit(1)

# 5. إدراج الدالة قبل def _get_integrity_status
insert_marker = 'def _get_integrity_status() -> str:'
if insert_marker not in current_text:
    print("Could not find insertion point (_get_integrity_status)")
    sys.exit(1)

current_text = current_text.replace(insert_marker, function_code + '\n\n' + insert_marker, 1)
atomic_write(current_path, current_text)
print("Successfully inserted run_integrity_check function")
