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

old_block = '''    valid, reason = innocence_chain.verify_chain()
    if valid:
        print("Chain verification: VERIFIED_OK")
        return 0
    else:
        print(f"Chain verification failed: {reason}", file=sys.stderr)
        return 3'''

new_block = '''    valid = innocence_chain.verify_chain()
    if valid:
        print("Chain verification: VERIFIED_OK")
        return 0
    else:
        print("Chain verification failed", file=sys.stderr)
        return 3'''

if old_block in text:
    text = text.replace(old_block, new_block, 1)
    atomic_write(file, text)
    print("Successfully fixed aaac_cli.py verification handling")
else:
    print("Old block not found, attempting alternative")
    # fallback: replace line by line
    text = text.replace("valid, reason = innocence_chain.verify_chain()", "valid = innocence_chain.verify_chain()")
    text = text.replace('print(f"Chain verification failed: {reason}", file=sys.stderr)', 'print("Chain verification failed", file=sys.stderr)')
    atomic_write(file, text)
    print("Attempted fallback fix")
