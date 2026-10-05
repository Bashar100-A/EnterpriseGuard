# ADIE — Decisions Log

**Purpose:** All architectural decisions taken during P0 → P-STEP-06.1, with
rationale and status.

---

## Decision Format

Each decision:
- **ID:** sequential
- **Date:** in-conversation date
- **Phase:** which step
- **Decision:** what was decided
- **Rationale:** why
- **Status:** adopted / amended / superseded

---

## DEC-001 — Start Forensic Audit (P0)

**Phase:** 0
**Decision:** Before any fix or new design, conduct a read-only forensic
audit of the entire repository.
**Rationale:** Earlier reports (V1) contained unverified assumptions.
**Status:** ✅ Adopted; completed.

---

## DEC-002 — Forensic Baseline Scope = 6 Questions

**Phase:** 0
**Decision:** Limit P0 scope to 6 questions, deliverable = 10-page
`FORENSIC_BASELINE.md`.
**Rationale:** Prevent audit becoming infinite.
**Status:** ✅ Adopted; completed.

---

## DEC-003 — Do Not Trust Any Prior Report

**Phase:** 0
**Decision:** Treat earlier assessment as hypothesis, not fact.
**Rationale:** Preserve intellectual honesty.
**Status:** ✅ Adopted.

---

## DEC-004 — Read-Only Rule During Audit

**Phase:** 0
**Decision:** No modifications during P0 or any subsequent reconnaissance.
**Rationale:** Discovery must not contaminate the object being discovered.
**Status:** ✅ Adopted; still in force.

---

## DEC-005 — Rule 15 Exception for Protected Paths (P-STEP-01)

**Phase:** P-STEP-01
**Decision:** Owner authorizes reading `src/enterpriseguard/adie/` under
Rule 15 for this session only.
**Rationale:** H4 requires reading policy/decision/manifest internals.
**Status:** ✅ Adopted; scoped to session.

---

## DEC-006 — 4-Level Verification (Signature / Integrity / Provenance / Claim)

**Phase:** P-STEP-01
**Decision:** Any verification task must distinguish 4 levels.
**Rationale:** Signature validity ≠ Claim validity.
**Status:** ✅ Adopted.

---

## DEC-007 — `UNKNOWN ≠ PASS ≠ REFUTED`

**Phase:** P-STEP-01
**Decision:** Three distinct outcomes for any hypothesis.
**Rationale:** Prevent filling gaps with assumed goodness.
**Status:** ✅ Adopted; Invariant.

---

## DEC-008 — H1–H4 as Falsifiable Hypotheses

**Phase:** P-STEP-01
**Decision:** State testable hypotheses, not conclusions.
**Rationale:** Reasoning must be inspectable.
**Status:** ✅ Adopted.

---

## DEC-009 — `NOT TESTABLE ≠ REFUTED`

**Phase:** P-STEP-01
**Decision:** If a hypothesis cannot be tested due to upstream failure, mark
`NOT TESTABLE`, not `REFUTED`.
**Rationale:** Distinguish hypothesis failure from dependency failure.
**Status:** ✅ Adopted.

---

## DEC-010 — Design Intent vs Implementation Alignment

**Phase:** P-STEP-03
**Decision:** Alignment and Fitness are two orthogonal columns.
**Rationale:** Design can be aligned and unfit.
**Status:** ✅ Adopted.

---

## DEC-011 — D: Semantic Reframing + Authority Unification

**Phase:** P-STEP-03/04
**Decision:** Adopt D+ (reframe + unify).
**Rationale:** Fix at architectural level, not as rename.
**Status:** ✅ Adopted.

---

## DEC-012 — Preserve `DecisionContract` Name

**Phase:** P-STEP-04
**Decision:** `DecisionContract` preserved for canonical layer. Legacy
reframed as `SignedIntent`.
**Rationale:** Don't lose the target name.
**Status:** ✅ Adopted.

---

## DEC-013 — `SignedIntent` as Assertion Layer

**Phase:** P-STEP-04
**Decision:** V1 artifact renamed (conceptually) to `SignedIntent`.
**Rationale:** Assertion ≠ Authority.
**Status:** ✅ Adopted.

---

## DEC-014 — New Invariants (Assertion ≠ Authority, Signature ≠ Authority, Integrity ≠ Validity)

**Phase:** P-STEP-04
**Decision:** Add three invariants.
**Rationale:** Formalize the split.
**Status:** ✅ Adopted.

---

## DEC-015 — `/v1/intents` for V1; `/v1/decisions` for V2

**Phase:** P-STEP-04
**Decision:** V1 endpoint renamed; V2 endpoint reserved.
**Rationale:** Don't pollute future name.
**Status:** ✅ Adopted.

