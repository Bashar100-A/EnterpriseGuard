import re
import sys
import shutil
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True
ROOT = Path('.')

def backup_file(path: Path):
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    b = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, b)
    return b

def atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fh:
            fh.write(content)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise

# 1) إضافة قرار DC-86
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')
ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1

entry = (
    f"| DC-{next_num} | 2026-09-06T21:00:00Z | Shift to self-imposing compliance layer (no market wait) | "
    "Owner decided to stop waiting for customer discovery results and instead build AAAC as a mandatory regulatory/technical layer. "
    "Focus on deep BYO-TSA/BYO-HSM integration, native LangSmith/Langfuse connectors, open-source verification standard, and EU AI Act compliance. "
    "Customer interviews will be used opportunistically, not as gate. | Strategic pivot approved by owner | Complete |\n"
)
if not text.endswith('\n'):
    text += '\n'
text += entry
atomic_write(log_path, text)
print(f"Added DC-{next_num}")

# 2) تحديث DECISIONS_INDEX.md
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')
lines = index_text.splitlines()
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-'):
        insert_pos = i + 1
if insert_pos is not None:
    lines.insert(insert_pos, f"| DC-{next_num} | Shift to self-imposing compliance layer (no market wait) | 2026-09-06 |")
    new_index = '\n'.join(lines) + '\n'
else:
    new_index = index_text
atomic_write(index_path, new_index)
print("Updated DECISIONS_INDEX.md")

# 3) تحديث CURRENT_STATE.md
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')
insert = f'''

## Strategic Pivot — 2026-09-06 (DC-{next_num})

- AAAC is no longer waiting for market pull; we are building a self-imposing compliance and trust layer.
- Immediate focus:
  - Revert temporary dashboard auth bypass (restore security before external exposure).
  - Implement BYO-TSA adapter for eIDAS Qualified Timestamp (QTSP) and BYO-HSM signing.
  - Create native connectors for LangSmith/Langfuse with configurable endpoints.
  - Enhance open-source verifier to be fully standalone (no dependency on private code).
  - Generate automated compliance evidence reports (EU AI Act Art.12/14).
- Customer discovery continues opportunistically but is no longer a gate for engineering.
- Next technical milestone: production-grade AAAC Core v0.2 with dynamic trust service plug-in.

'''
if 'Strategic Pivot — 2026-09-06' not in state_text:
    state_text = state_text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, state_text)
print("Updated CURRENT_STATE.md")

# 4) تحديث COMPONENTS.md
comp_path = ROOT / 'continuity' / 'COMPONENTS.md'
backup_file(comp_path)
comp_text = comp_path.read_text(encoding='utf-8')
if 'Self-imposing compliance layer' not in comp_text:
    comp_text = comp_text.replace('> Current phase:', '> Strategic direction: Self-imposing compliance layer.\n> Current phase:')
atomic_write(comp_path, comp_text)
print("Updated COMPONENTS.md")
