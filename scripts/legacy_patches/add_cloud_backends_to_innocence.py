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

# إضافة استيراد signing_backend في حالة عدم وجوده (يجب أن يكون موجودًا)
if 'from tools.signing_backend import' not in text:
    # إضافة بعد استيراد paths_config
    insert_after = 'from tools.paths_config import (\n'
    # إيجاد نهاية كتلة الاستيراد
    end = text.find(')', text.find(insert_after))
    if end != -1:
        insert_pos = text.find('\n', end) + 1
        text = text[:insert_pos] + '\nfrom tools.signing_backend import sign_bytes, verify_signature_hex, sign_genesis_chain_id_hex, verify_genesis_signature_hex\n' + text[insert_pos:]

# تعديل sign_ring_hash: إضافة فرع للخلفيات الأخرى بعد فرع mock
old_sign = "def sign_ring_hash(ring_hash: str) -> str:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        return hashlib.sha256((\"mock:\" + ring_hash).encode(\"utf-8\")).hexdigest()\n"
new_sign = "def sign_ring_hash(ring_hash: str) -> str:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        return hashlib.sha256((\"mock:\" + ring_hash).encode(\"utf-8\")).hexdigest()\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") in (\"aws_kms\", \"tpm\"):\n        return sign_bytes(ring_hash)\n"
if old_sign in text:
    text = text.replace(old_sign, new_sign, 1)
else:
    print("sign_ring_hash pattern not found, attempting insert")
    # fallback: just insert before local code
    marker = 'def sign_ring_hash(ring_hash: str) -> str:\n'
    if marker in text:
        text = text.replace(marker, new_sign, 1)
    else:
        print("Could not find sign_ring_hash")
        sys.exit(1)

# تعديل verify_ring_signature
old_verify = "def verify_ring_signature(ring_hash: str, signature_hex: str) -> bool:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        expected = hashlib.sha256((\"mock:\" + ring_hash).encode(\"utf-8\")).hexdigest()\n        return signature_hex == expected\n"
new_verify = "def verify_ring_signature(ring_hash: str, signature_hex: str) -> bool:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        expected = hashlib.sha256((\"mock:\" + ring_hash).encode(\"utf-8\")).hexdigest()\n        return signature_hex == expected\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") in (\"aws_kms\", \"tpm\"):\n        return verify_signature_hex(ring_hash, signature_hex)\n"
if old_verify in text:
    text = text.replace(old_verify, new_verify, 1)
else:
    print("verify_ring_signature pattern not found")
    # fallback similar
    marker = 'def verify_ring_signature(ring_hash: str, signature_hex: str) -> bool:\n'
    if marker in text:
        text = text.replace(marker, new_verify, 1)
    else:
        sys.exit(1)

# تعديل sign_genesis_chain_id
old_gen_sign = "def sign_genesis_chain_id(chain_id: str) -> str:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        return hashlib.sha256((\"genesis-mock:\" + chain_id).encode(\"utf-8\")).hexdigest()\n"
new_gen_sign = "def sign_genesis_chain_id(chain_id: str) -> str:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        return hashlib.sha256((\"genesis-mock:\" + chain_id).encode(\"utf-8\")).hexdigest()\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") in (\"aws_kms\", \"tpm\"):\n        return sign_genesis_chain_id_hex(chain_id)\n"
if old_gen_sign in text:
    text = text.replace(old_gen_sign, new_gen_sign, 1)
else:
    print("sign_genesis_chain_id pattern not found")
    marker = 'def sign_genesis_chain_id(chain_id: str) -> str:\n'
    if marker in text:
        text = text.replace(marker, new_gen_sign, 1)
    else:
        sys.exit(1)

# تعديل verify_genesis_signature
old_gen_verify = "def verify_genesis_signature(chain_id: str, signature_hex: str) -> bool:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        expected = hashlib.sha256((\"genesis-mock:\" + chain_id).encode(\"utf-8\")).hexdigest()\n        return signature_hex == expected\n"
new_gen_verify = "def verify_genesis_signature(chain_id: str, signature_hex: str) -> bool:\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") == \"mock\":\n        expected = hashlib.sha256((\"genesis-mock:\" + chain_id).encode(\"utf-8\")).hexdigest()\n        return signature_hex == expected\n    if os.environ.get(\"AAAC_SIGNING_BACKEND\") in (\"aws_kms\", \"tpm\"):\n        return verify_genesis_signature_hex(chain_id, signature_hex)\n"
if old_gen_verify in text:
    text = text.replace(old_gen_verify, new_gen_verify, 1)
else:
    print("verify_genesis_signature pattern not found")
    marker = 'def verify_genesis_signature(chain_id: str, signature_hex: str) -> bool:\n'
    if marker in text:
        text = text.replace(marker, new_gen_verify, 1)
    else:
        sys.exit(1)

atomic_write(file, text)
print("Successfully added cloud/TPM branches to innocence_chain.py")
