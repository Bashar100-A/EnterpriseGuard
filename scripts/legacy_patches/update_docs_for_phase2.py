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

# ===== 1) DECISIONS_LOG.md =====
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')
# حساب الرقم التالي
ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1
entry = f"| DC-{next_num} | 2026-09-06T16:40:00Z | Phase 2 Improvements: duplicate avoidance, RFC3161 field, dashboard | Implemented duplicate trace_id skipping in aaac_connector.py, added rfc3161_token (currently error placeholder until proper TSA request is fixed), and added /dashboard HTML endpoint to sovereign_http_server.py. Baselines regenerated and chain verified. | Owner approved technical phase despite earlier freeze | Complete |\n"
if not text.endswith('\n'): text += '\n'
text += entry
atomic_write(log_path, text)
print(f"Added DC-{next_num} to DECISIONS_LOG.md")

# ===== 2) CURRENT_STATE.md =====
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
text = state_path.read_text(encoding='utf-8')
if '## Phase 2 Technical Updates — 2026-09-06' not in text:
    insert = '''
## Phase 2 Technical Updates — 2026-09-06

- Duplicate avoidance added to `tools/aaac_connector.py` (skips existing `trace_id`).
- `rfc3161_token` field added to `tools/innocence_chain.py` (token currently error placeholder; proper TSA request to be fixed later).
- `/dashboard` endpoint added to `tools/sovereign_http_server.py` (simple HTML view of agents and events).
- Baselines regenerated; `integrity_monitor --check` returns `PASS`.
- Chain regenerated and verified `VERIFIED_OK`.
- Next: test dashboard, then await customer discovery results.
'''
    text = text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, text)
print("Updated CURRENT_STATE.md")

# ===== 3) TESTING_NOTES =====
notes_path = ROOT / 'docs' / 'TESTING_NOTES_2026-09-06.md'
backup_file(notes_path)
notes = notes_path.read_text(encoding='utf-8')
addition = '''

## Phase 2: Duplicate avoidance, RFC3161, dashboard
- Duplicate trace_id test: PASS (all 8 existing traces skipped on second run).
- RFC3161 token: partial (field present but returns "Bad request format or system error").
- Dashboard: endpoint created; pending browser test.
- Integrity check: PASS.
- Chain verify: VERIFIED_OK.
'''
notes += addition
atomic_write(notes_path, notes)
print("Updated TESTING_NOTES_2026-09-06.md")
