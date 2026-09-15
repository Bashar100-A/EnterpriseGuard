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

server_path = ROOT / 'tools' / 'sovereign_http_server.py'
if not server_path.exists():
    print("Server file not found")
    sys.exit(1)

backup_file(server_path)
text = server_path.read_text(encoding='utf-8')

# تعريف الدالة الجديدة
new_func = '''def load_agents() -> dict:
    """Return unique agent IDs from ring_storage.jsonl, falling back to relational memory if empty."""
    agents = set()
    if RING_STORAGE_PATH.exists():
        try:
            with open(RING_STORAGE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    agent_id = event.get("agent_id") or event.get("actor_id")
                    if agent_id:
                        agents.add(str(agent_id))
        except OSError:
            pass

    if agents:
        return {"agents": sorted(list(agents)), "source": "ring_storage"}
    # fallback to relational memory
    mem = load_json(RELATIONAL_MEMORY_PATH, None)
    if isinstance(mem, dict):
        nodes = mem.get("nodes")
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    agent_id = node.get("agent_id") or node.get("actor_id")
                    if agent_id:
                        agents.add(str(agent_id))
    return {"agents": sorted(list(agents)), "source": "relational_memory" if agents else "none"}'''

# استبدال أي دالة تبدأ بـ "def load_agents" وتنتهي بسطر فارغ قبل الدالة التالية أو نهاية الملف
pattern = r'def load_agents\(\) -> dict:.*?(?=\n\n\ndef |\n\n\Z)'
# note: use re.DOTALL
match = re.search(pattern, text, flags=re.DOTALL)
if not match:
    print("Could not find load_agents function")
    sys.exit(1)

text = text[:match.start()] + new_func + text[match.end():]
atomic_write(server_path, text)
print("Successfully updated /agents endpoint")
