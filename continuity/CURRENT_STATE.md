# EnterpriseGuard ADIE — Current State

## Current Checkpoint — ADIE-P0.10-R3

**Last updated:** 2026-09-17
**Current phase:** Gate 0 Governance Reconciliation
**Governance decision:** P0.9-F Owner Resolution — **RETAIN / DO_NOT_RESTORE**
**Canonical authority:** `src/enterpriseguard`

### Current Objective

Reconcile the repository governance records with the already-executed
P0.9-F package-convergence outcome, preserve the historical W005 and
forensic evidence, then perform the final strictly scoped **P0.10-R4**
Gate 0 re-audit.

The current Gate 0 state remains **BLOCKED** until the governance records
are reconciled and the R4 re-audit passes.

## Current Checkpoint — ADIE-P0.10-R5 CLEARED

**Last updated:** 2026-09-17
**Current phase:** Phase 0 — Market Signal Verification
**Gate 0 status:** ✅ CLEARED (P0.10-R5, Qwen independent re-audit)
**Governance decision:** P0.9-F Owner Resolution — RETAIN / DO_NOT_RESTORE
**Canonical authority:** `src/enterpriseguard`

### Current Objective

Execute Phase 0 signals (S1–S5) to validate market need before Phase A.
S1, S3 complete. S2 partial. S4, S5 pending. See "Phase 0 — Market Signal Progress" section below.
---

# 1. Working-Tree Corruption Incident

During packaging work, an unexpected working-tree corruption event was detected.

Observed state:

* approximately 220 files appeared modified;
* `tools/innocence_chain.py` had been reduced from approximately 686 lines
  to approximately 50 lines;
* five protected ADIE/intelligence files were reported as modified;
* `git HEAD` remained clean.

The corruption was determined to be **uncommitted working-tree damage** rather
than committed repository history.

### Recovery

The corrupted working tree was restored under owner authority:

```text
git restore .
```

Forensic evidence was preserved before/around recovery under:

```text
/tmp/forensics_20260916/
```

The expected `tools/innocence_chain.py` implementation was restored to
approximately 686 lines.

### Recovery Validation

After recovery:

* critical `tools/` files were checked;
* the package installed successfully in editable mode;
* the configured non-UI test suite passed;
* authorized packaging changes remained identifiable;
* protected ADIE/intelligence implementations were not deliberately migrated
  as part of W005.

---

# 2. W005 Packaging State

## W005 Status

**Status: Pending final closure**

The packaging/recovery gate passed its substantive technical validation,
but final staging, commit, and post-commit closure remain pending.

Verified:

* `pyproject.toml` exists and was structurally validated.
* Package name: `enterpriseguard`
* Package version: `0.2.0`
* Authoritative version source: `VERSION`
* Canonical non-protected implementation target: `src/enterpriseguard`
* Build backend: `setuptools.build_meta`
* Python requirement: `>=3.12`
* `pytest.ini` uses `pythonpath = src`
* Root `enterpriseguard/` compatibility surfaces were retained where
  applicable.
* Protected ADIE/intelligence implementations were not intentionally migrated.
* `enterpriseguard==0.2.0` was successfully installed in editable mode.
* The configured non-UI test suite passed with **178 tests**.
* `tests/test_ui.py` was intentionally excluded because the root and src UI
  implementations remain materially different and the Qt runtime boundary is
  unresolved.
* `DC-132` was recorded.
* Forensic evidence from the working-tree corruption incident was preserved.

Still pending for W005:

1. Ensure Lesson 11 is present in `continuity/LESSONS_LEARNED.md`.
2. Perform the final working-tree integrity gate.
3. Review the exact authorized staging set.
4. Stage only authorized files.
5. Create the W005 commit.
6. Run the post-commit verification.
7. Mark W005 formally closed.

W005 closure is a separate engineering task and must not be conflated with
Gate 0 certification.

---

# 3. P0.9-F Package Convergence State

## P0.9-F Outcome

P0.9-F was executed in Git by commit:

```text
8ee5e24
```

The commit explicitly retired the following four root duplicate
implementations:

