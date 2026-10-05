# ADIE — Governance Charter

**File:** ADIE_MEMORY_15_CHARTER.md
**Version:** 1.0
**Status:** ADOPTED
**Date:** 2026-10-05
**Authority:** Owner sign-off (Section 8 below)
**Supersedes:** None (this is the founding charter)

---

## 1. What ADIE Is — One Paragraph

ADIE (Adaptive Defense Intelligence Engine) is a **Decision
Integrity Infrastructure**. It emits **portable, independently
verifiable decision certificates** for AI-driven decisions. A third
party can verify a certificate **offline**, **without internet**,
**without contacting the issuer**, and **without trusting the
issuer's software after issuance**. ADIE proves **integrity**, not
**truth**. This distinction is foundational and non-negotiable.

---

## 2. What ADIE Is Not

ADIE is **not**:
- An AI Governance platform.
- A compliance product.
- A dashboard.
- A SIEM / SOAR / XDR.
- An ML detector.
- A policy engine.
- A truth oracle.
- A certificate authority (yet).

ADIE is a **verification layer for decision records**.

---

## 3. Authority Order (Non-Negotiable)

```
Protocol Semantics
    >
Conformance Tests
    >
Security Model
    >
Reference Implementation
    >
Commercial Product
    >
UI
```

**Rules derived from this order:**
- The UI does not define meaning.
- The backend does not define the protocol.
- A single client does not define semantics alone.
- **No AI in this project has authority to declare a claim "proven."**
- All AI outputs pass through human review (Owner).

---

## 4. Ten Governing Principles

Inherited from `ADIE_MEMORY_05_OPEN.md` §7, elevated to charter status:

1. **Truth before convenience.**
2. **Alignment ≠ Fitness.**
3. **Unknown ≠ Pass ≠ Refuted.**
4. **No code until design closes.**
5. **Every claim testable.**
6. **Reframe, don't destroy.**
7. **Causation ≠ Correlation.**
8. **Fail-closed on ambiguity.**
9. **Signature ≠ Authority. Integrity ≠ Validity.**
10. **Assertion ≠ Authority.**

These principles apply to:
- Every architectural decision.
- Every document written.
- Every command issued.
- Every AI in the project.

---

## 5. Canonical Sources of Truth

When files conflict, this hierarchy resolves:

| Rank | Source | Path |
|---|---|---|
| 1 | Governance Charter | `docs/ADIE_MEMORY/ADIE_MEMORY_15_CHARTER.md` (this file) |
| 2 | Memory files | `docs/ADIE_MEMORY/ADIE_MEMORY_00` … `_14` |
| 3 | Decision log | `docs/ADIE_MEMORY/ADIE_MEMORY_03_DECISIONS.md` (DEC-XXX) |
| 4 | POC Definition | `docs/ADIE_MEMORY/ADIE_MEMORY_08_POC_DEFINITION.md` |
| 5 | Overview | `docs/ADIE-OVERVIEW-v4.md` |
| 6 | Scope Paper | `docs/ADIE-SCOPE-PAPER.md` |
| 7 | Continuity cards | `continuity/DC-XXX` (LEGACY — see §6) |

**Interpretation rule:** a later DEC does not override this Charter
without an explicit amendment (see §7).

---

## 6. Boundary with EnterpriseGuard

ADIE was carved out of the EnterpriseGuard codebase. The boundary
is hereby declared:

### 6.1 In ADIE Scope

- `poc/` — the POC artifacts (Python verifier, browser verifier, certificates)
- `docs/ADIE_MEMORY/` — the memory files (this is the canonical record)
- `docs/ADIE-OVERVIEW-v4.md`
- `docs/ADIE-SCOPE-PAPER.md`
- `poc/gate2/`, `poc/gate3/` — evidence and playbooks

### 6.2 In EnterpriseGuard Scope (Not ADIE)

- `src/enterpriseguard/` — the original product code
- `frontend/` — the React UI (isolated from POC)
- `tools/` — SIBB, dimensional, command_center (legacy operational)
- `EnterpriseGuard/` (uppercase nested dir) — legacy worktree

### 6.3 Legacy Continuity

The `continuity/DC-XXX` series is **LEGACY**. It is not deleted, not
migrated. It is historical reference. The `DEC-XXX` series in
`docs/ADIE_MEMORY/03` supersedes it for all ADIE work.

**Do not create new DC-XXX entries. Use DEC-XXX.**

### 6.4 Unresolved Boundary Questions

These are explicitly deferred, not ignored:

- AQ-12: Reconcile RSA/ECDSA + Ed25519 signing systems.
- AQ-16: Fate of legacy `/v1/decisions` endpoint.
- Migration of any `src/enterpriseguard/sdk/` component into POC scope.

Each will be resolved by a new DEC, not by silently editing code.

---

## 7. Amendment Process

This Charter may be amended only by:

1. A new `DEC-XXX` in `03_DECISIONS.md` that explicitly states:
   - Which section of this Charter is being amended.
   - Why.
   - What the new text replaces.
2. Owner approval recorded in that DEC.
3. A `Version` bump in this file's header (1.0 → 1.1, etc.).

**Forbidden:**
- Silent edits to this file.
- Amending the Authority Order without a formal DEC.
- Adding principles 11+ without formal DEC.

---

## 8. Owner Sign-Off

This Charter enters effect upon:

- [x] Owner reads it fully.
- [x] Owner approves (DEC-045 recorded).
- [x] An explicit `DEC-045 — Charter Adopted` written to
      `03_DECISIONS.md`.
- [x] This file is committed to git.

Until all four conditions are met, this file is **PROPOSED**, not
ADOPTED.

---

## 9. Immediate Consequences of Adoption

If adopted, the following rules apply immediately:

1. Any action that contradicts §3 (Authority Order) or §4 (Ten
   Principles) is **blocked**.
2. Any new document created in `docs/` must declare which of §5's
   sources it derives from.
3. Any work on `src/enterpriseguard/` or `frontend/` must be
   justified as either:
   - Legacy maintenance, OR
   - An explicit ADIE-adjacent task with a DEC.
4. The `continuity/DC-XXX` folder is frozen. No new entries.

---

## 10. Known Open Issues (Not Blocking Adoption)

These are recorded honestly:

- **No git tracking of ADIE work.** Currently untracked. Must be
  fixed before Gate 3 passes.
- **No Dependency Map.** The `ADIE-ARCHITECTURE-DEPENDENCY-MAP.md`
  is referenced but does not yet exist. It will be file 16.
- **Scope Paper is thin.** 102 lines vs. Overview 955. Should be
  brought to parity before Gate 3.
- **Desktop clutter.** `asdfgh/`, `zxcvb/`, `New Folder/` on
  `~/Desktop/` — not part of the project; separate cleanup task.
- **Two nested `.git` folders.** `EnterpriseGuard/.git` and
  `EnterpriseGuard/EnterpriseGuard/.git`. Should be unified.
- **Empty file `certum_tsa_ca.pem`** in `tools/`. Either populate
  or delete.

Each becomes a DEC-tracked task. None blocks Charter adoption.

---

**End of ADIE Governance Charter v1.0 (PROPOSED).**

**Next file to create:** `ADIE_MEMORY_16_DEPENDENCY_MAP.md`.
