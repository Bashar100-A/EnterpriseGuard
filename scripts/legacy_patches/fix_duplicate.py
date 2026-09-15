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

file = ROOT / 'tools' / 'aaac_connector.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# إضافة دالة load_existing_trace_ids
new_func = '''

def load_existing_trace_ids():
    """Return set of trace_ids already stored in ring_storage.jsonl."""
    ids = set()
    if RING_STORAGE_PATH.exists():
        try:
            with open(RING_STORAGE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            tid = event.get('trace_id')
                            if tid:
                                ids.add(tid)
                        except json.JSONDecodeError:
                            continue
        except OSError:
            pass
    return ids
'''

# إدراجها قبل save_event_to_ring_storage
marker = 'def save_event_to_ring_storage'
if marker not in text:
    print('Marker not found')
    sys.exit(1)
text = text.replace(marker, new_func + '\n' + marker, 1)

# تعديل main لتجاهل التكرار
old_main = '''    normalized_events = []
    for obs in observations:
        trace_id = obs.get("traceId", "")
        trace_data = fetch_trace(trace_id) if trace_id else {}
        event = normalize_observation(obs, trace_data)
        normalized_events.append(event)
'''
new_main = '''    existing_ids = load_existing_trace_ids()
    normalized_events = []
    for obs in observations:
        trace_id = obs.get("traceId", "")
        if trace_id in existing_ids:
            print(f"Skipping duplicate trace_id: {trace_id}")
            continue
        trace_data = fetch_trace(trace_id) if trace_id else {}
        event = normalize_observation(obs, trace_data)
        normalized_events.append(event)
'''
if old_main not in text:
    print('Old main block not found')
    sys.exit(1)
text = text.replace(old_main, new_main, 1)

atomic_write(file, text)
print('Successfully added duplicate avoidance')