```text
enterpriseguard/decision/contracts.py
enterpriseguard/monitors/integrity_monitor.py
enterpriseguard/response/contracts.py
enterpriseguard/security/prompt_security_advanced.py
```

These four implementations are intentionally **absent from the current
working tree** and must **not** be restored.

### Owner Decision

The owner decision for P0.9-F is:

```text
RETAIN
DO_NOT_RESTORE
canonical_authority = src/enterpriseguard
```

This means:

* retain the P0.9-F architectural outcome;
* treat `src/enterpriseguard` as the canonical implementation authority;
* do not restore the four retired root duplicates;
* preserve root package compatibility boundaries;
* preserve remaining root-only fallback modules where applicable.

This is a narrowly scoped package-convergence exception to the general rule
against deleting existing working code.

It does not authorize unrelated deletion, cleanup, archival, or future
retirement of working repository code.

Any future retirement of tracked implementation code requires a separately
documented owner decision.

---

# 4. Canonical Package State

## Canonical Target

The canonical non-protected implementation target is:

```text
src/enterpriseguard/
```

Validated non-protected canonical surfaces include:

```text
enterpriseguard.decision.contracts
enterpriseguard.response.contracts
enterpriseguard.monitors.integrity_monitor
enterpriseguard.security.prompt_security_advanced
```

Focused validation established:

* Decision contracts: passed
* Response contracts: passed
* Integrity monitor: passed
* Prompt security: passed
* Consolidated focused validation: **27/27 passed**

## Root Compatibility Policy

The repository-root:

```text
enterpriseguard/
```

remains a compatibility/runtime boundary where applicable.

The four audited duplicate implementations listed in P0.9-F are no longer
part of that compatibility boundary because they were explicitly retired
by commit `8ee5e24`.

Root package initializers remain available as compatibility boundaries, and
remaining root-only modules may continue to provide fallback compatibility
where applicable.

The following rule remains in force for future repository changes:

Any further removal or deprecation of working code requires:

1. consumer inventory;
2. migration evidence;
3. focused validation;
4. explicit owner approval;
5. a separate governance decision.

---

# 5. Package Resolution Model

The repository uses `src` as the configured canonical package authority while
retaining root compatibility behavior.

### Packaging Authority

`pyproject.toml` establishes the package directory as:

```text
src
```

and setuptools package discovery is configured from:

```text
src
```

### Test Authority

`pytest.ini` establishes:

```text
pythonpath = src
```

Under the configured packaging and test environment, the validated
non-protected canonical surfaces resolve from:

```text
src/enterpriseguard
```

The repository also retains root compatibility boundaries for legacy or
fallback resolution where applicable.

The package model is therefore:

```text
Canonical implementation
        ↓
src/enterpriseguard
        ↓
packaging / pytest authority
        ↓
root enterpriseguard compatibility boundary
        ↓
remaining root-only fallback modules where applicable
```

The four overlapping root implementations retired by P0.9-F are not part of
that fallback boundary.

---

# 6. Packaging Metadata

`pyproject.toml` is now present.

Current design:

```text
Package name:
enterpriseguard

Version:
dynamic from VERSION

Version source:
VERSION

Build backend:
setuptools.build_meta

Python:
>=3.12

Package root:
src
```

Runtime dependencies currently declared for the package:

```text
cryptography==50.0.1
requests==2.34.2
regex==2026.9.10
```

Testing dependencies additionally required by the current pytest configuration:

```text
pytest-cov==7.1.0
coverage==7.16.1
```

### Package Boundary

The intended wheel/package boundary is explicitly limited to approved
non-protected EnterpriseGuard surfaces.

Protected packages are explicitly excluded:

```text
enterpriseguard.adie
enterpriseguard.adie.*
enterpriseguard.intelligence
enterpriseguard.intelligence.*
```

The repository-root compatibility tree is intentionally outside the primary
package installation boundary.

### Version Source

`VERSION` is the authoritative package-version source.

Current value:

```text
0.2.0
```

The version must not be duplicated as an independent source in other metadata.

---

# 7. Dependency State

`requirements.txt` is the bootstrap/environment dependency manifest.

The current runtime package dependencies are:

```text
cryptography==50.0.1
requests==2.34.2
regex==2026.9.10
```

The current test configuration also requires:

```text
pytest-cov==7.1.0
coverage==7.16.1
```

The repository's existing `tools/requirements.lock.txt` remains a separate
environment snapshot and is not treated as authoritative package metadata.

Its versions are not guaranteed to mirror `requirements.txt`.

---

# 8. UI Status

UI convergence is intentionally deferred.

Current implementations:

```text
enterpriseguard/ui/app.py
    ↓
PyQt5

src/enterpriseguard/ui/app.py
    ↓
PyQt6
```

The implementations are materially different.

Differences include:

* different Qt generation;
* different constructor signatures;
* different widget composition;
* different service wiring;
* different public surface;
* different internal view architecture.

The focused UI test was written against the root/PyQt5 implementation.

Therefore:

**Do not promote `src/enterpriseguard/ui/app.py` as a drop-in replacement.**

UI convergence requires a dedicated decision covering:

* Qt version;
* dependency installation;
* behavioral compatibility;
* test migration;
* runtime dependencies on protected ADIE/intelligence components.

---

# 9. BLOCKER-002

`BLOCKER-002` remains open.

It covers controlled ownership/migration decisions for the newly created or
currently untracked canonical non-protected `src` surfaces, including:

```text
src/enterpriseguard/decision/
src/enterpriseguard/monitors/
src/enterpriseguard/response/
src/enterpriseguard/security/
```

These files must not be:

* silently deleted;
* mixed into unrelated cleanup;
* committed without an explicit staging review.

BLOCKER-002 is a separate task from W005 closure and from the Gate 0
governance reconciliation.

---

# 10. Gate 0 Governance State

## P0.10-R3 Result

**Status: BLOCKED**

### P0.9-F Reconciliation

**Status: PASS**

The technical and historical P0.9-F outcome is confirmed by Git commit
`8ee5e24`.

### Remaining Governance Reconciliation

The following records still require reconciliation:

```text
continuity/CURRENT_STATE.md
tools/DECISIONS_LOG.md
continuity/DECISIONS_INDEX.md
docs/EXECUTION_PLAN.md
```

The required reconciliation is:

* record the P0.9-F owner decision;
* record the four explicitly retired root duplicate implementations;
* record `src/enterpriseguard` as canonical;
* record that root package initializers remain as the compatibility boundary;
* record that P0.9-F is a narrowly scoped owner-approved exception to the
  general no-deletion rule;
* remove obsolete statements claiming that the four retired duplicates are
  still present.

### Current Gate State

Gate 0 is **not yet certified**.

The next gate action is:

```text
P0.10-R4
```

which must be a strictly scoped read-only re-audit.

S3 remains stopped until R4 passes.

---

# 11. Governance Documentation State

### Historical Governance

**DC-132** was recorded for:

* P0.8-W005 packaging verification;
* working-tree corruption discovery;
* recovery;
* validation;
* remaining clarifications.

### P0.9-F Governance Reconciliation

The owner has approved the P0.9-F outcome:

```text
RETAIN
DO_NOT_RESTORE
canonical_authority = src/enterpriseguard
```

The dedicated P0.9-F governance record is now recorded in:

```text
tools/DECISIONS_LOG.md
```

and indexed in:

```text
continuity/DECISIONS_INDEX.md
```

The authoritative execution-plan exception must also be documented in:

```text
docs/EXECUTION_PLAN.md
```

The continuity files remain owner-maintained foundational documents.

---

# 12. Protected Security Boundaries

The following paths remain absolutely protected:

```text
adie/
intelligence/
src/enterpriseguard/adie/
src/enterpriseguard/intelligence/
```

Normal maintenance, packaging, migration, cleanup, or refactoring operations
must not:

* read;
* list;
* enumerate;
* modify;
* execute

files inside those directories.

Protected implementation details remain intentionally outside the current
Gate 0 re-audit unless explicitly authorized.

---

# 13. Current Critical Files

The current governance-critical file set includes:

