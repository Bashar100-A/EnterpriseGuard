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

file = ROOT / 'tools' / 'open_verifier.py'
backup_file(file)
text = file.read_text(encoding='utf-8')

# استبدال دالة verify_signature لتحويل hex إلى bytes
old_verify = '''def verify_signature(ring_hash: str, signature: str, public_key: Path) -> bool:
    if not signature or not public_key.exists():
        return False
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        f.write(ring_hash)
        data_file = f.name
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sig") as f:
        f.write(signature)
        sig_file = f.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(public_key),
             "-signature", sig_file, data_file],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0 and b"Verified OK" in result.stdout
    except Exception:
        return False
    finally:
        Path(data_file).unlink(missing_ok=True)
        Path(sig_file).unlink(missing_ok=True)'''

new_verify = '''def verify_signature(ring_hash: str, signature: str, public_key: Path) -> bool:
    if not signature or not public_key.exists():
        return False
    # Convert hex signature to bytes
    try:
        sig_bytes = bytes.fromhex(signature)
    except ValueError:
        return False
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        f.write(ring_hash)
        data_file = f.name
    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".sig") as f:
        f.write(sig_bytes)
        sig_file = f.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(public_key),
             "-signature", sig_file, data_file],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0 and b"Verified OK" in result.stdout
    except Exception:
        return False
    finally:
        Path(data_file).unlink(missing_ok=True)
        Path(sig_file).unlink(missing_ok=True)'''

if old_verify not in text:
    print("Old verify_signature not found")
    sys.exit(1)
text = text.replace(old_verify, new_verify, 1)

# تعديل verify_genesis_signature بنفس الطريقة
old_gen = '''def verify_genesis_signature(chain_id: str, signature: str, public_key: Path) -> bool:
    if not signature or not public_key.exists():
        return False
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        f.write(chain_id)
        data_file = f.name
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sig") as f:
        f.write(signature)
        sig_file = f.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(public_key),
             "-signature", sig_file, data_file],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0 and b"Verified OK" in result.stdout
    except Exception:
        return False
    finally:
        Path(data_file).unlink(missing_ok=True)
        Path(sig_file).unlink(missing_ok=True)'''

new_gen = '''def verify_genesis_signature(chain_id: str, signature: str, public_key: Path) -> bool:
    if not signature or not public_key.exists():
        return False
    try:
        sig_bytes = bytes.fromhex(signature)
    except ValueError:
        return False
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        f.write(chain_id)
        data_file = f.name
    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".sig") as f:
        f.write(sig_bytes)
        sig_file = f.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(public_key),
             "-signature", sig_file, data_file],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0 and b"Verified OK" in result.stdout
    except Exception:
        return False
    finally:
        Path(data_file).unlink(missing_ok=True)
        Path(sig_file).unlink(missing_ok=True)'''

if old_gen not in text:
    print("Old verify_genesis_signature not found")
    sys.exit(1)
text = text.replace(old_gen, new_gen, 1)

atomic_write(file, text)
print("Successfully fixed hex conversion in open_verifier.py")
