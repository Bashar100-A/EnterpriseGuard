## Current Checkpoint — ADIE-B1.0

**Last updated:** 2026-09-18
**Current phase:** Phase B - SDK
**Current task:** B1 - Python SDK
**Phase A:** COMPLETE
**Gate A:** PASS
**B1 start authorization:** OWNER AUTHORIZED
**B1 status:** PRE-IMPLEMENTATION CONTRACT FINALIZATION
**Canonical authority:** `src/enterpriseguard`

### Current Objective

Begin Phase B/B1 under the authoritative `docs/EXECUTION_PLAN.md`.
Finalize the approved SDK contract and implementation boundary before
writing production code. No protected paths, deletions, archival, or
unapproved architectural expansion are authorized.


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

**Status: PASS**

### P0.9-F Reconciliation

**Status: PASS**

The technical and historical P0.9-F outcome is confirmed by Git commit
`8ee5e24`.

### Governance Reconciliation

Governance reconciliation is COMPLETE. The P0.9-F owner decision is explicitly recorded in DC-134.
The four root duplicate implementations are officially retired and marked DO_NOT_RESTORE.
The canonical authority is now strictly `src/enterpriseguard`. Root package initializers are retained
exclusively as a compatibility boundary. This action is a narrowly scoped, owner-approved exception
to the general no-deletion rule.