---

## DEC-016 — Compatibility Shim for Legacy

**Phase:** P-STEP-04
**Decision:** Legacy `/v1/decisions` becomes deprecated alias with warning.
**Rationale:** Don't break existing consumers; document the boundary.
**Status:** ✅ Adopted.

---

## DEC-017 — No Shared Lifecycle

**Phase:** P-STEP-05
**Decision:** 12 entities, each with its own lifecycle.
**Rationale:** Forcing one lifecycle on all is V1's original sin.
**Status:** ✅ Adopted.

---

## DEC-018 — Entity Graph, not Pipeline

**Phase:** P-STEP-05
**Decision:** Model as Entity Graph with typed transitions.
**Rationale:** Pipeline hides relationships; graph shows them.
**Status:** ✅ Adopted.

---

## DEC-019 — Decision Lineage as Primary Trust Artifact

**Phase:** P-STEP-05
**Decision:** Lineage is the trust artifact; `DecisionContract` is the
operational output.
**Rationale:** Trust comes from reconstrucibility, not from the artifact
alone.
**Status:** ✅ Adopted (amended in P-STEP-06).

---

## DEC-020 — Manifest Required iff External Obligation

**Phase:** P-STEP-05
**Decision:** Manifest required **iff** decision declares external execution
obligation.
**Rationale:** Preserve `Decision ≠ Execution`.
**Status:** ✅ Adopted.

---

## DEC-021 — Prediction Absence is Policy-Derived Fact

**Phase:** P-STEP-05
**Decision:** `PolicyEvaluation` records `NOT_REQUIRED | REQUIRED_SATISFIED |
REQUIRED_MISSING`.
**Rationale:** Absence must be provable.
**Status:** ✅ Adopted.

---

## DEC-022 — Conceptual Reclassification, Not In-Place Rename

**Phase:** P-STEP-05
**Decision:** Legacy `DecisionContract` becomes compatibility representation
for `SignedIntent`. No file rename.
**Rationale:** Preserve lineage of the legacy entity.
**Status:** ✅ Adopted.

---

## DEC-023 — SIBB Stores Two Distinct Semantic Types

**Phase:** P-STEP-05
**Decision:** SIBB stores Evidence and Authority artifacts. Shared integrity
layer; different semantic types.
**Rationale:** Prevent semantic conflation.
**Status:** ✅ Adopted.

---

## DEC-024 — Lineage Answers "Causally Sufficient"

**Phase:** P-STEP-05
**Decision:** Lineage answers "what facts and rules were causally
sufficient?" — not "what is associated?"
**Rationale:** Causation ≠ Correlation.
**Status:** ✅ Adopted.

---

## DEC-025 — B: Ledger Above SIBB

**Phase:** P-STEP-06.1
**Decision:** Adopt Option B (Ledger above SIBB).
**Rationale:**
- SIBB = artifact store.
- Ledger = event store.
- Lineage = reconstruction from both.
**Status:** ✅ Adopted.

---

## DEC-026 — Ledger is Not Just an Event Log

**Phase:** P-STEP-06.1
**Decision:** Ledger must model causal edges (caused_by, required_for,
satisfied_by, derived_from, produced, superseded, revoked_by).
**Rationale:** To distinguish causal edges from mere references.
**Status:** ✅ Adopted.

---

## DEC-027 — Authority Model v1 (proposed)

**Phase:** P-STEP-06.1
**Decision:** Adopt Authority Model with `AuthorityGrant`, chain, time
model, scope, constraints, `AuthorityProof`.
**Status:** ✅ Adopted with 5 amendments (see DEC-028 to DEC-032).

---

## DEC-028 — `policy_basis_ref` is not Retroactive

**Phase:** P-STEP-06.1
**Decision:** Grant evaluated against policy version under which it was
issued + explicit subsequent invalidation.
**Rationale:** Prevent temporal discontinuity.
**Status:** ✅ Adopted.

---

## DEC-029 — Authority Resolution is Deterministic, Fail-Closed

**Phase:** P-STEP-06.1
**Decision:** No heuristic "strongest grant." Policy-defined resolution.
If ambiguous → `AMBIGUOUS` → no `DecisionContract`.
**Rationale:** No general mathematical answer for "strongest."
**Status:** ✅ Adopted.

---

## DEC-030 — Grant References Governance Directly

**Phase:** P-STEP-06.1
**Decision:** `policy_basis_ref` + `policy_version` + `policy_hash`.
No intermediate abstraction.
**Rationale:** Prevent re-creating V1's identity problem.
**Status:** ✅ Adopted.

---

## DEC-031 — `Approval ≠ AuthorityGrant`

