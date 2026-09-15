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

file = ROOT / 'tools' / 'innocence_chain.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# إضافة دالة get_rfc3161_timestamp
func = '''

def get_rfc3161_timestamp(data: str) -> str:
    """Request RFC3161 timestamp token from FreeTSA.org and return base64 token."""
    import requests
    import hashlib
    from base64 import b64encode
    try:
        digest = hashlib.sha256(data.encode('utf-8')).digest()
        headers = {"Content-Type": "application/timestamp-query"}
        resp = requests.post("https://freetsa.org/tsr", data=digest, headers=headers, timeout=10)
        if resp.status_code == 200:
            return b64encode(resp.content).decode('utf-8')
        return ""
    except Exception:
        return ""
'''
# إدراج بعد get_last_agent_events_hash
pattern = r'(def get_last_agent_events_hash\(\) -> str:.*?\n\n)'
if re.search(pattern, text, flags=re.DOTALL):
    text = re.sub(pattern, r'\1' + func, text, count=1, flags=re.DOTALL)
else:
    print('Insertion point not found')
    sys.exit(1)

# تعديل generate_ring
old_call = '''    ring_hash = compute_ring_hash(
        prev_hash, identity_key, integrity_status, snapshot,
        realtime_events_hash, chain_id, agent_events_hash
    )'''
new_call = '''    rfc3161_token = get_rfc3161_timestamp(agent_events_hash)
    ring_hash = compute_ring_hash(
        prev_hash, identity_key, integrity_status, snapshot,
        realtime_events_hash, chain_id, agent_events_hash
    )'''
if old_call not in text:
    print('Old ring_hash call not found')
    sys.exit(1)
text = text.replace(old_call, new_call, 1)

# تعديل بناء ring
old_dict = '''    ring = {
        "ring_hash": ring_hash,
        "prev_ring_hash": prev_hash,
        "integrity_status": integrity_status,
        "relational_memory_snapshot": snapshot,
        "realtime_events_hash": realtime_events_hash,
        "agent_events_hash": agent_events_hash,
        "signature": signature,
        "chain_id": chain_id,
        "created_at": utc_now_iso(),
    }'''
new_dict = '''    ring = {
        "ring_hash": ring_hash,
        "prev_ring_hash": prev_hash,
        "integrity_status": integrity_status,
        "relational_memory_snapshot": snapshot,
        "realtime_events_hash": realtime_events_hash,
        "agent_events_hash": agent_events_hash,
        "rfc3161_token": rfc3161_token,
        "signature": signature,
        "chain_id": chain_id,
        "created_at": utc_now_iso(),
    }'''
if old_dict not in text:
    print('Old ring dict not found')
    sys.exit(1)
text = text.replace(old_dict, new_dict, 1)

atomic_write(file, text)
print('Successfully added RFC3161 timestamp support')
