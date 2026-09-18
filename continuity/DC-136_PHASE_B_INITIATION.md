# DC-136: Phase B Initiation — Python SDK

**Date:** 2026-09-18
**Owner:** Biss
**Status:** APPROVED
**Predecessor:** Phase A Gate PASS (commit b8729cb, 2026-09-17)

---

## Context

Phase A (Understandability) is COMPLETE:
- A1: 22 components documented (DC-135 tiered standard)
- A2: QUICKSTART with verified commands
- A3: 5 recipes (commit 92aef19)
- A4: 50 FAQ questions (commit 0d1257c)
- Gate A: PASS (fresh clone test, GATE_A_ANSWERS.md)

Per EXECUTION_PLAN.md Section 3, Phase B may now begin.

---

## Decision

**Phase B is initiated** with the following scope (per EXECUTION_PLAN v2.3):

**Target:** Python SDK — `pip install enterpriseguard`
**Acceptance:** Create a decision in <=5 lines of Python

**Binding constraints (already in EXECUTION_PLAN):**
- Section 13 — Key Management Architecture (local file, keyring, KMS, Shamir)
- Section 14 — TSA Failover (4-layer, never blocks decision creation)
- Section 15 — Storage Concurrency (JSONL for Phase B, SQLite+WAL deferred)

**Task sequence:**
1. B1.8 — Signing backend reference audit (read-only)  ← first
2. B1.9 — Packaging boundary decision
3. B1.10 — SDK interface design
4. B1.x — Implementation

**Rule:** No code is written until the packaging boundary is decided.
Audit before mutation.

---

## Architectural guards

- Canonical implementation: `src/enterpriseguard`
- Root `enterpriseguard/`: compatibility boundary only
- Protected paths: `adie/`, `intelligence/`, `src/enterpriseguard/adie/`, `src/enterpriseguard/intelligence/`
- No changes to `pyproject.toml` before B1.9 is approved
- No new module under `src/` before the boundary is decided

---

## References

- EXECUTION_PLAN.md v2.3 Section 3 (Phase B)
- continuity/GATE_A_ANSWERS.md
- continuity/DC-133_PLAN_RECONCILIATION.md
- continuity/DC-135_A1_DOC_LENGTH_REVISION.md

**Approved by:** Biss (Owner)
**Effective:** 2026-09-18
