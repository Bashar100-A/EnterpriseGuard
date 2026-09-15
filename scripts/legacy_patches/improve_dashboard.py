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

file = ROOT / 'tools' / 'sovereign_http_server.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# نبحث عن دالة serve_dashboard الحالية ونستبدلها
pattern = r'    def serve_dashboard\(self\):.*?(?=\n    def |\n\Z)'
new_method = '''    def serve_dashboard(self):
        """Render a simple dashboard with chain summary, agents, and events."""
        chain_data = load_json(INNOCENCE_CHAIN_PATH, None)
        rings = chain_data.get("rings", []) if isinstance(chain_data, dict) else []
        chain_id = chain_data.get("chain_id") or (rings[0].get("chain_id") if rings else "unknown")
        ring_count = len(rings)
        last_ring = rings[-1] if rings else {}
        integrity_status = last_ring.get("integrity_status", "UNKNOWN")
        tsa_provider = last_ring.get("tsa_provider", "")
        tsa_verified = last_ring.get("tsa_verified", False)
        verification_result, verification_reason = verify_chain()

        agents = load_agents().get("agents", [])
        events = load_events('/events?limit=10').get("events", [])

        # بناء أجزاء HTML
        agents_html = "".join(f"<li>{escape(str(ag))}</li>" for ag in agents) if agents else "<li>No agents registered</li>"
        events_html = "".join(
            f"<li>{escape(str(ev.get('timestamp', '')))} - {escape(str(ev.get('command', '')))} - {escape(str(ev.get('agent_id', '')))}</li>"
            for ev in events
        ) if events else "<li>No events</li>"

        html = f"""<!DOCTYPE html>
<html>
<head>
<title>AAAC Dashboard</title>
<meta charset="utf-8">
<style>
body {{ font-family: sans-serif; margin: 2rem; background: #f9f9f9; color: #222; }}
h1 {{ border-bottom: 2px solid #444; padding-bottom: 0.5rem; }}
.card {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
.metric {{ display: inline-block; margin-right: 2rem; font-size: 1.2rem; }}
.ok {{ color: green; font-weight: bold; }}
.bad {{ color: red; font-weight: bold; }}
ul {{ list-style: none; padding-left: 0; }}
li {{ margin: 0.3rem 0; }}
</style>
</head>
<body>
<h1>AAAC Proof Layer</h1>
<div class="card">
  <span class="metric">Rings: <strong>{ring_count}</strong></span>
  <span class="metric">Chain ID: <strong>{escape(str(chain_id))}</strong></span>
  <span class="metric">Integrity: <strong class="{('ok' if integrity_status == 'PASS' else 'bad')}">{integrity_status}</strong></span>
  <span class="metric">Verification: <strong class="{('ok' if verification_result else 'bad')}">{verification_reason}</strong></span>
</div>
<div class="card">
  <span class="metric">TSA Provider: <strong>{escape(str(tsa_provider))}</strong></span>
  <span class="metric">TSA Verified: <strong class="{('ok' if tsa_verified else 'bad')}">{tsa_verified}</strong></span>
</div>
<div class="card">
  <h3>Agents</h3>
  <ul>{agents_html}</ul>
</div>
<div class="card">
  <h3>Recent Events</h3>
  <ul>{events_html}</ul>
</div>
<p><a href="/health">Health</a> | <a href="/verify-chain">Verify Chain</a> | <a href="/compliance-report">Compliance Report</a></p>
</body>
</html>"""
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
'''

if re.search(pattern, text, flags=re.DOTALL):
    text = re.sub(pattern, new_method, text, count=1, flags=re.DOTALL)
    print("Successfully replaced serve_dashboard")
else:
    print("serve_dashboard not found, trying fallback")
    # fallback: search for simple marker and add new method before it
    marker = '    def serve_compliance_report(self):'
    if marker in text:
        text = text.replace(marker, new_method + '\n' + marker, 1)
        print("Fallback: inserted new serve_dashboard before serve_compliance_report")
    else:
        sys.exit(1)

atomic_write(file, text)
print("Dashboard improved successfully")