```text
tools/TRUSTED_BASELINE.json
TRUSTED_BASELINE_SENTINEL.json
tools/integrity_baseline.json
integrity_baseline_sentinel.json
tools/hardware_identity.json
tools/genesis_baseline.json
VERSION
pyproject.toml
pytest.ini
requirements.txt
tools/DECISIONS_LOG.md
continuity/RULES.md
continuity/CURRENT_STATE.md
continuity/LESSONS_LEARNED.md
```

External private signing and identity keys must remain outside the repository
according to the permanent security rules.

---

# 14. Current Validation Evidence

Current and historical evidence is distributed across:

```text
tests/TEST_RESULTS.md
tests/ADVANCED_SECURITY_TESTS.md
tools/bandit_report.json
tools/pip_audit_report.json
docs/WHITEPAPER.md
/tmp/forensics_20260916/
```

### Latest W005 Validation

The authoritative reported result for the post-recovery W005 test gate is:

```text
178 tests passed
UI test intentionally excluded
```

Additional focused package-surface validation:

```text
27/27 focused canonical-surface tests passed
```

### P0.9-F Evidence

Git history records:

```text
8ee5e24 refactor(P0.9-F): retire 4 root duplicate implementations
```

The commit explicitly removed:

```text
enterpriseguard/decision/contracts.py
enterpriseguard/monitors/integrity_monitor.py
enterpriseguard/response/contracts.py
enterpriseguard/security/prompt_security_advanced.py
```

---

# 15. External Proof Layer

ADIE also maintains a separate externally demonstrable proof layer consisting
of:

* 148 adversarial validation tests;
* deterministic execution using a fixed seed;
* Ed25519-signed validation reports;
* public-key verification;
* MITRE ATT&CK threat-model mapping;
* GitHub Actions CI validation.

This proof layer is conceptually separate from the EnterpriseGuard/ADIE
runtime control-plane architecture.

It demonstrates validation and integrity.

It does not replace:

* canonical decision authority;
* governance;
* provenance;
* state;
* prediction;
* planning;
* execution boundaries;
* runtime safety controls.

---

# 16. Historical Strategic State — 2026-09-06

Earlier planning positioned AAAC as a proof layer above existing monitoring
tools and included a customer-discovery freeze.

That historical state is preserved for continuity.

The later packaging/recovery work represented by P0.8-W005 superseded the
engineering freeze for this specific technical gate.

---

## Strategic Update — 2026-09-06

* AAAC was positioned as a proof layer above existing monitoring tools.
* Customer discovery was launched.
* Market and technical responsibilities were separated.

## Technical Prototype Update — 2026-09-06

* Langfuse Cloud was used instead of self-hosted Langfuse V3.
* `tools/aaac_connector.py` was created.
* `agent_events_hash` was incorporated into innocence-chain calculations.
* Chain verification was restored.

## HTTP Server Update — 2026-09-06

* `/agents` was updated to read unique agent IDs.
* `/events` gained a capped limit.
* `/agents` was tested with `agent-123`.

## Phase 2 Technical Updates — 2026-09-06

* Duplicate avoidance added.
* RFC3161 field introduced.
* Dashboard endpoint added.
* Baselines regenerated.
* Chain regenerated and verified.

## RFC3161 / Dashboard / Open Verifier

* RFC3161 timestamping was improved.
* `tsa_provider` was recorded.
* Temporary dashboard authentication bypass was introduced for local testing.
* `tools/open_verifier.py` was created.
* Official verification remained functional.

## Compliance Documentation

Created:

```text
docs/AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md
docs/AAAC_LEGAL_USE_CASE.md
```

These remain draft/legal-support materials and are not a substitute for legal
review.

## Strategic Pivot — DC-86

AAAC was repositioned as a self-imposing compliance and trust layer.

Historical technical priorities included:

* dashboard authentication restoration;
* BYO-TSA;
* BYO-HSM;
* LangSmith/Langfuse connectors;
* standalone verification;
* compliance evidence reporting.

---

# 17. Historical Technical Decisions

## DC-87 — TSA Verification Field

Added `tsa_verified` to innocence-chain rings.

## DC-88 — Open Verifier

Standalone verifier attempt was unsuccessful; import-based verification was
retained.

