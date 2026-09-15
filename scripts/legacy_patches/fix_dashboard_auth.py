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

# البحث عن بداية do_GET
old_block = '''    def do_GET(self) -> None:
        if not self._authenticated():
            return

        if self.path == "/dashboard":
            self.serve_dashboard()
            return
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})'''

new_block = '''    def do_GET(self) -> None:
        # Allow /dashboard without auth for local testing only
        if self.path == "/dashboard":
            self.serve_dashboard()
            return

        if not self._authenticated():
            return

        if self.path == "/health":
            self._send_json(200, {"status": "ok"})'''

if old_block not in text:
    print("Old GET block not found, trying alternative pattern")
    # alternative: just move dashboard before auth by string replace
    auth_line = '        if not self._authenticated():\n            return\n'
    dash_line = '        if self.path == "/dashboard":\n            self.serve_dashboard()\n            return\n'
    if auth_line in text and dash_line in text:
        # remove dash_line from current location and insert before auth_line
        text = text.replace(dash_line, '', 1)
        insert_pos = text.find('    def do_GET(self) -> None:\n') + len('    def do_GET(self) -> None:\n')
        text = text[:insert_pos] + '\n        if self.path == "/dashboard":\n            self.serve_dashboard()\n            return\n' + text[insert_pos:]
        atomic_write(file, text)
        print("Successfully moved dashboard before auth")
    else:
        print("Could not find required patterns")
        sys.exit(1)
else:
    text = text.replace(old_block, new_block, 1)
    atomic_write(file, text)
    print("Successfully updated dashboard auth")
