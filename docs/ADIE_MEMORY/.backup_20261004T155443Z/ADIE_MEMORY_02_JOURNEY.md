# ADIE — Journey

**Purpose:** Complete forensic journey from P0 (Repository audit) to
P-STEP-06.1 (Authority Model amendment).

---

## Phase P0 — Forensic Baseline

**Goal:** Understand what actually exists, before any decision.

### P0-STEP-01 — Repository Shape

**Findings:**
- 304 files in `src/`, 134 TSX, 77 test files.
- 4 commits head at L.4 (focus-visible extensions).
- Two Git repositories (root + `EnterpriseGuard/`).
- Docker compose runs `tools/sovereign_http_server.py` (stub, /health only).
- **Discovery:** 5 products coexist:
  1. `src/enterpriseguard/adie/` — Sovereign Reference Core (protected)
  2. PyQt6 desktop UI (works with ADIE)
  3. React frontend (isolated)
  4. AAAC Engine (`EnterpriseGuard/`) — separate pitch product
  5. HTTP API (`src/enterpriseguard/api/`)

### P0-STEP-02 — Python Backend & Integration Surface

**Findings:**
- `sovereign_http_server.py` = 109 lines, only `/health`. Production stub.
- `src/api/server.py` = 22KB, real routes: `/v1/health`, `/v1/decisions`,
  `/v1/verify`.
- **SDK uses `X-ADIE-Key` auth; frontend doesn't know about it.**
- **No `fetch()` calls in frontend production code.**
- Frontend `ApiClient` is defined but never instantiated in production.
- Coverage report: 96.26% statements / 53.49% functions — **frontend only**.

### P0-STEP-03 — Internal Documentation Survey

**Findings:**
- 145 decision cards (DC-028 to DC-145).
- 19 permanent rules.
- `EXECUTES_SECURITY_ACTIONS = False` in 6 source files.
- ADIE = Adaptive Defense Intelligence Engine (GLOSSARY).
- Pipeline: `Event → State → Prediction → Policy → Decision → Execution Manifest`.
- Phase A, Phase B, C1 all completed.
- C2/C3/C4 blocked historically; later resolved.

### P0-STEP-04 — Frontend/Backend Integration Intent

**Findings:**
- Frontend contracts (`decision.contract.ts` etc.) **mirror ADIE concepts**
  in naming but not structure.
- `Decision` in frontend = UI narrative.
- `DecisionContract` in Python = security contract.
- **PyQt6 UI works with ADIE; React does not.**
- Frontend built with 12 phases (A→L) without touching a real backend.

### P0 — Key Conclusions

- **CONFIRMED:** ADIE is real, mature, disciplined.
- **CONFIRMED:** Frontend and Python do not connect.
- **REFUTED (old assumption):** "No backend exists."
- **NEW QUESTION:** Why does `/v1/decisions` return `authorized=True` by default?

---

## Phase P-STEP-01 — Read-Only Reconnaissance

**Goal:** Determine what the SDK actually produces.

**Method:** Read-only inspection of SDK, signing, decision contracts, API,
tests, frontend contracts.

**Findings:**
- `SignedDecision` = `{contract, signature_hex, signed_at, backend, signed_payload_hash}`.
- `DecisionContract` = `{decision_id, evaluation_id, policy_id, action, status, authorized, created_at, expires_at, target_resource_id, parameters, provenance_hash}`.
- **H1 REFUTED:** artifact doesn't carry evidence/authority/policy references.
- **H2 CONFIRMED:** `verify_report.py` verifies adversarial reports, not
  decision certificates.
- **H3 PARTIAL:** offline verifier primitives exist; no deliverable artifact.
- **H4 REFUTED:** no evidence-discoverable chain from claim to evidence.

**Critical discovery:**
`Client.decide()` calls `_PolicyEvaluationAdapter(allowed=True,
decision_score=1.0)`. This bypasses `ADIEPolicy.evaluate()` entirely.

**Also discovered:**
- Two `canonicalization.py` files (identical hash).
- `jcs` (RFC 8785) is installed but unused in SDK.
- Two signing systems: RSA/ECDSA for decisions, Ed25519 for reports.

---

## Phase P-STEP-02 — Missing-Loop Reconnaissance

**Goal:** Trace the chain:
`Input → Policy → Evidence → Authority → Decision → Manifest → Certificate → Verifier`

**Findings:**

| Layer | Exists | Isolated |
|---|---|---|
| Input | ✅ | — |
| Policy Evaluation | ✅ (`adie/policy.py`) | Bypassed by SDK |
| Evidence | ✅ (`PolicyEvidence`, `DecisionEvidence`) | Not in SignedDecision |
| Authority | ✅ (`ExecutionAuthorization`) | Not linked to SDK |
| Decision | ✅ × 2 systems | Same name, different meaning |
| Execution Manifest | ✅ (30+ fields) | Not used by SDK or API |
| Certificate | ✅ (`SignedDecision`) | Signs only `{contract, signed_at}` |
| Verifier | ✅ × 4 | None check claim validity |

**Classification:**
- Category (4): **Issuance path that creates claims stronger than its evidence.**
- Sub-symptom: **Architectural divergence** — two `DecisionContract` classes
  with same name, different fields.

**All U1–U6 resolved:**
- U1: `ADIEPolicy` produces `PolicyEvaluation` without evidence refs.
- U2: `ExecutionManifest` cannot be signed by SDK.
- U3: API doesn't accept `ExecutionManifest`.
- U4: `/v1/verify` uses `Client.verify`.
- U5: `PolicyEvaluation` structure fully documented.
- U6: `adie/decision.py` uses a different API than `decision/contracts.py`.

---