## DC-89 — Compliance Report Endpoint

Added `/compliance-report` using chain verification.

## DC-90 — Native Connectors

Unified LangSmith/Langfuse fetch support was introduced.

## DC-91 — AAAC CLI

Created fetch → store → generate-ring → verify pipeline.

## DC-92 — Duplicate Avoidance

Existing trace IDs were skipped.

## DC-93 — AAAC README

Created `README_AAAC.md`.

## DC-94 — TSA Verification Improvement

Extended RFC3161 verification support.

## DC-95 — Strict TSA Verification

CA-chain verification was introduced.

## DC-96 — Dashboard Enhancement

Dashboard expanded with chain, integrity, TSA, agents, and events.

## DC-97 / DC-98 — Signing Backend

Local RSA and mock signing modes were introduced.

## DC-99 — Cloud Adapters

AWS KMS and Azure Key Vault adapter code was added.

## DC-100 — HSM/TPM

Dormant HSM/TPM support was added but not fully hardware-tested.

## DC-101 / DC-102

TSA failover and signing-backend tests were added.

## DC-103..DC-107

* TSA improvements;
* signing tests;
* Bandit cleanup;
* Docker support;
* SQLite event store.

## DC-108 — Dynamic Compliance Engine

Rules-based compliance evaluation was introduced.

## DC-109 — Sovereign Verifier UI

Static browser verifier was created.

## DC-110 — Key Reset

Keys and chain were regenerated and revalidated.

## DC-111 — Blockchain Anchoring

Local and Sepolia anchoring prototypes were completed.

## DC-112 — Advanced Compliance Engine

Rules-based compliance logic was expanded.

## DC-113 — Sepolia Deployment

Anchor deployment was recorded on Sepolia.

## DC-114 — HTML Verifier Deferred

HTML verifier issues remained deferred.

## DC-116 — Open Verifier Reverted

Working import-based verifier was restored.

## DC-117 / DC-118 — ECDSA

ECDSA support and benchmarking were completed.

## DC-120 — Key Backup

`tools/backup_keys.py` was implemented using `age`.

---

# 18. Historical Sovereign Reference Core State

The five original Sovereign Reference Core components were recorded as complete:

1. `hardware_identity.py`
2. `genesis_seed.py`
3. `relational_memory.py`
4. `distributed_proof.py`
5. `innocence_chain.py`

Historical security coverage included:

* DoS on Integrity Monitor
* Concurrency & Load
* TOCTOU
* Chain Spoofing
* Hard Fork / Chain Splitting
* Supply Chain analysis
* Mutation Fuzzing
* DDoS / Resource Exhaustion
* Time Spoofing
* Resource Starvation
* Cryptographic Collision Simulation
* Genesis Signature
* Sovereign Installer
* Centralized path management
* dimensional history collection

---

# 19. Historical SIBB Completion

The following components were recorded as complete:

| Component                  | File                                  | Tests | Status   |
| -------------------------- | ------------------------------------- | ----: | -------- |
| SIBB Storage               | `tools/sibb_storage.py`               | 19/19 | Complete |
| SIBB Distributed Storage   | `tools/sibb_distributed.py`           | 23/23 | Complete |
| SIBB Key Management        | `tools/sibb_keys.py`                  | 29/29 | Complete |
| SIBB CLI                   | `tools/sibb_cli.py`                   | 17/17 | Complete |
| SIBB-Innocence Integration | `tools/sibb_innocence_integration.py` | 15/15 | Complete |

Historical governance decisions:

```text
DC-122
DC-123
DC-124
DC-125
DC-126
```

---

# 20. Historical Kernel Protection State

## DC-127 — 2026-09-08

Adopted `chattr +i` with mandatory-access-control considerations.

eBPF prototype was deferred due to compatibility issues.

## DC-128 — 2026-09-08

Established `chattr +i` as the primary kernel-level WORM mechanism.

Documented that root with the relevant capability can bypass immutability.

## DC-129 — 2026-09-09

Tested:

```text
kernel_lockdown=confidentiality
```

Result:

* raw disk access was blocked;
* root could still remove immutability with `chattr -i`.

