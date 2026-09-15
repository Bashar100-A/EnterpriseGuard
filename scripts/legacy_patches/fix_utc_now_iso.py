import sys, shutil, tempfile, os
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

file = ROOT / 'tools' / 'sovereign_http_server.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# إضافة دالة utc_now_iso بعد دوال load_json أو قبل الفئة
func = '''

def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
'''

# إدراجها بعد استيراد datetime? الأسهل: قبل تعريف class SovereignRequestHandler
marker = 'class SovereignRequestHandler'
if marker in text:
    text = text.replace(marker, func + '\n' + marker, 1)
else:
    # fallback: add after sys.dont_write_bytecode
    marker2 = 'sys.dont_write_bytecode = True'
    text = text.replace(marker2, marker2 + '\n' + func, 1)

atomic_write(file, text)
print("Successfully added utc_now_iso function")
