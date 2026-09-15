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

file = ROOT / 'tools' / 'innocence_chain.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# تعديل sign_ring_hash: إضافة فرع mock في البداية
text = text.replace(
    'def sign_ring_hash(ring_hash: str) -> str:\n',
    'def sign_ring_hash(ring_hash: str) -> str:\n    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":\n        return hashlib.sha256(("mock:" + ring_hash).encode("utf-8")).hexdigest()\n'
)

# تعديل verify_ring_signature: إضافة فرع mock في البداية
text = text.replace(
    'def verify_ring_signature(ring_hash: str, signature_hex: str) -> bool:\n',
    'def verify_ring_signature(ring_hash: str, signature_hex: str) -> bool:\n    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":\n        expected = hashlib.sha256(("mock:" + ring_hash).encode("utf-8")).hexdigest()\n        return signature_hex == expected\n'
)

# تعديل sign_genesis_chain_id
text = text.replace(
    'def sign_genesis_chain_id(chain_id: str) -> str:\n',
    'def sign_genesis_chain_id(chain_id: str) -> str:\n    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":\n        return hashlib.sha256(("genesis-mock:" + chain_id).encode("utf-8")).hexdigest()\n'
)

# تعديل verify_genesis_signature
text = text.replace(
    'def verify_genesis_signature(chain_id: str, signature_hex: str) -> bool:\n',
    'def verify_genesis_signature(chain_id: str, signature_hex: str) -> bool:\n    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":\n        expected = hashlib.sha256(("genesis-mock:" + chain_id).encode("utf-8")).hexdigest()\n        return signature_hex == expected\n'
)

atomic_write(file, text)
print("Successfully added mock branches to signing functions")
