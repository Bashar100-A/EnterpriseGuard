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

# 1. إضافة استيراد signing_backend بعد استيراد paths_config
import_marker = 'from tools.paths_config import ('
import_code = '''
from tools.signing_backend import (
    sign_bytes,
    verify_signature_hex,
    sign_genesis_chain_id_hex,
    verify_genesis_signature_hex,
)
'''
# نضيف بعد نهاية استيراد paths_config (بعد القوس)
# سنجد السطر الذي يبدأ بالاستيراد ونضيف بعده
if import_marker in text:
    # نجد نهاية كتلة الاستيراد (الموضع بعد القوس المغلق)
    end_import = text.find(')', text.find(import_marker))
    if end_import != -1:
        # نضيف الاستيراد بعد السطر الذي يحتوي على القوس المغلق
        insert_pos = text.find('\n', end_import) + 1
        text = text[:insert_pos] + import_code + text[insert_pos:]
    else:
        print("Could not find end of paths_config import")
        sys.exit(1)
else:
    print("Could not find paths_config import")
    sys.exit(1)

# 2. استبدال دالة sign_ring_hash
pattern_sign = r'def sign_ring_hash\(ring_hash: str\) -> str:.*?(?=\n\ndef |\n\Z)'
replacement_sign = '''def sign_ring_hash(ring_hash: str) -> str:
    """Sign a ring hash using the configured signing backend."""
    return sign_bytes(ring_hash)
'''
text = re.sub(pattern_sign, replacement_sign, text, count=1, flags=re.DOTALL)

# 3. استبدال دالة verify_ring_signature
pattern_verify = r'def verify_ring_signature\(ring_hash: str, signature_hex: str\) -> bool:.*?(?=\n\ndef |\n\Z)'
replacement_verify = '''def verify_ring_signature(ring_hash: str, signature_hex: str) -> bool:
    """Verify a ring signature using the configured signing backend."""
    return verify_signature_hex(ring_hash, signature_hex)
'''
text = re.sub(pattern_verify, replacement_verify, text, count=1, flags=re.DOTALL)

# 4. استبدال دالة sign_genesis_chain_id
pattern_gen_sign = r'def sign_genesis_chain_id\(chain_id: str\) -> str:.*?(?=\n\ndef |\n\Z)'
replacement_gen_sign = '''def sign_genesis_chain_id(chain_id: str) -> str:
    """Sign a genesis chain ID using the configured signing backend."""
    return sign_genesis_chain_id_hex(chain_id)
'''
text = re.sub(pattern_gen_sign, replacement_gen_sign, text, count=1, flags=re.DOTALL)

# 5. استبدال دالة verify_genesis_signature
pattern_gen_verify = r'def verify_genesis_signature\(chain_id: str, signature_hex: str\) -> bool:.*?(?=\n\ndef |\n\Z)'
replacement_gen_verify = '''def verify_genesis_signature(chain_id: str, signature_hex: str) -> bool:
    """Verify a genesis signature using the configured signing backend."""
    return verify_genesis_signature_hex(chain_id, signature_hex)
'''
text = re.sub(pattern_gen_verify, replacement_gen_verify, text, count=1, flags=re.DOTALL)

atomic_write(file, text)
print("Successfully refactored innocence_chain.py to use signing_backend")