**Phase:** P-STEP-06.1
**Decision:** Provisional: `Approval` is a separate entity.
**Rationale:** Grant = who may do X. Approval = condition for specific case.
**Status:** ✅ Provisional; to confirm after Ledger design.

---

## DEC-032 — Trust Anchor ≠ Genesis Key

**Phase:** P-STEP-06.1
**Decision:** Root Authority derived from Trust Anchor (institutional,
charter-based).
**Rationale:** Single genesis key would just rename `authorized=True`.
**Status:** ✅ Adopted; details pending.

---

## DEC-033 — `Authority ≠ Capability`

**Phase:** P-STEP-06.1
**Decision:** Grant is proof-of-grant, not bearer token.
**Rationale:** Grant = may. Proof = did. Not same.
**Status:** ✅ Adopted.

---

## DEC-034 — AuthorityProof is Immutable

**Phase:** P-STEP-06.1
**Decision:** `AuthorityProof` referenced by `DecisionContract` is immutable.
Extension via new artifact, not modification.
**Rationale:** Historical decisions must remain reconstructible as of
issuance.
**Status:** ✅ Adopted.

---


---

## DEC-035 — Ledger / Event Model Adopted (P-STEP-06.2 v2.4)

**Phase:** P-STEP-06.2
**Decision:** The Ledger / Event Model design (P-STEP-06.2, v2.4) is adopted.

**Key claims:**
- Ledger topology = **hybrid** (linear within entity chain, DAG between decisions).
- Decision boundary = **primary-subject identity**, not time.
- `decision_id` allocated at `DECISION_INITIATED` event.
- Cross-chain events = two atomic events in one transaction.
- Event envelope with `event_class` (LIFECYCLE / RELATIONSHIP).
- `contract_ref` in `LIFECYCLE_EVENT` body points to `DecisionContract`.
- `payload_ref` = `{location_hint}` only; hash is authoritative.
- Causal edges in separate fields from informational refs.
- JCS (RFC 8785) for canonical serialization.
- Distinct domain prefixes per hash type (`ADIE:EVENT`, `ADIE:PAYLOAD`,
  `ADIE:CONTRACT`, `ADIE:EMISSION`).
- `prev_event_hash` **is included** in `event_hash`.
- Merkle construction = **RFC 6962** (Certificate Transparency), explicitly.
- Circular dependency resolved via **Solution C** (`DecisionContract` =
  content-only; fingerprint in SIBB; ref via link artifact).
- `emission_fingerprint` computed at **`DECISION_EMITTED`**; covers
  Construction + Emission segments only.
- **Content-Only Contract Principle** (§0.1): post-freeze outputs live in
  separate SIBB artifacts, never embedded in the contract.
- Multi-tenancy = one logical Ledger; `tenant_id` + `environment_id`
  mandatory on every event.
- `by_decision` returns exactly one chain (one fingerprint per decision).
- Reconstruction requires **Ledger + SIBB** (not Ledger alone).

**WORM ordering procedure (six steps, §5.5):**
1. Freeze contract content.
2. Compute `decision_contract_content_hash`.
3. Compute `emission_fingerprint`.
4. Store fingerprint in SIBB.
5. Store `contract-emission-link` in SIBB.
6. Record `DECISION_EMITTED` event with `contract_ref`.

**Documented discoveries:** 15 (see file 06 §4).

**Open questions:** OQ-06.2-1 → OQ-06.2-14 (13 questions; see file 06 §5).

**Depends on:** DEC-025, DEC-026, DEC-034.
**Supersedes:** none (first Ledger design).
**Full details:** `ADIE_MEMORY_06_P_STEP_06_2.md`.

**Rationale:**
- Fixes V1's "SDK issues claims without evidence" at the structural level.
- Provides a verifiable, offline-checkable lineage for every emitted decision.
- Names and enforces the WORM ordering — no artifact is amended.
- Lays the groundwork for P-STEP-06.3 (causal sufficiency) with explicit
  structural fields (`caused_by[]`, `required_for[]`, etc.).

**Status:** ✅ Adopted upon recording.



---

## DEC-036a — Four Questions of Decision-Causal Sufficiency

**Phase:** P-STEP-06.3 (Semantic Separation)
**Status:** ✅ Adopted.
**Related:** DCDS reclassified as **Decision-Derivation Proof Layer**
(not the framework for DCS). Framework choice deferred.

### Decision

Any causal-sufficiency claim about a Decision D MUST specify which of
the following four questions it answers:

| Q | Name | Target |
|---|---|---|
| **Q1** | Production | Why was D produced (issued)? |
| **Q2** | Justification | Why was D justified? |
| **Q3** | Authorization | Why was D authorized? |
| **Q4** | Optimality | Why was D preferred over alternatives? |

