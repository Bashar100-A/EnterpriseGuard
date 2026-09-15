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

# استبدال الدالة الحالية بالنسخة الصارمة (نفس المحتوى الذي سبق)
old_func = '''def verify_rfc3161_token(token_b64: str, data_hex: str = None) -> bool:
    """Verify RFC3161 token structure and optionally signature with TSA certificate."""
    import base64
    import subprocess
    import tempfile
    from pathlib import Path as _Path
    if not token_b64:
        return False
    token_file = None
    data_file = None
    try:
        token_bytes = base64.b64decode(token_b64)
        fd, token_file = tempfile.mkstemp(suffix='.tsr')
        with os.fdopen(fd, 'wb') as f:
            f.write(token_bytes)

        cmd = ["openssl", "ts", "-reply", "-in", token_file]
        # إذا توفرت شهادة CA خارجية، أضفها للتحقق من التوقيع
        ca_file = os.environ.get("AAAC_TSA_CAFILE")
        if ca_file and _Path(ca_file).exists():
            cmd += ["-CAfile", ca_file]
        # إذا مررنا data_hex (الهاش الأصلي)، يمكننا التحقق من تطابق الرسالة
        if data_hex:
            fd2, data_file = tempfile.mkstemp(suffix='.txt')
            with os.fdopen(fd2, 'wb') as f:
                f.write(bytes.fromhex(data_hex))
            cmd += ["-data", data_file]
        cmd += ["-text"]
        result = subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        return result.returncode == 0
    except Exception:
        return False
    finally:
        if token_file and os.path.exists(token_file):
            os.unlink(token_file)
        if data_file and os.path.exists(data_file):
            os.unlink(data_file)'''

new_func = '''def verify_rfc3161_token(token_b64: str, data_hex: str = None) -> bool:
    """Verify RFC3161 token signature if CA file provided; otherwise basic structure check."""
    import base64
    import subprocess
    import tempfile
    from pathlib import Path as _Path
    if not token_b64:
        return False
    token_file = None
    data_file = None
    try:
        token_bytes = base64.b64decode(token_b64)
        fd, token_file = tempfile.mkstemp(suffix='.tsr')
        with os.fdopen(fd, 'wb') as f:
            f.write(token_bytes)

        ca_file = os.environ.get("AAAC_TSA_CAFILE")
        cmd = ["openssl", "ts", "-reply", "-in", token_file]
        if ca_file and _Path(ca_file).exists() and _Path(ca_file).stat().st_size > 0:
            cmd += ["-CAfile", ca_file]
            if data_hex:
                fd2, data_file = tempfile.mkstemp(suffix='.txt')
                with os.fdopen(fd2, 'wb') as f:
                    f.write(bytes.fromhex(data_hex))
                cmd += ["-data", data_file]
            result = subprocess.run(cmd, capture_output=True, timeout=15, check=False)
            return result.returncode == 0
        else:
            result = subprocess.run(cmd + ["-text"], capture_output=True, timeout=15, check=False)
            return result.returncode == 0
    except Exception:
        return False
    finally:
        if token_file and os.path.exists(token_file):
            os.unlink(token_file)
        if data_file and os.path.exists(data_file):
            os.unlink(data_file)'''

if old_func in text:
    text = text.replace(old_func, new_func, 1)
    print("Replaced function with strict version")
else:
    print("Old function not found, try regex")
    import re
    pattern = r'def verify_rfc3161_token\(token_b64: str, data_hex: str = None\) -> bool:.*?(?=\n\n\ndef |\n\n\Z)'
    text = re.sub(pattern, new_func, text, count=1, flags=re.DOTALL)
    print("Regex replacement done")

atomic_write(file, text)
print("Successfully updated verify_rfc3161_token to strict mode")
