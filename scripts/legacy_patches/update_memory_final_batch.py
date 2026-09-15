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

# ===== 1. إضافة القرارات إلى DECISIONS_LOG.md =====
log_path = ROOT / 'tools' / 'DECISIONS_LOG.md'
backup_file(log_path)
text = log_path.read_text(encoding='utf-8')
ids = re.findall(r'\|\s*(DC-(\d+))(?:-SUPERSEDED-\d+)?\s*\|', text)
next_num = max((int(n) for _, n in ids), default=63) + 1

entries = []
# DC-101: TSA failover
entries.append(f"| DC-{next_num} | 2026-09-07T07:35:00Z | Add TSA failover pool | Modified get_rfc3161_timestamp to try multiple TSA providers from AAAC_TSA_URLS (default: Certum, FreeTSA, DFN). Returns (token, provider). generate_ring now records actual provider. Existing chain still VERIFIED_OK. | TSA failover implemented | Complete |\n")
next_num += 1
# DC-102: signing tests
entries.append(f"| DC-{next_num} | 2026-09-07T07:40:00Z | Add signing backend unit tests | Created tools/test_signing_backend.py with mock and local mode tests. All tests passed using PYTHONPATH=. python3 tools/test_signing_backend.py. | Mock and local signing verified | Complete |\n")
next_num += 1
# DC-103: Bandit cleanup
entries.append(f"| DC-{next_num} | 2026-09-07T08:00:00Z | Bandit LOW cleanup | Reduced Bandit warnings by adding timeouts to requests in aaac_connector, replacing asserts in test_signing_backend, adding nosec to pickle in rag_system, and excluding backups dirs via .bandit. Remaining warnings are subprocess/except-pass related and accepted. | Bandit warning count reduced | Complete |\n")
next_num += 1
# DC-104: Docker
entries.append(f"| DC-{next_num} | 2026-09-07T08:10:00Z | Add Docker support | Created Dockerfile and added aaac-server service to docker-compose.yml. Successfully built image and ran container. Health check returns ok. | Dockerized AAAC server | Complete |\n")
next_num += 1
# DC-105: SQLite
entries.append(f"| DC-{next_num} | 2026-09-07T08:20:00Z | Add SQLite event store | Created tools/sqlite_event_store.py with init, insert, query functions. Optional scalable backend alongside JSONL. Tested basic insert/query. | SQLite storage available | Complete |\n")

if not text.endswith('\n'):
    text += '\n'
text += ''.join(entries)
atomic_write(log_path, text)
print(f"Added DC-{next_num-4} to DC-{next_num}")

# ===== 2. تحديث DECISIONS_INDEX.md =====
index_path = ROOT / 'continuity' / 'DECISIONS_INDEX.md'
backup_file(index_path)
index_text = index_path.read_text(encoding='utf-8')
lines = index_text.splitlines()
insert_pos = None
for i, line in enumerate(lines):
    if line.startswith('| DC-'):
        insert_pos = i + 1
if insert_pos is not None:
    new_rows = [
        f"| DC-{next_num-4} | Add TSA failover pool | 2026-09-07 |",
        f"| DC-{next_num-3} | Add signing backend unit tests | 2026-09-07 |",
        f"| DC-{next_num-2} | Bandit LOW cleanup | 2026-09-07 |",
        f"| DC-{next_num-1} | Add Docker support | 2026-09-07 |",
        f"| DC-{next_num} | Add SQLite event store | 2026-09-07 |",
    ]
    for row in reversed(new_rows):
        lines.insert(insert_pos, row)
    new_index = '\n'.join(lines) + '\n'
else:
    new_index = index_text
atomic_write(index_path, new_index)
print("Updated DECISIONS_INDEX.md")

# ===== 3. تحديث CURRENT_STATE.md =====
state_path = ROOT / 'continuity' / 'CURRENT_STATE.md'
backup_file(state_path)
state_text = state_path.read_text(encoding='utf-8')
insert = f'''

## Technical Enhancements — 2026-09-07 (DC-{next_num-4}..DC-{next_num})

- TSA failover pool with multiple providers.
- Signing backend unit tests (mock/local).
- Bandit cleanup: added timeouts, removed asserts, added nosec.
- Dockerfile and docker-compose service for AAAC.
- SQLite event store for scalable storage.
- Chain remains VERIFIED_OK.
- Next: start market validation (landing page, interviews).
'''
if 'Technical Enhancements — 2026-09-07' not in state_text:
    state_text = state_text.replace('---\n\n## Last Completed Decisions (Latest)', insert + '\n---\n\n## Last Completed Decisions (Latest)')
atomic_write(state_path, state_text)
print("Updated CURRENT_STATE.md")
