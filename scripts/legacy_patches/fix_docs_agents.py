import re
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

# 1) DECISIONS_LOG
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
if log_path.exists():
    backup_file(log_path)
    text = log_path.read_text(encoding='utf-8')
    ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
    next_num = max((int(n) for _, n in ids), default=63) + 1
    entry = (
        f"| DC-{next_num} | 2026-09-06T15:35:00Z | Fixed /agents endpoint to read agents from ring_storage.jsonl | "
        "Updated sovereign_http_server.py load_agents to extract unique agent IDs from ring_storage.jsonl, falling back to relational memory. "
        "Fixed mismatch between agent_id and actor_id; added limit cap and reverse read for /events. | "
        "Verified: GET /agents returns agent-123 from ring_storage | Complete |\n"
    )
    if not text.endswith('\n'):
        text += '\n'
    text += entry
    atomic_write(log_path, text)
    print(f"Added DC-{next_num} to DECISIONS_LOG.md")

# 2) CURRENT_STATE
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
if state_path.exists():
    backup_file(state_path)
    text = state_path.read_text(encoding='utf-8')
    if 'HTTP server /agents endpoint now reads from ring_storage' not in text:
        update = '''
## HTTP Server Update — 2026-09-06

- `GET /agents` fixed to read unique agent IDs from `tools/ring_storage.jsonl`, fallback to relational memory.
- `/events` now supports `limit` cap (max 500) and reads last 2000 lines for performance.
- `/agents` tested: returns `agent-123` from `ring_storage`.
- Next: regenerate baselines, then pause technical work pending customer discovery.
'''
        text = text.replace('---\n\n## Last Completed Decisions (Latest)', update + '\n---\n\n## Last Completed Decisions (Latest)')
    atomic_write(state_path, text)
    print("Updated CURRENT_STATE.md")
