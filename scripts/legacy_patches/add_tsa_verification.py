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
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise

file = ROOT / 'tools' / 'innocence_chain.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# 1. إضافة دالة التحقق بعد دالة get_rfc3161_timestamp
func_to_add = '''

def verify_rfc3161_token(token_b64: str) -> bool:
    """Perform a basic integrity check of an RFC3161 token."""
    import base64
    import subprocess
    import tempfile
    from pathlib import Path as _Path
    if not token_b64:
        return False
    token_file = None
    try:
        token_bytes = base64.b64decode(token_b64)
        fd, token_file = tempfile.mkstemp(suffix='.tsr')
        with os.fdopen(fd, 'wb') as f:
            f.write(token_bytes)
        result = subprocess.run(
            ["openssl", "ts", "-reply", "-in", token_file, "-text"],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False
    finally:
        if token_file and os.path.exists(token_file):
            os.unlink(token_file)
'''

marker = 'def get_rfc3161_timestamp(data: str) -> str:'
# نجد نهاية الدالة الحالية (أول سطر فارغ بعدها)
# سنستخدم أسلوب replace بسيط: نضيف الدالة بعد انتهاء get_rfc3161_timestamp
# لكن من الصعب تحديد النهاية بدقة، لذا سنضيف الدالة قبل generate_ring مباشرة
insert_before = 'def generate_ring() -> dict:'
if insert_before not in text:
    print("Could not find generate_ring")
    sys.exit(1)
text = text.replace(insert_before, func_to_add + '\n' + insert_before, 1)

# 2. تعديل generate_ring لاستدعاء verify وإضافة حقل tsa_verified
old_block = "rfc3161_token = get_rfc3161_timestamp(agent_events_hash)\n    tsa_provider = os.environ.get('AAAC_TSA_URL', 'http://time.certum.pl')"
new_block = "rfc3161_token = get_rfc3161_timestamp(agent_events_hash)\n    tsa_provider = os.environ.get('AAAC_TSA_URL', 'http://time.certum.pl')\n    tsa_verified = verify_rfc3161_token(rfc3161_token) if rfc3161_token else False"
if old_block not in text:
    print("Old rfc block not found")
    sys.exit(1)
text = text.replace(old_block, new_block, 1)

# 3. إضافة الحقل في بناء الحلقة
old_dict = '''    ring = {
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
new_dict = '''    ring = {
        "ring_hash": ring_hash,
        "prev_ring_hash": prev_hash,
        "integrity_status": integrity_status,
        "relational_memory_snapshot": snapshot,
        "realtime_events_hash": realtime_events_hash,
        "agent_events_hash": agent_events_hash,
        "rfc3161_token": rfc3161_token,
        "tsa_provider": tsa_provider,
        "tsa_verified": tsa_verified,
        "signature": signature,
        "chain_id": chain_id,
        "created_at": utc_now_iso(),
    }'''
if old_dict not in text:
    print("Old ring dict not found")
    sys.exit(1)
text = text.replace(old_dict, new_dict, 1)

atomic_write(file, text)
print("Successfully added TSA verification and tsa_verified field")