Conclusion:

Full root-proof protection requires stronger enforcement such as SELinux
or eBPF LSM in an appropriately controlled environment.

---

# 21. Next Actions

## Immediate — P0.10 Gate 0 Reconciliation

1. Record the P0.9-F owner decision in `tools/DECISIONS_LOG.md`.
2. Add the corresponding entry to `continuity/DECISIONS_INDEX.md`.
3. Record the narrowly scoped P0.9-F exception in `docs/EXECUTION_PLAN.md`.
4. Preserve the reconciled `CURRENT_STATE.md`.
5. Run **P0.10-R4** as a strictly scoped read-only audit.
6. Do not start S3 until Gate 0 is formally cleared.

## Separate W005 Closure

The original W005 closure sequence remains a separate engineering item:

1. Confirm Lesson 11.
2. Run the working-tree integrity gate.
3. Review exact authorized staging set.
4. Stage only authorized files.
5. Create the W005 commit.
6. Verify the committed state.
7. Mark W005 formally closed.

## Next Engineering Gate

After the applicable governance and Gate 0 work:

1. Resolve `BLOCKER-002`.
2. Validate package/wheel behavior in an isolated environment.
3. Validate runtime path precedence.
4. Decide the future lifecycle of remaining root compatibility surfaces.
5. Resolve the UI Qt strategy separately.
6. Preserve the protected ADIE/intelligence boundary.

## Market Track

S1 and S2 remain recorded as completed parallel market-evidence work.

Gate 0 was formally cleared on 2026-09-17 by P0.10-R5 read-only
re-audit (Qwen independent verification). S3 may now proceed.

## Longer-Term

* complete canonical package convergence;
* establish controlled production packaging;
* continue independent security validation;
* preserve the separation between proof artifacts and the ADIE runtime
  decision-control plane.
---
## Phase 0 — Market Signal Progress (2026-09-17)

### S1 — Big-4 reports on AI auditability
**Status:** ✅ COMPLETE (5/5 verified)
File: docs/P0_SIGNALS/S1_BIG4_REPORTS.md

### S2 — AI Governance jobs in EU financial institutions
**Status:** 🟡 PARTIAL (3/20 verified — paused)
File: docs/P0_SIGNALS/S2_AI_GOVERNANCE_JOBS.csv
Note: LinkedIn blocked in Syria; used ai-governance-jobs.com.
Paused at 3 verified jobs; target may be reduced to 10.

### S3 — Public statements on AI audit
**Status:** ✅ COMPLETE (3/3 verified)
File: docs/P0_SIGNALS/S3_CISO_POSTS.md
Angles covered:
  1. r/GRC — regulatory evidence (point-in-time vs continuous)
  2. r/Compliance — audit-defensible evidence (EU AI Act Art. 4)
  3. r/SaaS — architectural independence (audit layer vs model)

### S4 — Government/bank RFPs
**Status:** ⬜ NOT STARTED

### S5 — Named contacts (50-500 employees, EU BFSI)
**Status:** ⬜ NOT STARTED

---

# 22. Current Architectural Summary

EnterpriseGuard → ADIE is currently in a:

**controlled governance-reconciliation + packaging-hardening phase**

The current package direction is:

```text
P0.9-F approved outcome
        ↓
src/enterpriseguard = canonical authority
        ↓
four audited root duplicates = retired / DO_NOT_RESTORE
        ↓
root package initializers = compatibility boundary
        ↓
remaining root-only fallback modules = retained where applicable
        ↓
protected ADIE/intelligence = untouched
        ↓
P0.10-R4 = next certification gate
```

The audited non-protected package surfaces are converged on
`src/enterpriseguard` per P0.9-F/P0.9-C. Broader package
convergence remains pending for out-of-scope areas (UI Qt strategy,
BLOCKER-002, remaining root-only fallback modules).

Gate 0 is currently **BLOCKED pending governance reconciliation and R4
verification**.

The immediate objective is therefore:

```text
P0.10-R4
```

not S3.

The original W005 closure remains a separate historical engineering task and
must not be conflated with Gate 0 certification.

