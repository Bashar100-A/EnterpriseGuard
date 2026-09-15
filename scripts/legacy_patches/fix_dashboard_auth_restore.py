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

# البحث عن كتلة do_GET الحالية (التي بها استثناء /dashboard)
old_block = '''    def do_GET(self) -> None:
        # Allow /dashboard without auth for local testing only
        if self.path == "/dashboard":
            self.serve_dashboard()
            return

        if not self._authenticated():
            return

        if self.path == "/health":
            self._send_json(200, {"status": "ok"})'''

new_block = '''    def do_GET(self) -> None:
        if not self._authenticated():
            return

        if self.path == "/dashboard":
            self.serve_dashboard()
            return
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})'''

if old_block in text:
    text = text.replace(old_block, new_block, 1)
    atomic_write(file, text)
    print("Successfully restored authentication for /dashboard")
else:
    # fallback: البحث عن أي ذكر dashboard بدون تحقق وإصلاحه
    print("Old block not found, attempting alternative")
    sys.exit(1)
