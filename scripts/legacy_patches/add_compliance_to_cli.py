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

# 1) إضافة استيراد compliance_engine بعد استيراد native_connectors
if 'from tools.compliance_engine import enrich_event_with_compliance' not in text:
    text = text.replace(
        'from tools.native_connectors import unified_fetch',
        'from tools.native_connectors import unified_fetch\nfrom tools.compliance_engine import enrich_event_with_compliance'
    )

# 2) تعديل حلقة الأحداث لإضافة الامتثال قبل التخزين
old_block = '''    for event in events:
        append_event_to_ring_storage(event)

    print(f"Stored {len(events)} events to {RING_STORAGE_PATH}")'''
new_block = '''    # Apply compliance engine to each event before storing
    for event in events:
        enriched = enrich_event_with_compliance(event)
        append_event_to_ring_storage(enriched)

    print(f"Stored {len(events)} events to {RING_STORAGE_PATH}")'''

if old_block in text:
    text = text.replace(old_block, new_block, 1)
    print("Modified main loop to apply compliance")
else:
    print("Old block not found, attempting alternative")
    # fallback: search for append_event_to_ring_storage(event)
    if 'append_event_to_ring_storage(event)' in text:
        text = text.replace(
            'append_event_to_ring_storage(event)',
            'enriched = enrich_event_with_compliance(event)\n        append_event_to_ring_storage(enriched)',
            1
        )
        print("Fallback applied")
    else:
        print("Could not find event appending code")
        sys.exit(1)

atomic_write(file, text)
print("Successfully integrated compliance engine into aaac_cli.py")
