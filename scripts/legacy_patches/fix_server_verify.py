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

file = ROOT / 'tools' / 'sovereign_http_server.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# 1. استيراد verify_chain الحقيقية
# نضيف استيراد في الأعلى بعد استيراد innocence_chain
if 'from tools.innocence_chain import verify_chain as real_verify_chain' not in text:
    text = text.replace(
        'from tools.paths_config import',
        'from tools.innocence_chain import verify_chain as real_verify_chain\nfrom tools.paths_config import',
        1
    )

# 2. استبدال الدالة المحلية verify_chain بتوجيه إلى real_verify_chain
# نبحث عن تعريف الدالة المحلية ونستبدلها
old_def = '''def verify_chain() -> tuple[bool, str]:
    """Validate ring presence, status, hashes, and predecessor linkage."""
    payload = load_json(INNOCENCE_CHAIN_PATH, None)
    if not isinstance(payload, dict):
        return False, "invalid_json"

    rings = payload.get("rings")
    if not isinstance(rings, list) or not rings:
        return False, "no_rings"

    previous_hash = None
    for index, ring in enumerate(rings):
        if not isinstance(ring, dict):
            return False, f"invalid_ring_{index}"
        if ring.get("integrity_status") != "PASS":
            return False, f"integrity_fail_{index}"
        ring_hash = ring.get("ring_hash")
        if not ring_hash:
            return False, f"missing_hash_{index}"
        if index > 0 and ring.get("prev_ring_hash") != previous_hash:
            return False, f"linkage_fail_{index}"
        previous_hash = ring_hash
    return True, "ok"
'''
new_def = '''def verify_chain() -> tuple[bool, str]:
    """Delegate to the canonical verification from innocence_chain."""
    try:
        valid = real_verify_chain(allow_unsigned=False)
        return valid, "ok" if valid else "invalid"
    except Exception as e:
        return False, str(e)
'''
if old_def in text:
    text = text.replace(old_def, new_def, 1)
else:
    print("Old verify_chain definition not found, trying alternative replacement")
    sys.exit(1)

# 3. إصلاح genesis_signature في serve_compliance_report
old_sig = '"genesis_signature": last_ring.get("genesis_signature", "") if rings and "genesis_signature" in rings[0] else "",'
new_sig = '"genesis_signature": rings[0].get("genesis_signature", "") if rings else "",'
text = text.replace(old_sig, new_sig, 1)

atomic_write(file, text)
print("Successfully fixed verify_chain and genesis_signature in server")