## Phase P-STEP-03 — Design Intent Reconnaissance

**Goal:** Was the split intentional or an accident?

**Findings:**
- **DC-139 §D7 states explicitly:** "No policy engine (policy is passed as
  intent string)."
- **DC-140 does not warn** about semantic escalation in naming
  `/v1/decisions`.
- **DC-141 dashboard** shows `authorized` column with no context.
- **`ExecutionManifest` is not mentioned in any DC-136 through DC-141.**
- **`allowed=True` was intentional**, not inherited.

**Semantic analysis:**
`Decision` means 4 different things across documents:
1. DC-136: event (any SDK product)
2. DC-139: `DecisionContract` carrying `authorized=True`
3. DC-140: signed artifact from `/v1/decisions`
4. `DECISION_TRUST_LAYER`: two levels (Signed Decision ≠ Decision Proof)

**Two-level distinction documented:**
> V1 = Signed Decision Proof
> V2 = Decision Proof (with evidence, state, policy, authority)

**Conclusion:**
- **Alignment = YES** (implementation matches design).
- **Fitness for Proof-of-Claim = NO** (design itself escalates semantics).

**Recommended path:** D (Semantic Reframing + Authority Unification).

---

## Phase P-STEP-04 — Decision Phase (Design)

**Goal:** Decide the architectural direction.

**Decision: D+ adopted.**

D+ means:
1. Reframe V1 as `SignedIntent` (assertion layer).
2. Preserve `DecisionContract` name for the canonical layer.
3. `/v1/intents` for V1; `/v1/decisions` reserved for V2.
4. Compatibility shim for legacy `/v1/decisions`.
5. New invariants: `Assertion ≠ Authority`, `Signature ≠ Authority`,
   `Integrity ≠ Validity`.
6. `ExecutionManifest` becomes architectural, not optional feature.
7. Authority becomes first-class entity.
8. No code changes until full decision phase complete.

**New invariants (6-8).**

**Authority ladder** proposed (later revised as entity lifecycles, not one
ladder).

---

## Phase P-STEP-05 — Entity Model, Lifecycles, Lineage

**Goal:** Design the entity model.

**Decisions:**
- **12 entities** across 4 layers (Perception, Evaluation, Decision,
  Execution).
- **Each entity has its own lifecycle** — no shared state machine.
- **Transition Graph** between entities, not within one entity.
- **Decision Lineage** = primary trust artifact.
- **Causal sufficiency**, not association.

**Amendments adopted (by Owner):**
1. Invariant 9: Lineage is the *trust* artifact; DecisionContract remains
   the operational output.
2. Invariant 7: Manifest required iff external execution obligation
   declared (not by decision name).
3. Invariant 8: Prediction absence is a policy-derived **fact** (NOT_REQUIRED
   | REQUIRED_SATISFIED | REQUIRED_MISSING).
4. س6: Conceptual reclassification YES; in-place rename NO.
5. SIBB stores two distinct semantic types (Evidence vs Authority).
6. Lineage answers "causally sufficient" not "associated with".

**Adopted as Invariants 9-12.**

---

## Phase P-STEP-06.1 — Authority Model (Design)

**Goal:** Design the Authority subsystem.

**Owner decision:** B — **Ledger above SIBB**.
Decision Ledger ─refs→ SIBB
(canonical events) (immutable artifacts)
text


**Authority Model proposed:**
- `AuthorityGrant` = first-class entity with 20+ fields.
- Chain of delegation with `parent_grant_ref`.
- Time model: `granted_at`, `effective_from`, `expires_at`, `revoked_at`.
- Scope = resource patterns × action types × environments × tenants.
- Constraints = approval level, execution mode, time windows, rate limits,
  co-signers.
- `AuthorityProof` = runtime evaluation, stored in SIBB, referenced by
  `DecisionContract`.
- 8 failure modes documented.
- Conflict resolution: fail-closed (most restrictive wins).

**Owner amendments (5 points):**

1. **`policy_basis_ref` is not retroactive.** Grant is evaluated against
   the policy version under which it was issued, plus any explicit
   subsequent invalidation. `POLICY_OBSOLETE ≠ POLICY_INVALIDATED_GRANT`.

2. **Authority resolution is policy-defined, deterministic, fail-closed.**
   No heuristic "strongest grant." If no resolution rule → `AMBIGUOUS` →
   no `DecisionContract`.

3. **Grant references Governance directly** via `policy_basis_ref` +
   `policy_version` + `policy_hash`. No intermediate abstraction.

4. **`Approval` ≠ `AuthorityGrant`.** Provisional: `Approval` is a separate
   entity, likely referenced by grant constraints. To be confirmed after
   Ledger design.

5. **Trust Anchor ≠ genesis key.** Root is institutional (Charter +
   keys, or threshold). To be confirmed.

**Additional (Owner):** `Authority ≠ Capability`. Grant is not a bearer
token; it's proof-of-grant. Use of authority at a specific time is
`AuthorityProof`.

**Response to amendments (pending):** see `05_OPEN.md`.

---

## Summary of Investigation

**Total steps:** 6 major phases, 20+ sub-steps.

**Key findings (chronological):**
1. Repository is much more mature than expected.
2. V1 contains a **semantic escalation** (`authorized=True` with no
   policy evaluation).
3. Design admits this (DC-139) but API naming contradicts it.
4. D+ adopted: reframe V1, preserve V2 name, make Authority first-class.
5. Entity Graph adopted (12 entities, independent lifecycles).
6. Authority Model designed; 5 amendments adopted.

**What has NOT happened:**
- No code changes.
- No final spec.
- No B.2 implementation.
- No certificate issued.
- No verifier built.

---

**End of JOURNEY.**