### Scope

- **Q1, Q2, Q3:** in scope for P-STEP-06.3.
- **Q4:** DEFERRED. Requires an objective function, alternatives,
  utility/regret semantics — outside the Proof-of-Claim scope.

### Consequences

1. No single causal-sufficiency claim may answer two questions at once.
2. A Decision may have different causal sets for different Q.
3. The umbrella term is **DCS**; each instance must state its Q explicitly.
4. **The unqualified term "causal sufficiency" MUST NOT be used as an
   ADIE claim.** ADIE uses **DCS** only for its project-specific,
   question-indexed notion.

### Neutral stage-wise definition of DCS

```
DCS(Q, S, D | M, C, T)
```

is a **declared claim** that the set `S` satisfies the **sufficiency
criterion** defined by:

- causal model `M`,
- causal context `C`,
- evaluation semantics `T`,
- question `Q`,

with respect to decision `D`.

**The causal model `M` is what defines** "contribution", "dependence",
"intervention", and "counterfactual" semantics. DCS itself does not
presuppose these definitions.

### Layered architecture

```
DCDS         ──► "Is D derived from S?"                 YES / NO
   │
Causal Model ──► "What does contribution/dependence mean?"  (per M)
   │
   ▼
DCS          ──► "Does S satisfy the declared sufficiency criterion?"
             ──► YES / NO / INDETERMINATE
```

DCDS is **not** the framework for DCS. DCDS is the **derivation proof
layer**.

### What This Decision Does NOT Determine

- The framework for the derivational layer — **DEC-036b** (deferred).
- The framework for the causal layer — **DEC-036c** (deferred).
- The algorithm for evaluating sufficiency — later.
- Whether Q4 is eventually adopted — later.

### Related Invariants (see file 01)

- **Invariant 17:** No causal sufficiency claim without explicit Q,
  model/version, context, evaluation semantics.
- **Invariant 18:** Never prove more causality than the declared model
  supports.
- **Invariant 19:** Corroboration ≠ causation.
- **Invariant 20:** Derivability ≠ Causal Sufficiency.
- **Invariant 21:** Computation correctness, derivation correctness, and
  causal sufficiency are distinct proof obligations.

### Related Concepts

- **DCDS** — Decision-Derivation Proof Layer. Handles "how was D
  derived?" question. **Not** the framework for DCS.
- **Causal Layer** — framework TBD. Handles "what made D the case?"
  question, operating on **derived representations**, not the
  historical record.

**Approved by:** Owner.
**Effective:** 2026-10-04.



---

## DEC-036a-4 — Partial Framework Dependence Admitted

**Phase:** P-STEP-06.3a (finding from Strategic Question S1)
**Status:** ✅ Adopted.
**Related:** P-STEP-06.3a v3.1 (proposed), §7.

### Finding

P-STEP-06.3a aimed to separate semantics from framework. The strategic
analysis (S1) concluded:

> Complete semantic separation is **impossible** for some terms.
> Specifically, three terms cannot be defined without committing to a
> framework:
>
> - **T4** (Causal Model M)
> - **T6** (Structural Causal Dependence)
> - **T7** (Instance Counterfactual Dependence)
>
> These require an explicit framework specifying:
> 1. A directed graph structure over variables.
> 2. Endogenous/exogenous partition.
> 3. Directional mapping functions.
> 4. An intervention/mutation operator.

### Consequence

- Nine terms (T1, T2, T3, T5, T8, T9, T10, T11, T12) are framework-
  independent and remain as defined in P-STEP-06.3a.
- Three terms (T4, T6, T7) are recorded as **framework-dependent**.
- Framework selection (a future decision) is therefore **not a
  downstream task**; it is a **co-requisite** for finalizing these
  three terms.

### DEC Numbering (Proposed)

| Number | Content | Status |
|---|---|---|
| DEC-035 | Ledger / Event Model | Recorded |
| DEC-036a | Four Questions of DCS | Recorded |
| DEC-036a-4 | Partial Framework Dependence | This decision |
| DEC-036b | Semantic Separation Adopted | Reserved |
| DEC-036c | Framework Selection | Deferred |
| DEC-036d | DCS Evaluation Algorithm | Deferred |

### What This Decision Does NOT Do

- Does not select a framework.
- Does not begin P-STEP-06.3b.
- Does not modify DEC-035 or DEC-036a.
- Does not authorize implementation.

### Status of the Framework Question

**Deferred.** P-STEP-06.3b is postponed pending the POC Definition
Document and its Gate 2 outcome.

**Approved by:** Owner.
**Effective:** 2026-10-04.



---

