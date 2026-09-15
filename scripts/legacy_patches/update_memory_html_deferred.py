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

# 1) DECISIONS_LOG.md
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')
ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1
entry = f"| DC-{next_num} | 2026-09-07T14:10:00Z | Defer HTML sovereign verifier fix | Attempted to fix sovereign_verifier.html using WebCrypto and jsrsasign; ring 0 signature verification still fails due to inconsistency between signing_backend and innocence_chain internal verification. Official verifiers (open_verifier.py and /verify-chain) work correctly. Decision: defer HTML verifier and rely on official tools for now. | open_verifier.py works | Complete |\n"
if not text.endswith('\n'): text += '\n'
text += entry
atomic_write(log_path, text)
print(f"Added DC-{next_num}")

# 2) DECISIONS_INDEX.md
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')
lines = index_text.splitlines()
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-'):
        insert_pos = i + 1
if insert_pos is not None:
    lines.insert(insert_pos, f"| DC-{next_num} | Defer HTML sovereign verifier fix | 2026-09-07 |")
    new_index = '\n'.join(lines) + '\n'
else:
    new_index = index_text
atomic_write(index_path, new_index)
print("Updated DECISIONS_INDEX.md")

# 3) CURRENT_STATE.md
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')
insert = f'''

## HTML Verifier Deferred — 2026-09-07 (DC-{next_num})

- HTML sovereign verifier still fails ring 0 signature verification.
- Official verifiers (`open_verifier.py`, `/verify-chain`) work.
- Decision: defer HTML verifier, focus on report and market.
'''
if 'HTML Verifier Deferred' not in state_text:
    state_text = state_text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, state_text)
print("Updated CURRENT_STATE.md")
