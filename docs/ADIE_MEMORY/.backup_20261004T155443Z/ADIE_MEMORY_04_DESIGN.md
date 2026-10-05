# ADIE — Current Design

**Purpose:** The current authoritative design state.

**Phase:** P-STEP-06.1 complete (Authority Model).
**Next:** P-STEP-06.2 (Ledger / Event Model).

---

## 1. High-Level Architecture
┌────────────────────────────┐
│ Trust Anchor │
│ (charter + keys) │
└─────────────┬──────────────┘
│
┌─────────────▼──────────────┐
│ Root AuthorityGrant │
└─────────────┬──────────────┘
│
delegation
│
┌─────────────▼──────────────┐
│ Authority Chain │
└─────────────┬──────────────┘
│
┌───────────────────┼───────────────────┐
│ │ │
▼ ▼ ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Observation │ │ Policy │ │ Authority │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
│ │ │
▼ │ │
┌───────────────┐ │ │
│ Evidence │ │ │
└───────┬───────┘ │ │
│ │ │
▼ │ │
┌───────────────┐ │ │
│ State │ │ │
└───────┬───────┘ │ │
│ │ │
▼ │ │
┌───────────────┐ │ │
│ Prediction │ │ │
│ (optional) │ │ │
└───────┬───────┘ │ │
│ │ │
└───────────┬───────┴───────────────────┘
│
▼
┌───────────────┐
│ PolicyEvaluation│
└───────┬───────┘
│
SignedIntent│(optional input)
│
▼
┌───────────────┐
│DecisionContract│
└───────┬───────┘
│
▼ (iff external obligation)
┌───────────────┐
│ExecutionManifest│
└───────┬───────┘
│
▼
External Executor
│
▼
┌───────────────┐
│ Execution │
└───────┬───────┘
│
▼
┌───────────────┐
│ Outcome │
└───────┬───────┘
│
▼
┌───────────────┐
│ Feedback │
└───────┬───────┘
│
└───► (loops back to Observation)
text


---

## 2. The 12 Entities

### Layer 1 — Perception

| # | Entity | Lifecycle |
|---|---|---|
| 1 | Observation | `CAPTURED → NORMALIZED → ATTRIBUTED` |
| 2 | Evidence | `RAW → VERIFIED → BOUND_TO_SIBB → ATTESTED → ARCHIVED` |
| 3 | State | `SNAPSHOT → VALIDATED → IN_USE → SUPERSEDED` |
| 4 | Prediction | `GENERATED → VALIDATED → CONSUMED → EXPIRED → SUPERSEDED` |

### Layer 2 — Evaluation

| # | Entity | Lifecycle |
|---|---|---|
| 5 | PolicyEvaluation | `REQUESTED → EVALUATING → EVALUATED → {ALLOWED | DENIED | INDETERMINATE}` |
| 6 | AuthorityGrant | `PROPOSED → GRANTED → ACTIVE → {REVOKED | EXPIRED}` |

### Layer 3 — Decision

| # | Entity | Lifecycle |
|---|---|---|
| 7 | SignedIntent | `RECEIVED → VERIFIED → ACCEPTED → {REJECTED | REFUSED | DEFERRED}` |
| 8 | DecisionContract | `DRAFTED → VALIDATED → AUTHORIZED → EMITTED → {CONSUMED | EXPIRED | SUPERSEDED}` |

### Layer 4 — Execution & Learning

| # | Entity | Lifecycle |
|---|---|---|
| 9 | ExecutionManifest | `DRAFT → ELIGIBLE → APPROVED → DISPATCHED → {RECALLED | EXPIRED}` |
| 10 | Execution | `SCHEDULED → RUNNING → {COMPLETED | FAILED | ABORTED}` |
| 11 | Outcome | `RECORDED → ASSESSED → CLOSED` |
| 12 | Feedback | `CAPTURED → CLASSIFIED → {APPLIED | ARCHIVED}` |

---

## 3. Storage Model

┌─────────────────────────────────────┐
│ Decision Ledger │
│ │
│ • canonical events │
│ • typed transitions │
│ • causal edges │
│ • lineage structure │
│ • reconstruction queries │
└──────────────┬──────────────────────┘
│ references (by hash / id)
▼
┌─────────────────────────────────────┐
│ SIBB │
│ │
│ ├── Evidence artifacts │
│ └── Authority artifacts │
│ │
│ • immutable content │
│ • content-addressed │
│ • WORM │
│ • hashes + provenance │
└─────────────────────────────────────┘
text