## DEC-036b — Semantic Separation Adopted (P-STEP-06.3a v3.1)

**Phase:** P-STEP-06.3a
**Status:** ✅ Adopted.
**Supersedes:** v3, v0 (preserved as .bak_).
**Related:** DEC-036a (Four Questions), DEC-036a-4 (Framework Dependence).

### Decision

The vocabulary of P-STEP-06.3a v3.1 is adopted as ADIE's authoritative
semantic foundation for decision-sufficiency work: **12 terms (T1–T12)**,
**6 proof obligations (O1–O6)**, **5 invariants (17–21)**.

### Key Content

- **12 terms:** Derivation, Justification, Authorization, Causal Model,
  Evaluation Context, Structural Dependence, Instance Counterfactual
  Dependence, DCS, Derivational Necessity, Actual Causal Contribution,
  Validity, Applicability.
- **6 obligations:** Computation, Derivation, Evidence, Policy
  Applicability, Authority, Causal Sufficiency Evaluation.
- **3 layers:** Provenance/Authority → DCDS → DCS Evaluator.
- **3 framework-dependent terms:** T4, T6, T7 (per DEC-036a-4).

### Distinctions Preserved

- Integrity ≠ Truth.
- Derivability ≠ Causal Sufficiency (Invariant 20).
- Corroboration ≠ Causation (Invariant 19).

### What This Decision Does NOT Do

- Does not select a framework (DEC-036c deferred).
- Does not advance P-STEP-06.3b/c.
- Does not authorize implementation beyond POC scope.

### Reference

Full text: `ADIE_MEMORY_07_P_STEP_06_3A_V0.md` (filename preserved for
historical stability).

**Approved by:** Owner.
**Effective:** 2026-10-04.



---

## DEC-037 — POC Execution Adopted (P-STEP-02)

**Phase:** P-STEP-02
**Status:** Adopted.
**Related:** DEC-036b (Semantic Separation), Directive PR-01 to PR-05.

### Decision

The POC execution (P-STEP-02) is adopted as the first operational
artifact of ADIE. It produces a standalone verifier, a signed
certificate fixture, and a 10-case test suite.

### Artifacts Produced

| Artifact | Location | Size |
|---|---|---|
| verify.py | poc/verify.py | 179 lines |
| certificate-001.json | poc/certificate-001.json | 2067 bytes |
| public-key-001.pem | poc/public-key-001.pem | 451 bytes |
| test_pstep02.py | poc/test_pstep02.py | 111 lines |

### Results

- 10/10 test cases pass (TC-01 to TC-10).
- Error codes E001-E010 implemented (E004, E008 reserved for P-STEP-03).
- No enterpriseguard import.
- No network access (verified via unshare -rn).
- No json.dumps(sort_keys=True) - uses JCS (RFC 8785).
- Standalone, offline, zero-trust.

### Trust Boundary

The POC proves Integrity Verification: the certificate has not been
altered since issuance, and the issuer's signed assertions are
cryptographically bound.

The POC does NOT prove Decision Truth: that the decision described
in the certificate actually occurred, or that any real-world
assertion is true.

### What This Decision Does NOT Do

- Does not select a framework (DEC-036c deferred).
- Does not advance P-STEP-06.3b/c or P-STEP-06.5.
- Does not authorize Cross-Language work.
- Does not modify DEC-035, DEC-036a, DEC-036a-4, or DEC-036b.

### Reference

Full POC: poc/ directory. Strategic context: file 09.

**Approved by:** Owner.
**Effective:** 2026-10-04.



---

## DEC-038 — Gate 2 PASS (External Developer Test)

**Phase:** P-STEP-02 (Gate 2)
**Status:** PASS
**Date:** 2026-10-04

### Evidence

An external developer (not the owner) ran the POC on a MacBook M2
(macOS ARM64, Python 3.11), a materially different environment from
the owner's (Ubuntu x86_64, Python 3.12):

- Test A (valid certificate) → VALID
- Test B (wrong key) → INVALID: E001_SIGNATURE_INVALID
- Test C (test suite) → 10/10 passed
- Time: 4 minutes
- No confusion, no errors

### Interpretation

Per ADIE_MEMORY_10_PRE_AUDIT_BLUEPRINT §1.1 (S1.1 Clean PASS):
all six expected input items present, all criteria met.

### What This Proves

- The verifier is portable across OS/architecture
  (Linux x86_64 → macOS ARM64).
- The verifier works on Python 3.11 (owner tested on 3.12).
- Instructions are sufficient for an independent developer.
- 10/10 in two different environments confirms real verification
  logic, not overfitting.

### What This Does NOT Prove

