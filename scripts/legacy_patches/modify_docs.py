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
    backup = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, backup)
    return backup

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

# ===== 1. إضافة قرار جديد في DECISIONS_LOG.md =====
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
if log_path.exists():
    backup_file(log_path)
    text = log_path.read_text(encoding='utf-8')
    # حساب الرقم التالي
    ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
    next_num = max((int(n) for _, n in ids), default=63) + 1
    entry = (
        f"| DC-{next_num} | 2026-09-06T15:25:00Z | AAAC MVP Connector and Chain Integration (Working Prototype) | "
        "Created aaac_connector.py using Langfuse Cloud free tier, fetching observations via v2 API, saving to ring_storage.jsonl; "
        "modified innocence_chain.py to include agent_events_hash in compute_ring_hash, generate_ring, and _verify_rings; "
        "reset chain and verified VERIFIED_OK. integrity_status is FAIL due to baselines not updated after code changes. | "
        "Prototype verified locally with test trace | Complete |\n"
    )
    if not text.endswith('\n'):
        text += '\n'
    text += entry
    atomic_write(log_path, text)
    print(f"Added DC-{next_num} to DECISIONS_LOG.md")

# ===== 2. تحديث CURRENT_STATE.md =====
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
if state_path.exists():
    backup_file(state_path)
    text = state_path.read_text(encoding='utf-8')
    if '## Technical Prototype Update — 2026-09-06' not in text:
        insert_block = '''
## Technical Prototype Update — 2026-09-06

- Langfuse Cloud (free tier) used instead of self-hosted Langfuse V3 due to ClickHouse complexity.
- Created `tools/aaac_connector.py` which fetches observations from Langfuse v2 API, normalizes them, and saves to `tools/ring_storage.jsonl`.
- Modified `tools/innocence_chain.py` to include `agent_events_hash` in ring computation, generation, and verification.
- Reset innocence chain and verified `VERIFIED_OK`.
- `integrity_status` is currently `FAIL` because baselines were not regenerated after code changes (expected during active development).
- Next steps: update baselines to restore PASS, then test ring generation with new agent events.
'''
        text = text.replace('---\n\n## Last Completed Decisions (Latest)', insert_block + '\n---\n\n## Last Completed Decisions (Latest)')
    atomic_write(state_path, text)
    print("Updated CURRENT_STATE.md")

# ===== 3. تحديث COMPONENTS.md =====
comp_path = ROOT / 'continuity' / 'COMPONENTS.md'
if comp_path.exists():
    backup_file(comp_path)
    text = comp_path.read_text(encoding='utf-8')
    if 'AAAC Connector (Prototype)' not in text:
        note = '\n> New in prototype: `tools/aaac_connector.py` (Langfuse integration), `tools/ring_storage.jsonl` (agent events), `tools/send_test_trace.py` (test trace sender).\n'
        text = note + text
    atomic_write(comp_path, text)
    print("Updated COMPONENTS.md")

# ===== 4. إنشاء docs/AAAC_PROTOTYPE_NOTES.md =====
notes_path = ROOT / 'docs' / 'AAAC_PROTOTYPE_NOTES.md'
backup_file(notes_path) if notes_path.exists() else None
notes_content = '''# AAAC Prototype Notes — Langfuse Integration and Chain Extension

**Date:** 2026-09-06T15:25:00Z
**Status:** Working prototype (local testing)

## Goal
Create a proof layer that pulls agent traces from Langfuse, normalizes them, stores them temporarily, and includes their hash in the innocence chain.

## Steps Completed
1. Dropped self-hosted Langfuse V3 due to ClickHouse complexity; switched to Langfuse Cloud free tier (5k traces/month).
2. Created `tools/send_test_trace.py` using REST API to send a test observation.
3. Created `tools/aaac_connector.py` to fetch observations from Langfuse v2 API, merge trace metadata, and save normalized events to `tools/ring_storage.jsonl`.
4. Modified `tools/innocence_chain.py`:
   - Added `get_last_agent_events_hash()` to compute SHA-256 of last line in ring_storage.
   - Extended `compute_ring_hash` with `agent_events_hash` parameter.
   - Updated `_verify_rings` and `generate_ring` to include the new field.
5. Reset innocence chain (old chain was incompatible) and generated new genesis ring.
6. Verified chain: `VERIFIED_OK`.

## Known Issues
- `integrity_status` shows `FAIL` because baselines not regenerated after code changes.
- Langfuse API v1 trace endpoint is deprecated but still working until Nov 2026.
- API keys were exposed in chat during testing; should be rotated before any real use.

## Next Steps
- Regenerate trust/integrity baselines so integrity_status becomes PASS.
- Test end-to-end: send new trace → run connector → generate ring → verify chain.
- Add sensitive data filtering (already minimal in connector).
'''
atomic_write(notes_path, notes_content)
print(f"Created {notes_path}")

print("All documentation updates completed.")
