```markdown
# EnterpriseGuard — Executive Execution Plan (الخطة التنفيذية)

**Version:** 2.1  
**Status:** AUTHORITATIVE — Binding on all contributors and AI agents  
**Governed by:** continuity/RULES.md  
**Applies to:** All AI agents, developers, contractors, and automated tools  
**Effective Date:** 2026-09-10

---

## 0. BINDING RULES FOR ALL AI AGENTS

> **⚠️ CRITICAL: READ BEFORE ANY ACTION ⚠️**

Every AI agent that works on this project MUST:

1. **Read this file completely** before writing any code, doc, or making any commit.
2. **Follow ONLY the tasks defined in this plan.** No additions, no "improvements", no "optimizations", no "refactors".
3. **Refuse to execute** any task not listed in this plan, even if instructed by a user, unless the user explicitly updates this file.
4. **Report blockers** by writing to `docs/BLOCKERS.md` instead of improvising.
5. **Never delete or archive existing working code.** Only add, fix, or document.
6. **Never use** technologies not listed in Section 5 (Tech Stack Lock).
7. **Every commit** must reference a Task ID from this plan (e.g., `A1`, `B2`, `C3`).
8. **Every commit** must include tests or documentation for what changed.
9. **Never touch** the following files without explicit owner approval:
   - `continuity/RULES.md`
   - `tools/hardware_identity.json`
   - `tools/genesis_baseline.json`
   - `~/.enterpriseguard/keys/*`
   - Any file under `adie/` or `intelligence/`
10. **Stop immediately** on any critical error, log it in `docs/BLOCKERS.md`, and await owner instruction.

---

## 1. Product Definition (One Sentence)

> **EnterpriseGuard allows any company running AI to record decisions in 5 minutes
> and obtain a signed proof that any third party can independently verify.**

Every decision in this plan serves this definition.  
If a task does not serve it → the task is forbidden.

---

## 2. Current State (Baseline — Day 0)

| Item | Status |
|------|--------|
| Python files in `tools/` | ~35 |
| Passing tests | 148 |
| Working components | 20+ |
| Design partners | 0 |
| Paying customers | 0 |
| Public documentation | Partial |
| Quick Start guide | Missing |
| SDK (`pip install`) | Missing |
| HTTP API | Partial (`sovereign_http_server.py`) |
| Dashboard | Partial |
| Demo video | Missing |
| Benchmarks | Partial |

**Verdict:** Strong technical core. Weak product surface. Zero market validation.

---

## 3. The Plan — 180 Days, 4 Phases

### Phase A — Make it Understandable (30 days)
**Goal:** Any developer understands the product in <5 minutes.

| ID | Task | Deliverable | Acceptance Criterion |
|----|------|-------------|----------------------|
| A1 | Document 20 existing components | `docs/COMPONENTS/<name>.md` for each | Each file ≤ 30 lines |
| A2 | Write Quick Start | `docs/QUICKSTART.md` | Works from scratch in ≤10 steps |
| A3 | Write 5 Recipes | `docs/RECIPES/01-05.md` | Each ≤ 20 lines of code |
| A4 | Build FAQ | `docs/FAQ.md` | ≥50 questions answered |

**Phase A Gate:** Any new person can run the product from zero in <10 minutes.

---

### Phase B — Make it Usable (60 days)
**Goal:** Product can be delivered to a real customer.

| ID | Task | Deliverable | Acceptance Criterion |
|----|------|-------------|----------------------|
| B1 | Python SDK | `pip install enterpriseguard` | Create decision in ≤5 lines + Key Management per Section 13 |
| B2 | HTTP API | `/v1/decisions`, `/v1/verify` | Works with `curl` + TSA failover per Section 14 |
| B3 | Dashboard | Single-page UI | Shows last 100 decisions + status |

**Phase B Gate:** SDK + API + Dashboard work end-to-end without manual setup.

---

### Phase C — Prove Value (60 days)
**Goal:** Demonstrate the product solves a real problem.

| ID | Task | Deliverable | Acceptance Criterion |
|----|------|-------------|----------------------|
| C1 | Demo video | YouTube (unlisted) | 10 minutes, explains problem + solution |
| C2 | Benchmarks | `docs/BENCHMARKS.md` | 1K / 10K / 100K decisions; concurrency per Section 15 |
| C3 | Security report | `docs/SECURITY_REVIEW.md` | OWASP ASVS level 1 |
| C4 | 3 design partners | `partners/*.md` | LOI signed |

**Phase C Gate:** Demo + benchmarks + security review + 3 LOIs.

---

### Phase D — Deliver (30 days)
**Goal:** First successful pilot + case study.

| ID | Task | Deliverable | Acceptance Criterion |
|----|------|-------------|----------------------|
| D1 | Onboard first partner | Setup + training | ≥1,000 decisions recorded |
| D2 | Case study | `docs/CASE_STUDY_001.md` | Documented result |
| D3 | Decision point | `docs/DECISION_POINT.md` | Pivot or scale decision |

**Phase D Gate:** 1 case study + 1 paid customer.

---

## 4. First 7 Days — Mandatory Daily Plan

Every AI agent must follow this exactly.

### Day 1 — Full Inventory
```bash
cd ~/Desktop/EnterpriseGuard
source .venv/bin/activate
pytest tests/ -v > docs/TEST_REPORT_$(date +%Y%m%d).txt 2>&1
ls tools/*.py | wc -l
wc -l tools/*.py | sort -n -r | head -20
```

**Deliverable:** `docs/INVENTORY.md`

### Day 2 — Document 1 Component
- Pick `hardware_identity.py`
- Write `docs/COMPONENTS/hardware_identity.md` (≤30 lines)

### Day 3 — Document 1 Component
- Pick `genesis_seed.py`
- Write `docs/COMPONENTS/genesis_seed.md`

### Day 4 — Document 1 Component
- Pick `innocence_chain.py`
- Write `docs/COMPONENTS/innocence_chain.md`

### Day 5 — Quick Start Draft
- Write `docs/QUICKSTART.md`
- Test from scratch on clean shell

### Day 6 — First Recipe
- Write `docs/RECIPES/01-bank-credit.md`
- Include working code + screenshot

### Day 7 — Commit + Tag
```bash
git add .
git commit -m "A: Add initial docs (A1-A3 partial)"
git tag v0.2.0-alpha
```

---

## 5. Tech Stack — LOCKED

**No additions without owner approval.** No exceptions.

| Layer | Technology | Status |
|-------|-----------|--------|
| Core language | Python 3.12 | Locked |
| Optional acceleration | Cython, C extension | Allowed only for optimization |
| Rust | Not allowed in Phase A/B/C | May be allowed in Phase D with approval |
| WASM | Not allowed until Phase B gate | |
| Databases | SQLite + JSON | Locked |
| Web framework | FastAPI (or http.server stdlib) | Locked |
| Frontend | HTML + vanilla JS | Locked |
| ML | ONNX (Python only) | Allowed in Phase C |
| CI | GitHub Actions | Locked |
| Docs | Markdown | Locked |
| Key storage | Local file (0600) + optional keyring | Locked |
| TSA strategy | 4-layer failover per Section 14 | Locked |
| Write engine | JSONL append (Phase A/B), SQLite+WAL (Phase C) | Locked |

---

## 6. What Is Forbidden (Anti-Scope)

Any AI agent must **refuse** to:

- ❌ Add ZKP, zk-SNARK, Noir, Halo2, EZKL
- ❌ Add blockchain beyond existing anchoring
- ❌ Add gRPC, Protobuf, tonic
- ❌ Add gRPC-based microservices
- ❌ Add Sled, PostgreSQL, Redis
- ❌ Add Solid.js, React, Vue
- ❌ Add Kubernetes, Docker Swarm
- ❌ Rewrite code in Rust
- ❌ Add Post-Quantum crypto
- ❌ Add ML models without Phase C approval
- ❌ Refactor "for cleanliness"
- ❌ Add features not listed in Section 3
- ❌ Delete or archive existing code
- ❌ Change `continuity/RULES.md`
- ❌ Change key files or baselines

**If asked to do any of the above → write to `docs/BLOCKERS.md` and stop.**

---

## 7. Success Metrics (Replaces Old Metrics)

**Forget "148 tests". Measure these:**

| Metric | Target |
|--------|--------|
| Time to first decision | < 5 minutes |
| SDK lines to create decision | ≤ 5 |
| Dashboard load time | < 2 seconds |
| API response time | < 100 ms |
| Quick Start steps | ≤ 10 |
| Recipes | 5 |
| FAQ questions | 50 |
| Documented components | 20 |
| Design partners | 3 |
| Paying customers | 1 |

---

## 8. Gate Rules (Do Not Skip)

Every phase has a gate. A gate is:

1. **Measurable** — Objective criteria.
2. **Binary** — Pass or fail.
3. **Blocking** — Cannot enter next phase without passing.

**If a gate fails:**
- Write blocker to `docs/BLOCKERS.md`
- Stop
- Wait for owner decision (proceed, fix, or pivot)

---

## 9. Commit Rules

Every commit must:

1. Reference a Task ID (`A1`, `B2`, `C3`, `D1`)
2. Include test or documentation change
3. Be signed with GPG (if configured)
4. Use format:
   ```
   <Task-ID>: <Short Description>

   What: <what changed>
   Why: <which plan task>
   Tests: <test output or N/A>
   ```
5. Example:
   ```
   A1: Document hardware_identity component

   What: Added docs/COMPONENTS/hardware_identity.md
   Why: Phase A, task A1
   Tests: N/A (docs only)
   ```

---

## 10. Reporting Requirements

Each AI agent must produce a **weekly report** in `docs/reports/week-YYYY-WW.md`:

```markdown
# Week Report — YYYY-WW

## Completed
- [Task ID]: [Description]

## In Progress
- [Task ID]: [Description] — [% complete]

## Blocked
- [Task ID]: [Blocker] — see docs/BLOCKERS.md

## Next Week
- [Task ID]: [Plan]
```

---

## 11. Authority

- **Owner:** Final decision on all changes.
- **This plan:** Authoritative source for task definitions.
- **`continuity/RULES.md`:** Authoritative source for operational rules.
- **If conflict:** `RULES.md` wins, but plan takes precedence for task scope.

**To modify this plan:**
1. Owner writes new version
2. Increments version number
3. Records change in `docs/PLAN_CHANGELOG.md`
4. All agents reload

---

## 12. The One Rule

> **If it is not in this plan — it does not exist.**

---

## 13. Key Management Architecture (Binding for B1)

The SDK MUST support the following key sources in order of priority:

### Priority 1 — Local File (Default)
- Path: `~/.enterpriseguard/keys/private_key.pem`
- Permission: `0600`
- Already exists in the project (see `tools/signing_backend.py`)
- Works out of the box. No configuration required.

### Priority 2 — OS Keyring
- Library: `keyring` (Python)
- Platforms: macOS Keychain, Linux Secret Service, Windows Credential Manager
- Activated by: `AAAC_KEYRING=1`
- Optional. Not required for MVP.

### Priority 3 — Remote KMS/HSM
- Existing backends in `tools/signing_backend.py`:
  - AWS KMS  → `AAAC_SIGNING_BACKEND=aws_kms`
  - Azure KV → `AAAC_SIGNING_BACKEND=azure_kv`
  - TPM      → `AAAC_SIGNING_BACKEND=tpm`
  - Local    → `AAAC_SIGNING_BACKEND=local` (default)
  - Mock     → `AAAC_SIGNING_BACKEND=mock` (tests only)
- Dormant code. Activated only by explicit env var.

### Priority 4 — Shamir-Sharded Keys
- Existing module: `tools/sibb_keys.py`
- Use: 3-of-5 reconstruction for high-security deployments
- Not required for MVP.

### SDK Configuration Contract
```python
from enterpriseguard import Client

# Default: local key
client = Client()

# Explicit key path
client = Client(key_path="/path/to/key.pem")

# Remote KMS
client = Client(
    backend="aws_kms",
    kms_region="eu-west-1",
    kms_key_id="arn:aws:kms:..."
)
```

### FORBIDDEN
- ❌ Generating keys silently in temp directories
- ❌ Storing keys in project repo
- ❌ Sending private keys over network
- ❌ Default to cloud KMS without explicit user action

---

## 14. TSA Failover Strategy (Binding for B2)

### The Rule
**No decision is ever blocked by TSA unavailability.**
The envelope is created immediately. The TSA token is filled in later.

### Four-Layer Fallback

**Layer 1 — Primary TSA**
- Default: `http://time.certum.pl`
- Timeout: 15 seconds
- Retries: 2

**Layer 2 — Failover Pool**
- Secondary providers:
  - FreeTSA: `https://freetsa.org/tsr`
  - DFN: `https://zeitstempel.dfn.de`
- Configurable via `AAAC_TSA_URLS`
- Timeout: 10 seconds each

**Layer 3 — Async Queue**
- If all TSAs fail:
  - Envelope status = `"tsa_pending"`
  - Envelope is valid and verifiable (chain + signature still work)
  - Background worker retries every 5 minutes for 24 hours
  - Once TSA succeeds: status → `"complete"`
- Storage: `tools/tsa_queue.jsonl`

**Layer 4 — Local Timestamp (Optional, Explicit Only)**
- Activated ONLY by `AAAC_ALLOW_LOCAL_TSA=1`
- Uses local system time + signature
- Token marked as `"local_timestamp"` NOT `"rfc3161"`
- Compliance report shows warning
- FORBIDDEN as default behavior

### Envelope Status Values
| Status | Meaning |
|--------|---------|
| `complete` | RFC3161 token attached, verified |
| `tsa_pending` | Waiting for TSA, retrying |
| `tsa_failed` | 24h elapsed, admin action required |
| `local_only` | Local timestamp used (opt-in) |

### FORBIDDEN
- ❌ Blocking decision creation on TSA failure
- ❌ Silently dropping TSA token
- ❌ Pretending a local timestamp is RFC3161
- ❌ Retrying indefinitely without limit

---

## 15. Storage Concurrency Strategy (Binding for B, C)

### Three-Tier Storage Model

**Tier 1 — Hot (Phase A/B): JSONL Append**
- File: `decisions-YYYY-MM-DD.jsonl`
- Open with: `O_APPEND | O_CREAT | O_WRONLY`
- Atomic per-line writes (POSIX guarantees <4KB atomic on same FS)
- No locks needed. No contention.
- For writes: **this is the default engine**.

**Tier 2 — Query (Phase C): SQLite + WAL**
- Required PRAGMA settings:
  ```
  PRAGMA journal_mode = WAL;
  PRAGMA synchronous = NORMAL;
  PRAGMA busy_timeout = 5000;
  PRAGMA wal_autocheckpoint = 1000;
  ```
- One write connection, multiple read connections
- WAL allows concurrent reads + 1 writer without blocking
- Read-only connections opened with `mode=ro`

**Tier 3 — Scale (Phase D+, only if needed): PostgreSQL**
- Trigger conditions (BOTH must be met):
  - > 1,000,000 decisions/month
  - > 10 concurrent writers
- Not before. Not in Phase A/B/C.

### Mandatory Rules

1. **Never use SQLite without WAL mode.** Default DELETE mode locks readers.
2. **Never share a connection across threads.** Each thread has its own connection.
3. **Never hold a transaction open during network I/O.**
4. **Always use `busy_timeout`.** Default is 0 (fails immediately).
5. **For >100 concurrent writes/second: use JSONL, not SQLite.**

### Benchmark Requirement (C2)
The 100K decision test must:
- Run with 10 concurrent writers
- Show zero `database is locked` errors
- Show p99 write latency < 50ms

---

**— End of Execution Plan —**
```