- That the idea is correct or valuable.
- That an auditor would find value (Gate 3).
- That the market exists (Gate 4).
- Anything about Decision Truth, causality, or policy correctness.

### Log

Verbatim response: poc/gate2/20261004-external-dev-macOS.txt

**Approved by:** Owner.
**Effective:** 2026-10-04.



---

## DEC-039 — Gate 2 Windows Finding: Portability Bug

**Phase:** P-STEP-02 (Gate 2 hardening)
**Status:** Fixed in POC v3 (pending Windows retest)
**Date:** 2026-10-04

### Discovery

An institutional tester (Windows 11, Python 3.12) ran the POC and
reported:

- Test A: `INVALID: E002_HASH_MISMATCH`
- Test B: `INVALID: E001_SIGNATURE_INVALID` (correct)
- Test C: 2/10 passed
- Verbatim: `INVALID: E002_HASH_MISMATCH (content_hash)`

Their diagnostic: Windows extraction converted LF to CRLF in
`certificate-001.json`, which altered the parsed content.

### What This Revealed

1. **Fail-closed worked correctly.** The verifier did not crash; it
   returned a specific error code.
2. **OS-portability was untested.** Our Linux + macOS tests passed,
   but Windows failed.
3. **The verifier read the file in text mode**, which is not
   OS-agnostic.

### Fix (POC v3)

- `verify.py` now reads the file as **raw bytes** (`read_bytes()`),
  with no newline translation.
- UTF-8 BOM stripped if present.
- Strict UTF-8 decode; failures produce E009.
- `SHA256SUMS` file added for pre-flight integrity check on any OS.
- `INSTRUCTIONS.md` includes a Step 0 for hash verification.

### Post-Fix Status

- All local tests pass again (10/10).
- Windows retest pending.

### Classification

- **Gate 2 evidence:** real-world portability bug, found externally.
- **Not a failure of the verifier's design** — the design correctly
  failed closed.
- **A failure of our testing coverage** — we did not test Windows.

### What This Does NOT Change

- No change to P-STEP-06.2.
- No change to DEC-037 (POC).
- No change to trust boundaries.
- The bug was in I/O, not in verification logic.

**Approved by:** Owner.
**Effective:** 2026-10-04.



---


---

## DEC-040 — Gate 2 Linux Confirmation (v3)

**Phase:** P-STEP-02
**Status:** PASS.
**Date:** 2026-10-04
**Missing slot filled:** This decision was reported earlier but not
recorded. Now recorded.

### Evidence

An external tester ran POC v3 on Linux x86_64 (Python 3.12):

- SHA256SUMS: 7/7 OK
- Test A → VALID
- Test B → INVALID: E001_SIGNATURE_INVALID
- Test C → 10/10 passed
- Test D (certificate-002) → VALID
- cryptography 50.0.2, jcs 0.2.1

### Why This Matters

1. POC v3 works on Linux — Windows fix did not regress Linux.
2. cryptography 50.0.2 (much newer than baseline 41.0.7) — wide
   version compatibility confirmed.
3. SHA256SUMS works externally.
4. Test D (second certificate) passes externally — not overfit.

### What It Does NOT Prove

- Windows v3 retest still pending (DEC-039).
- Decision Truth, causality, policy correctness.
- Anything about Gate 3 (Customer Truth).

**Approved by:** Owner.
**Effective:** 2026-10-04.

## DEC-041 — Rule PR-06: No External Modification of POC

**Phase:** P-STEP-02 (post-hardening)
**Status:** Adopted.
**Date:** 2026-10-04

### Incident

An external script (generated by another AI model) was applied directly
to `poc/` without review. It overwrote `verify.py` and `test_pstep02.py`,
the latter with a syntax error (`IndentationError`), breaking Test C.

The recovery restored the working `test_pstep02.py` from `external-test/`
and kept the new `verify.py` (196 lines, still < 200, still works).

### Rule Adopted

**PR-06: No external modification of poc/ without review.**

