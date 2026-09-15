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

file = ROOT / 'tools' / 'innocence_chain.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# 1. استبدال دالة get_rfc3161_timestamp الحالية بالنسخة الصحيحة
pattern = r'def get_rfc3161_timestamp\(data: str\) -> str:.*?\n\n'
new_func = '''def get_rfc3161_timestamp(data: str) -> str:
    """Request RFC3161 timestamp token from configured TSA and return base64 token."""
    import subprocess
    import requests
    import base64
    from urllib.parse import urlparse

    tsa_url = os.environ.get("AAAC_TSA_URL", "http://time.certum.pl")
    try:
        # إنشاء استعلام طابع زمني بصيغة DER
        query = subprocess.run(
            ["openssl", "ts", "-query", "-data", "-", "-sha256"],
            input=data.encode("utf-8"),
            capture_output=True,
            timeout=10,
            check=True,
        ).stdout

        # إرسال الاستعلام إلى خادم TSA
        headers = {"Content-Type": "application/timestamp-query"}
        resp = requests.post(tsa_url, data=query, headers=headers, timeout=15)
        if resp.status_code == 200:
            # تخزين الرد كـ base64
            return base64.b64encode(resp.content).decode("ascii")
        else:
            print(f"TSA returned status {resp.status_code}", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"Timestamp request failed: {e}", file=sys.stderr)
        return ""

'''
if re.search(pattern, text, flags=re.DOTALL):
    text = re.sub(pattern, new_func, text, count=1, flags=re.DOTALL)
else:
    print("Could not find get_rfc3161_timestamp function")
    sys.exit(1)

# 2. إضافة متغير tsa_provider وحفظه في الحلقة
# نبحث عن السطر الذي يستدعي get_rfc3161_timestamp
old_call = "rfc3161_token = get_rfc3161_timestamp(agent_events_hash)"
new_call = "rfc3161_token = get_rfc3161_timestamp(agent_events_hash)\n    tsa_provider = os.environ.get('AAAC_TSA_URL', 'http://time.certum.pl')"
if old_call not in text:
    print("Old get_rfc3161_timestamp call not found")
    sys.exit(1)
text = text.replace(old_call, new_call, 1)

# 3. إضافة حقل tsa_provider في بناء الحلقة
old_dict = '''    ring = {
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
new_dict = '''    ring = {
        "ring_hash": ring_hash,
        "prev_ring_hash": prev_hash,
        "integrity_status": integrity_status,
        "relational_memory_snapshot": snapshot,
        "realtime_events_hash": realtime_events_hash,
        "agent_events_hash": agent_events_hash,
        "rfc3161_token": rfc3161_token,
        "tsa_provider": tsa_provider,
        "signature": signature,
        "chain_id": chain_id,
        "created_at": utc_now_iso(),
    }'''
if old_dict not in text:
    print("Old ring dict not found")
    sys.exit(1)
text = text.replace(old_dict, new_dict, 1)

atomic_write(file, text)
print("Successfully updated RFC3161 timestamp with dynamic TSA and tsa_provider field")
