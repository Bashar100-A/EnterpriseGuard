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

log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')

ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1

entry = f"| DC-{next_num} | 2026-09-07T15:00:00Z | Start execution phase and accept investor conditions | Accepted investor offer of $400k at $2.5M pre-money. Conditions for first tranche: key backup (Shamir/age) in 60 days, standalone open_verifier in 45 days, ECDSA migration with 40% perf improvement in 60 days. Execution plan created. | Execution started | Complete |\n"

if not text.endswith('\n'):
    text += '\n'
text += entry
atomic_write(log_path, text)
print(f"Added DC-{next_num}")