Any change to poc/verify.py, poc/test_pstep02.py, poc/certificate-*.json,
or poc/*.pem must pass through the review conversation before execution.

If review is not possible, the script must run on a copy (`.sandbox/`)
first.

### What Was Preserved

- verify.py 196 lines, fortified (read_bytes + BOM strip + SHA256SUMS).
- test_pstep02.py original 10-case suite restored.
- certificate-001.json, certificate-002.json intact.
- SHA256SUMS regenerated (10 files).
- Tarball v3 rebuilt (12 files, 10560 bytes).

**Approved by:** Owner.
**Effective:** 2026-10-04.



---

## DEC-042 — Cross-Language Equivalence Achieved

**Phase:** P-STEP-02 (hardening)
**Status:** Proven.
**Date:** 2026-10-05

### Discovery

The browser-based verifier (`visual-verifier-v2.html`) and the Python
verifier (`verify.py`) produce **byte-identical** hashes for both
certificate-001.json and certificate-002.json:

| Cert | Field | Python | Browser |
|---|---|---|---|
| 001 | Content Hash | sha256:e751b663...aa0d051 | sha256:e751b663...aa0d051 |
| 001 | Fingerprint  | sha256:6337c84b...5a1523 | sha256:6337c84b...5a1523 |
| 002 | Content Hash | sha256:25517b04...7b6340 | sha256:25517b04...7b6340 |
| 002 | Fingerprint  | sha256:b223180f...183599 | sha256:b223180f...183599 |

### What This Proves

1. RFC 8785 JCS (recursive) implemented in JavaScript = the Python
   `jcs` library, byte-for-byte.
2. RFC 6962 Merkle construction in JavaScript = the Python
   implementation, byte-for-byte.
3. RSA-2048 PKCS1v15 verification via Web Crypto API = Python
   `cryptography`, byte-for-byte.
4. No service, no CDN, no network — pure offline.

### Why It Matters

A certificate issued by a Python issuer can be verified by a
JavaScript verifier running in a browser, with no intermediary.

This is the definition of "portable certificate".

### Limitations

- Safari on `file://` may require HTTPS or localhost.
- Web Crypto must be available (all modern browsers).

**Approved by:** Owner.
**Effective:** 2026-10-05.

---

## DEC-043 — Browser Verifier v2 Adopted (Design)

**Phase:** P-STEP-02 (Gate 3 preparation)
**Status:** Adopted as design.
**Date:** 2026-10-05

### Decision

A second verifier, `visual-verifier-v2.html`, is adopted as a design
artifact for Gate 3. It implements the same verification logic as
`verify.py`, in pure JavaScript, using Web Crypto API.

### Constraints Satisfied

- PR-05: Zero external dependencies, no network, no CDN.
- PR-04: Does not modify the Python verifier or certificates.
- PR-06: Reviewed before adoption.

### What It Adds

- An auditor without Python can verify certificates in a browser.
- Drag-and-drop interface.
- Same error codes (E001-E010).

### What It Does NOT Do

- Does not replace `verify.py` (which remains canonical).
- Does not extend scope of the Python-based POC.
- Does not add a new cryptographic primitive.

### Location

Currently: `poc/.sandbox/visual-verifier-v2.html` (isolated).
Promotion to `poc/` requires a follow-up decision (DEC-044).

**Approved by:** Owner.
**Effective:** 2026-10-05.



---

## DEC-044 — Browser Verifier Production-Ready

**Phase:** P-STEP-02 (Gate 3 preparation)
**Status:** Proven.
**Date:** 2026-10-05

### Test Results (visual-verifier-v2.html)

| Input | Output |
|---|---|
| certificate-001.json + public-key-001.pem | VALID |
| certificate-002.json + public-key-001.pem | VALID |
| certificate-001.json + wrong-key.pem | INVALID: E001_SIGNATURE_INVALID |
| certificate-001-TAMPERED.json + public-key-001.pem | INVALID: E002_HASH_MISMATCH |

### What This Proves

1. The browser verifier **does not accept everything** — it rejects
   tampered certificates with a specific error code.
2. Tampering with a single field (decision_id) is detected before
   signature verification, at the JCS content-hash stage.
3. The verifier is fail-closed: any alteration → specific rejection.

### Constraints Satisfied

- PR-05: Offline, no CDN, no external dependency.
- E001-E010 error codes matched.
- Byte-identical to Python verifier (DEC-042).

### Deployment Decision

The browser verifier is **production-ready** for Gate 3 use.

Location:
- Current: `poc/.sandbox/visual-verifier-v2.html`
- Ready copy: `~/Desktop/adie-browser-test/visual-verifier-v2.html`
- Tarball: to be regenerated as v4 (includes browser verifier).

### Promotion to poc/

Deferred until after Gate 3 confirms auditors actually use it.

**Approved by:** Owner.
**Effective:** 2026-10-05.


## Summary

| ID Range | Phase | Count |
|---|---|---|
| DEC-001 to DEC-004 | P0 | 4 |
| DEC-005 to DEC-009 | P-STEP-01 | 5 |
| DEC-010 to DEC-016 | P-STEP-03/04 | 7 |
| DEC-017 to DEC-024 | P-STEP-05 | 8 |
| DEC-025 to DEC-034 | P-STEP-06.1 | 10 |
| DEC-035 | P-STEP-06.2 | 1 |
| DEC-036a | P-STEP-06.3 | 1 |
| DEC-036a-4 | P-STEP-06.3a | 1 |
| DEC-036b | P-STEP-06.3a | 1 |
| DEC-037 | P-STEP-02 | 1 |
| DEC-038 | P-STEP-02 (Gate 2) | 1 |
| DEC-039 | P-STEP-02 (Gate 2) | 1 |
| DEC-040 | P-STEP-02 (Gate 2) | 1 |
| **Total** | | **36** |

---

**End of DECISIONS.**


---

## DEC-045 — Charter Adopted

**Phase:** V5.1 Era (governance founding)
**Date:** 2026-10-05
**Status:** ✅ Adopted.
**Related:** File 15 (Charter), DEC-001 through DEC-044.

### Decision

The `ADIE_MEMORY_15_CHARTER.md` document is adopted as the founding
governance charter of the ADIE project. It becomes the highest-ranked
source of truth in the canonical hierarchy, superseding interpretation
conflicts between memory files, decision logs, and any AI-generated
output.

### Key Claims Elevated to Charter Status

1. **Authority Order (non-negotiable):**
   `Protocol Semantics > Conformance Tests > Security Model > Reference Implementation > Commercial Product > UI`

2. **Ten Governing Principles** (previously in `05_OPEN.md` §7):
   Truth before convenience; Alignment ≠ Fitness; Unknown ≠ Pass ≠ Refuted;
   No code until design closes; Every claim testable; Reframe, don't
   destroy; Causation ≠ Correlation; Fail-closed on ambiguity;
   Signature ≠ Authority; Assertion ≠ Authority.

3. **Canonical Sources of Truth (Charter §5):**
   Charter → Memory files → Decision log → POC Definition → Overview →
   Scope Paper → Legacy continuity.

4. **Boundary with EnterpriseGuard (Charter §6):**
   ADIE scope = `poc/`, `docs/ADIE_MEMORY/`, overview + scope paper.
   EnterpriseGuard scope = `src/enterpriseguard/`, `frontend/`, legacy
   `tools/`, uppercase `EnterpriseGuard/`.
   Legacy `continuity/DC-XXX` is frozen; new entries use `DEC-XXX`.

5. **Amendment Process (Charter §7):**
   Amendments require a new DEC referencing the amended section.

### What This Decision Does NOT Do

- Does not authorize any code change.
- Does not resolve AQ-12, AQ-16, or pending SDK migration questions
  (each requires its own DEC).
- Does not activate V5.1, ZK, HW, or BFT work.
- Does not amend any DEC-001 through DEC-044.

### Consequences

1. Any action contradicting Charter §3 or §4 is blocked.
2. New documents must declare their source from Charter §5.
3. Work on `src/enterpriseguard/` or `frontend/` requires justification
   as legacy maintenance or an explicit DEC.
4. The `continuity/DC-XXX` folder is frozen.

**Approved by:** Owner.
**Effective:** 2026-10-05.

---

**End of DEC-045.**


---

## DEC-046 — EXECUTION_PLAN.md Retraction Banner

**Phase:** V5.1 Era (governance housekeeping)
**Date:** 2026-10-05
**Status:** ✅ Adopted.
**Related:** DEC-045 (Charter), DC-145, DC-152a, DC-150i, DC-151.

### Decision

A retraction banner is added at the top of `docs/EXECUTION_PLAN.md`.
The banner declares the file **non-authoritative** and documents the
conflict between the file's "Phase C Completed" claim and the
authoritative record in DC-145.

### Rationale

Per DC-152a:

> "This DC documents the conflict only. `EXECUTION_PLAN.md` is
> intentionally NOT modified here. Follow-up DC-152b requires
> owner-authored v3.0 content (Rule 5)."

The banner is not a rewrite of v3.0. It is a **truth marker** that
prevents readers from being misled by false completion claims while
a proper owner-authored v3.0 is prepared. It respects Rule 5 by
not authoring substantive plan content.

### What This Decision Does NOT Do

- Does not author v3.0 content.
- Does not delete or truncate the existing file.
- Does not authorize any Phase C task.
- Does not resolve DC-152b (which remains pending).
- Does not affect the P0 signals or ADIE v2 scope.

### Consequences

1. Future readers of `EXECUTION_PLAN.md` see the retraction immediately.
2. The file remains tracked in git for audit purposes.
3. A future decision (number TBD) will replace this file with
   owner-authored v3.0 content per Rule 5.

### Precedent

This is the first "truth marker" DEC in the ADIE v2 era. It is a
template for how to neutralize a false claim without erasing history:
add a banner, record a DEC, preserve the original text.

**Approved by:** Owner.
**Effective:** 2026-10-05.

---

**End of DEC-046.**