**Rules:**
- SIBB stores **content**; Ledger stores **structure + events**.
- Ledger never duplicates SIBB content.
- SIBB never stores transitions.
- `Decision Lineage` is reconstructed from both.

---


### 3.5 — Storage Model Refined (P-STEP-06.2, DEC-035)

The storage model below supersedes the initial view in §3.

**Ledger topology (hybrid):**
- Within a single entity chain: linear, append-only, `prev_event_hash`.
- Between decisions: DAG, atomic decision nodes, typed causal edges.
- Decision boundary = primary subject identity.

**WORM ordering (six steps, §5.5 of P-STEP-06.2):**

Step 1: Freeze contract content.
DecisionContract = content only.
Step 2: decision_contract_content_hash
= H("ADIE:CONTRACT:v1:" || JCS(content))
Step 3: emission_fingerprint
= H("ADIE:EMISSION:v1:" || RFC6962_Merkle_Root(leaf_list))
Step 4: Store fingerprint in SIBB (immutable).
Step 5: Store contract-emission-link in SIBB:
{decision_id, decision_contract_content_hash, emission_fingerprint_ref}
Step 6: Record DECISION_EMITTED with contract_ref.
text


**Content-Only Contract Principle:**
> `DecisionContract` is content-only. All outputs computed after its content
> is frozen live in separate SIBB artifacts, referenced via link artifacts —
> never embedded in the contract.

**Emission fingerprint (RFC 6962):**
- Leaves (canonical order): `event_hash` list + SIBB artifact hashes +
  `decision_contract_content_hash`.
- Scope: Construction + Emission segments only (frozen at `DECISION_EMITTED`).

**Event envelope:**
- Two classes: `LIFECYCLE_EVENT`, `RELATIONSHIP_EVENT`.
- Causal edges in separate fields from informational references.
- `tenant_id` + `environment_id` mandatory on every event.

**Full details:** `ADIE_MEMORY_06_P_STEP_06_2.md`.


## 4. Authority Model

### 4.1 `AuthorityGrant` — Schema Sketch

AuthorityGrant
├── grant_id
├── grant_version (semver)
├── grantor
│ ├── grantor_id
│ ├── grantor_type (human | role | system | service)
│ └── parent_grant_ref (nullable only at root)
├── grantee
│ ├── grantee_id
│ └── grantee_type
├── scope
│ ├── resource_patterns[]
│ ├── action_types[]
│ ├── environment_ids[]
│ └── tenant_ids[]
├── constraints
│ ├── required_approval_level
│ ├── execution_mode (DRY_RUN | MANUAL_APPROVAL | AUTOMATIC)
│ ├── time_window
│ ├── rate_limits
│ └── co_signers[]
├── time
│ ├── granted_at
│ ├── effective_from
│ ├── expires_at (mandatory)
│ └── max_validity
├── revocation
│ ├── revoked_at (nullable)
│ ├── revoked_by
│ ├── revocation_reason
│ └── revocation_proof_ref
├── policy_basis
│ ├── policy_basis_ref
│ ├── policy_version (immutable)
│ └── policy_hash (content-addressed)
├── granted_purpose
├── signature (by grantor, not by ADIE)
└── status (derived, not stored)
text


### 4.2 Chain Rules

grantee.scope ⊆ grantor.scope
grantee.constraints ⊇ grantor.constraints
grantee.expires_at ≤ grantor.expires_at
text


**Delegation narrows; never widens.**

### 4.3 Time Model

| Field | Meaning |
|---|---|
| `granted_at` | When issued |
| `effective_from` | When becomes active (can be future) |
| `expires_at` | When auto-expires |
| `revoked_at` | When manually revoked (or null) |

**Active at time T iff:**

effective_from ≤ T < expires_at
AND revoked_at IS NULL
AND parent_chain_is_active(T)
text


`status` is **derived** (a query result), not a stored field.

### 4.4 Authority Resolution (policy-defined)

**No heuristic "strongest grant."** Resolution is:

Candidate Grants
↓
Validity check
↓
Scope matching
↓
Constraint checking
↓
Conflict Resolution Policy ← must be explicit
↓
ONE deterministic AuthorityProof
text


Result types:
- `VERIFIED` — valid chain found
- `INSUFFICIENT` — authority exists but not for this action
- `AMBIGUOUS` — conflicting authorities, no resolution rule
- `FAILED` — no authority

**If `AMBIGUOUS`: no DecisionContract.**

### 4.5 Failure Modes (explicit)

| Mode | Meaning |
|---|---|
| `AUTHORITY_NOT_FOUND` | No matching grant |
| `AUTHORITY_EXPIRED` | Found but expired |
| `AUTHORITY_REVOKED` | Found but revoked |
| `AUTHORITY_OUT_OF_SCOPE` | Found but out of scope |
| `AUTHORITY_CONSTRAINT_VIOLATED` | In scope but constraint broken |
| `AUTHORITY_CHAIN_BROKEN` | An ancestor grant failed |
| `AUTHORITY_POLICY_INVALIDATED` | Explicit subsequent policy invalidation |
| `AUTHORITY_CONFLICT` | Unresolved conflict |

Note: `AUTHORITY_POLICY_OBSOLETE` removed — see DEC-028.

### 4.6 `policy_basis_ref` Semantics

- Grant evaluated against **policy version under which issued**.
- NOT against current policy version.
- Exceptions only if:
  - New policy explicitly invalidates existing grants
  - New policy is declared retroactive
- `POLICY_OBSOLETE ≠ POLICY_INVALIDATED_GRANT`.

### 4.7 AuthorityProof

- Runtime artifact, immutable.
- Stored as SIBB artifact.
- `DecisionContract` holds `authority_proof_ref`.
- Proof cannot be modified after issuance.
- If extension needed: new artifact, new ref. Old proof remains for the
  historical decision.

### 4.8 Trust Anchor

- Not a single genesis key.
- Composite:
  - Institutional charter
  - Key set (possibly threshold)
  - Explicit delegation into Root AuthorityGrant
- Details to be defined (deferred).

### 4.9 Authority ≠ Capability

- `AuthorityGrant` = proof of granted authority.
- `AuthorityProof` = proof of use at time T.
- Grant is **not** a bearer token or credential.

---

## 5. Canonicalization & Signing (Current — to be revised)

- `SignedIntent` signed with RSA-2048 / ECDSA-P256 (from `signing/backend.py`).
- Report signing (adversarial tests) uses Ed25519.
- **Two signing systems not reconciled.**
- `jcs` (RFC 8785) installed but unused.
- Canonicalization is `json.dumps(sort_keys=True, separators=(",", ":"))`.

**Open issue:** Reconcile signing systems as part of V2.

---

## 6. API Surface (Target)

| Endpoint | Layer | Status |
|---|---|---|
| `POST /v1/intents` | Assertion | To be built (rename of `/v1/decisions` V1) |
| `POST /v1/verify` | Verification | Exists (but verifies only signature) |
| `POST /v1/decisions` | Canonical | Reserved for V2 |
| `GET /v1/health` | Health | Exists |
| `GET /v1/decisions/recent` | Query | Exists; will be reframed |
| `GET /dashboard` | UI | Exists; will display intents + decisions distinctly |

---

## 7. Frontend React Status

- 304 files, 24 routes, 12 phases (A→L).
- Contracts mirror ADIE concepts in naming, differ in structure.
- `ApiClient` exists; never wired in production.
- Not connected to any backend.
- **Frozen** until V2 API is defined.

---

## 8. What Has Changed Since V1

| Aspect | V1 | V2 (Design) |
|---|---|---|
| `authorized=True` default | Yes | Not present |
| Policy evaluation | Bypassed | Required |
| Authority | Text field | First-class entity |
| Evidence refs | Not in artifact | Required |
| Manifest | Not linked | Architectural |
| Lifecycle | One unified | 12 independent |
| `Decision` meaning | 4 conflicting | 2 distinct (Intent vs Contract) |
| Signature system | RSA/ECDSA + Ed25519 (unreconciled) | To be reconciled |
| Verifier | Signature only | Signature + Provenance + Claim (planned) |

---

**End of DESIGN.**
