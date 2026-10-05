# ADIE — Identity

**Purpose:** What ADIE is, what concepts it uses, what invariants it holds.

---

## 1. What ADIE Means

**ADIE** = **Adaptive Defense Intelligence Engine**
- The decision core of EnterpriseGuard.
- Defined in `continuity/GLOSSARY.md`.
- Note: `README.md` has an outdated expansion ("Autonomous Decision
  Governance Infrastructure") — this is an error; GLOSSARY is authoritative.

**EnterpriseGuard** = the umbrella project.
**ADIE** = the engine inside it.
**SIBB** = Sovereign Immutable Black Box (WORM storage layer, DC-121).
**AAAC** = Agentic Accountability & Audit Core (separate product for
  LangSmith/Langfuse traces; not part of ADIE's core).
**DCP** = Decision Contract Protocol (future open specification, DC-143).

---

## 2. What ADIE Does NOT Do

ADIE is a **control plane**, not an executor.

Documented invariants (verified in source):
- `EXECUTES_SECURITY_ACTIONS = False` (in 6 source files)
- `DESTRUCTIVE_ACTIONS_ALLOWED = False` (in 5 source files)

ADIE:
- ✅ Observes
- ✅ Evaluates
- ✅ Decides
- ✅ Produces ExecutionManifests
- ✅ Signs evidence and decisions

ADIE does NOT:
- ❌ Execute security actions
- ❌ Modify infrastructure
- ❌ Perform remediation
- ❌ Call external systems

Execution happens **outside** ADIE, through a Manifest boundary.

---

## 3. Core Concepts

### Decision Lineage
The primary **trust artifact**. A reconstructible chain from decision back
to its evidence, policy, authority, and alternatives. Must answer:
> "What facts and rules were **causally sufficient** for D-184?"

### DecisionContract
The operational semantic output. A canonical decision issued by ADIE's
Decision Authority, after a complete evaluation chain. Distinct from
`SignedIntent`.

### SignedIntent (new, reframed from legacy DecisionContract)
An external caller's **assertion**, signed. Proves:
- Caller identity
- Request integrity
- Timestamp

Does NOT prove:
- Authority
- Policy compliance
- Decision validity

### AuthorityGrant
A first-class entity representing delegated authority. Has:
- Grantor (with `parent_grant_ref`)
- Grantee
- Scope (resource patterns, action types, environments, tenants)
- Constraints (approval level, execution mode, time windows, rate limits)
- Time validity (`granted_at`, `effective_from`, `expires_at`)
- Revocation state
- `policy_basis_ref` (versioned)
- `granted_purpose`
- Signature (by grantor, not by ADIE)

### AuthorityProof
The evaluation of authority at decision time T. Stored as a SIBB artifact.
Referenced by `DecisionContract` via `authority_proof_ref`. Immutable after
issuance.

### ExecutionManifest
The boundary between ADIE and external executors. Required **iff** the
DecisionContract declares an external execution obligation.

---

## 4. Invariants (Consolidated)

Numbered list, additions chronologically marked.
    Observation ≠ Decision

    Decision ≠ Execution

    Evidence ≠ Authority

    Planning ≠ Action

    Prediction ≠ Decision

    Assertion ≠ Authority (added P-STEP-04)

    Signature ≠ Authority (added P-STEP-04)

    Integrity ≠ Validity (added P-STEP-04)

    No single entity carries the whole lifecycle (added P-STEP-05)

    ExecutionManifest required iff external obligation declared (amended)

    Prediction requirement is policy-derived fact (amended)

    Lineage is primary trust artifact; DecisionContract remains the
    operational semantic output (amended P-STEP-05)

    Authority ≠ Capability (added P-STEP-06)

    AuthorityResolution is policy-defined, deterministic, fail-closed
    (added P-STEP-06)

    Grants are evaluated against the policy version under which they were
    issued, plus any explicit subsequent invalidation (added P-STEP-06)

    Approval ≠ AuthorityGrant (added P-STEP-06, provisional)
17. No causal sufficiency claim is valid without an explicitly
    identified causal question, causal model/version, context,
    and evaluation semantics. (added P-STEP-06.3)
18. ADIE must never prove more causality than its declared causal
    model supports. (added P-STEP-06.3)
19. Corroborative evidence may strengthen an evidentiary claim
    but must not be promoted to a causal claim without causal
    support. (added P-STEP-06.3)
20. Derivability ≠ Causal Sufficiency. (added P-STEP-06.3)
21. Computation correctness, derivation correctness, and causal
    sufficiency are distinct proof obligations.
    (added P-STEP-06.3)

text


---

## 5. Key Glossary Terms

| Term | Definition |
|---|---|
| **Ledger** | Canonical event stream + causal structure. Sits *above* SIBB. |
| **SIBB** | WORM storage for Evidence and Authority artifacts. |
| **Trust Anchor** | Institutional root (charter + keys). Not a single genesis key. |
| **Authority Chain** | Series of grants from Root to Actor. |
| **Causal Sufficiency** | Minimal set of facts/rules sufficient to explain a decision. |
| **Semantic Escalation** | A value gaining meaning it doesn't earn (e.g., `authorized=True`). |
| **Reframing** | Conceptual reclassification without destructive rename. |

---

## 6. Repository Structure (as of audit)

EnterpriseGuard/
├── src/enterpriseguard/ ← CANONICAL
│ ├── adie/ ← PROTECTED (Rule 1)
│ ├── intelligence/ ← PROTECTED (Rule 1)
│ ├── decision/ ← canonical decision contracts
│ ├── response/ ← canonical response contracts
│ ├── sdk/ ← Phase B SDK
│ ├── api/ ← HTTP API
│ ├── signing/ ← crypto backend
│ └── ui/ ← PyQt6 (unresolved)
├── frontend/ ← React UI (isolated)
├── EnterpriseGuard/ ← legacy AAAC pitch (separate git repo)
├── enterpriseguard/ ← legacy compatibility boundary
├── tools/ ← CLI tools, verification utilities
├── continuity/ ← decision cards (DC-XXX)
├── docs/ ← strategic documents
└── tests/ ← root test suite
text


**Protected paths (Rule 1):**
- `adie/`
- `intelligence/`
- `src/enterpriseguard/adie/`
- `src/enterpriseguard/intelligence/`

---

## 7. Governance

- **145 decision cards** (DC-XXX) recorded.
- **19 permanent rules** (RULES.md).
- **GitHub Actions CI** validates 148 adversarial tests.
- **Two Git repos** exist (root + nested in EnterpriseGuard/).

**Rule 15** allows Owner to authorize exceptions to Rule 1 (Protected
Directories). Such authorization must be documented.

---

## 8. What ADIE is NOT (positioning)

- Not a SIEM.
- Not a SOAR.
- Not an XDR.
- Not a Dashboard.
- Not an ML detector.

**ADIE is a Decision Trust Layer.** Its goal:
> "Don't trust the AI. Verify the decision."

---


---

## 4b. Permanent Rules (PR-01 to PR-05)

Adopted 2026-10-04 as binding constraints for all ADIE work.

| # | Rule | Effect |
|---|---|---|
| PR-01 | Semantic Pollution Prohibited | DecisionContract (content-only) is strictly separated from emission_fingerprint (RFC 6962 Merkle root). Linkage through explicit refs, never through merging. |
| PR-02 | JCS (RFC 8785) Mandatory | No json.dumps(sort_keys=True) for canonicalization. All signatures and hashes use JCS. |
| PR-03 | Fail-Closed Always | Every tampering scenario must produce a specific error code (E001-E010). No silent acceptance. |
| PR-04 | Phase P Frozen Scope | During POC, only the 4 designated files. No React, PyQt6, or Cross-Language work. |
| PR-05 | Standalone Verifier | verify.py must not import enterpriseguard, must work offline, must be zero-trust. |

These rules are non-negotiable. Any code that violates them is rejected.



---

## 4c. Permanent Rule PR-06 (adopted 2026-10-04)

**No external modification of poc/ without review.**

Any change to poc/verify.py, poc/test_pstep02.py, poc/certificate-*.json,
or poc/*.pem must pass through the review conversation before execution.

If review is not possible, run the script on a copy in `.sandbox/` first.

Rationale: an external script broke test_pstep02.py with an
IndentationError on 2026-10-04. The recovery restored the working
version, but the incident proved untrusted modifications to the POC
are a real risk.


**End of IDENTITY.**
