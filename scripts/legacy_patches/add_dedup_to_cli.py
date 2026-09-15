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

file = ROOT / 'tools' / 'aaac_cli.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# 1. إضافة دالة load_existing_trace_ids بعد تعريف RING_STORAGE_PATH
insert_after = 'RING_STORAGE_PATH = ROOT / "tools" / "ring_storage.jsonl"'
new_func = '''

def load_existing_trace_ids():
    """Return set of trace_ids already stored in ring_storage.jsonl."""
    ids = set()
    if RING_STORAGE_PATH.exists():
        try:
            with open(RING_STORAGE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            tid = event.get("trace_id")
                            if tid:
                                ids.add(tid)
                        except json.JSONDecodeError:
                            continue
        except OSError:
            pass
    return ids
'''
text = text.replace(insert_after, insert_after + new_func, 1)

# 2. تعديل main لتصفية الأحداث المكررة
old_block = '''    for event in events:
        append_event_to_ring_storage(event)

    print(f"Stored {len(events)} events to {RING_STORAGE_PATH}")'''
new_block = '''    existing_ids = load_existing_trace_ids()
    new_events = []
    for event in events:
        tid = event.get("trace_id")
        if tid and tid in existing_ids:
            print(f"Skipping duplicate trace_id: {tid}")
            continue
        new_events.append(event)

    for event in new_events:
        append_event_to_ring_storage(event)

    print(f"Stored {len(new_events)} new events to {RING_STORAGE_PATH}")'''
if old_block not in text:
    print("Old block not found")
    sys.exit(1)
text = text.replace(old_block, new_block, 1)

atomic_write(file, text)
print("Successfully added duplicate avoidance to aaac_cli.py")
