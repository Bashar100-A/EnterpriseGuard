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

# استيراد html escape
if 'from html import escape' not in text:
    text = text.replace('import http.server', 'import http.server\nfrom html import escape', 1)

# إضافة دالة serve_dashboard داخل الفئة
dashboard_func = '''

    def serve_dashboard(self):
        events_html = "<h3>Events</h3><ul>"
        events = load_events('/events?limit=10').get('events', [])
        for ev in events:
            events_html += f"<li>{escape(str(ev.get('timestamp', '')))} - {escape(str(ev.get('command', '')))} - {escape(str(ev.get('agent_id', '')))}</li>"
        events_html += "</ul>"
        agents_html = "<h3>Agents</h3><ul>"
        agents = load_agents().get('agents', [])
        for ag in agents:
            agents_html += f"<li>{escape(str(ag))}</li>"
        agents_html += "</ul>"
        html = f"""<!DOCTYPE html>
<html>
<head><title>AAAC Dashboard</title><meta charset="utf-8"></head>
<body>
<h1>AAAC Proof Layer</h1>
{agents_html}
{events_html}
<p><a href="/health">Health</a> | <a href="/verify-chain">Verify Chain</a></p>
</body>
</html>"""
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
'''
marker = '    def log_message(self, format: str, *args: object) -> None:\n        return\n'
if marker not in text:
    print('Marker not found')
    sys.exit(1)
text = text.replace(marker, marker + '\n' + dashboard_func, 1)

# إضافة المسار في do_GET
old_get = '''        if self.path == "/health":
            self._send_json(200, {"status": "ok"})'''
new_get = '''        if self.path == "/dashboard":
            self.serve_dashboard()
            return
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})'''
if old_get not in text:
    print('Old GET block not found')
    sys.exit(1)
text = text.replace(old_get, new_get, 1)

atomic_write(file, text)
print('Successfully added dashboard endpoint')
