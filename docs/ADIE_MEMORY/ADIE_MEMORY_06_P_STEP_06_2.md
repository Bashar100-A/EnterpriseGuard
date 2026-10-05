# ADIE — P-STEP-06.2: Ledger / Event Model

**Purpose:** Complete memory of P-STEP-06.2 (Ledger Event Model design),
including its journey, decisions, discoveries, and open questions.

**Status:** Design COMPLETE — pending adoption as DEC-035.
**Supersedes:** none (this is the first Ledger design).
**Depends on:** P-STEP-06.1 (Authority Model, DEC-025 → DEC-034).

---

## 0 — Status & Relationship to Files 00–05

**Read this file after files 00–05.**

Files 00–05 covered:
- ADIE identity (file 01)
- Forensic journey P0 → P-STEP-06.1 (file 02)
- Decisions DEC-001 → DEC-034 (file 03)
- Design state through Authority Model (file 04)
- Open questions AQ-1 → AQ-22 (file 05)

This file (06) extends that memory with:
- **The full Ledger design** (P-STEP-06.2) — target DEC-035
- **13 new open questions** (OQ-06.2-1 → OQ-06.2-14)
- **The WORM ordering procedure** (correct sequencing of artifact writes)
- **The Content-Only Contract Principle** (§0.1 of the design)
- **The journey v1 → v2.4** (four iterations with 15+ discoveries)

**Current state:**
- Design phase: still design-only. No code authorized.
- Next phase: P-STEP-06.3 (Causal Sufficiency).
- DEC-035 is ready to record.

---

## 1 — Journey: v1 → v2.4

P-STEP-06.2 went through **four design iterations**, each closing specific gaps.

### v1 (initial draft)

Produced: topology (hybrid), event structure, causal edges, JCS, Merkle,
multi-tenancy, query interface.

**Issues found in review:**
1. `prev_event_hash` was placed before topology was fixed — reversed order.
2. Decision boundary defined as "before/after EMITTED" — semantic error.
3. Circular dependency between `lineage_fingerprint` and `DecisionContract hash` not resolved.
4. "Merkle tree" not specified — many variants possible.
5. `payload_ref` had redundant `content_hash`.
6. `superseded_by[]` semantics ambiguous.
7. `RELATIONSHIP_EVENT` class not defined.
8. No mention of compaction/retention.

### v2

**Fixes:**
1. Reordered: topology → event structure → causal edges → serialization → fingerprint.
2. §1.2 rebuilt around **subject identity**, not time.
3. Solution C for circular dependency: `DecisionContract` = content-only; fingerprint in SIBB; ref via link artifact.
4. RFC 6962 adopted explicitly with test vectors.
5. `payload_ref` simplified to `{location_hint}`.
6. `superseded_by[]` clarified (event_ids only; entity via traversal).
7. `RELATIONSHIP_EVENT` class added.
8. Compaction/retention named as out-of-scope.

**Issues found in v2 review:**
1. §1.2 still had "after EMITTED → new Decision context" — wrong.
2. `decision_id` allocation not defined.
3. `superseded_by[]` still type-ambiguous.
4. Fingerprint computation point not specified.
5. `payload_ref.content_hash` still redundant.

### v2.1

**Fixes:**
1. §1.2 fully rebuilt: primary-subject identity defines chain.
2. `DECISION_INITIATED` event introduced; `decision_id` allocated there.
3. §1.3 title changed to "Events Spanning Multiple Chains".
4. §5.9 added — **Fingerprint Computation Point** (at `EMITTED`, covers Construction + Emission only).
5. `superseded_by[]` — event_ids only.
6. `payload_ref.content_hash` removed.

**Issues found in v2.1 review:**
1. No field on `DECISION_EMITTED` pointed to `DecisionContract`.
2. Atomic transaction across chains (superseding) not representable in data.
3. `lineage_fingerprint` naming too broad — actual scope is emission only.

### v2.2

**Fixes:**
1. `contract_ref: {content_hash, location_hint} | null` added to `LIFECYCLE_EVENT` body.
2. Transaction representation deferred to OQ-06.2-12.
3. Renamed `lineage_fingerprint` → `emission_fingerprint` throughout.

**Issues found in v2.2 review:**
1. Scope of "content" for `decision_contract_content_hash` not defined.
2. No domain prefix for `decision_contract_content_hash` in §4.3.
3. WORM violation: §5.5 wrote the ref back onto the contract after fingerprint computation.

### v2.3

**Fixes:**
1. §5.5 Step 1 defines `content` explicitly (all fields except marked derived).
2. `ADIE:CONTRACT:v1:` domain prefix added.
3. §5.5 Step 5 rewritten — the mapping lives in a **separate SIBB artifact** (`contract-emission-link`); the contract is NOT modified.
4. §5.8 updated with WORM note (causal_set_ref symmetry).
5. OQ-06.2-13 added (role of `EMISSION_FINGERPRINT_COMPUTED`).

**Issues found in v2.3 review:**
1. §5.8 still had textual contradiction.
2. SIBB lookup path from `decision_contract_content_hash` to link artifact undefined.
3. Design principle implicit but not named.

### v2.4 (current)

**Fixes:**
1. §0.1 — **Content-Only Contract Principle** named explicitly. All post-freeze outputs go to separate SIBB artifacts.
2. §5.8 — placement **deferred**; WORM constraint recorded; recommendation noted as proposal.
3. OQ-06.2-14 added (SIBB lookup path with 3 candidates).

**Status:** ready for adoption as DEC-035.

---

## 2 — Design Decisions Adopted (upcoming DEC-035)

The following are the load-bearing decisions of P-STEP-06.2:

| # | Decision | Section |
|---|---|---|
| D1 | Ledger topology = **hybrid** (linear within chain, DAG between decisions) | §1.1 |
| D2 | Decision boundary = **primary subject identity**, not time | §1.2 |
| D3 | `decision_id` allocated at `DECISION_INITIATED` | §1.2 |
| D4 | Cross-chain events = **two atomic events in one transaction** | §1.3 |
| D5 | Event envelope with `event_class` (LIFECYCLE / RELATIONSHIP) | §2.1 |
| D6 | `contract_ref` in `LIFECYCLE_EVENT` body — points to `DecisionContract` | §2.1.1 |
| D7 | `payload_ref` = `{location_hint}` only | §2.1 |
| D8 | Causal edges in **separate fields** from informational refs | §3.1 |
| D9 | JCS (RFC 8785) for canonical serialization | §4.1 |
| D10 | Distinct **domain prefixes** per hash type | §4.3 |
| D11 | `prev_event_hash` **is included** in `event_hash` | §4.4 |
| D12 | Merkle construction = **RFC 6962** explicitly | §5.2 |
| D13 | Circular dependency resolved via **Solution C** | §5.5 |
| D14 | Fingerprint computed at **`DECISION_EMITTED`**; Construction + Emission only | §5.9 |
| D15 | **Content-Only Contract Principle** — post-freeze outputs live in SIBB artifacts | §0.1 |
| D16 | Multi-tenancy = **one logical Ledger** | §6 |
| D17 | `by_decision` returns exactly one chain | §7.1 |
| D18 | Reconstruction requires **Ledger + SIBB** | §7.3 |

---

## 3 — Key Design Artifacts

### 3.1 — Ledger Topology

**Hybrid:**
- Within one entity chain: linear, append-only, `prev_event_hash`.
- Between decisions: DAG, atomic decision nodes, typed causal edges.
- Cross-entity edges are typed (not linearized).

**Decision boundary = primary subject identity:**
- An event belongs to entity `E` iff its primary subject is `E`.
- For `LIFECYCLE_EVENT`: primary subject = `subject`.
- For `RELATIONSHIP_EVENT`: primary subject = `subject_primary`.

### 3.2 — Event Envelope
LedgerEvent
├── event_id, schema_version, event_class, event_type
├── tenant_id, environment_id
├── actor {actor_id, actor_type}
├── timestamp {physical_utc, logical_clock}
├── preconditions[]
├── authority_proof_ref, policy_basis_ref
├── payload {payload_hash, payload_ref}
├── causal {caused_by[], produces[], required_for[],
│ satisfied_by[], derived_from[], superseded_by[], revoked_by[]}
├── refs[]
├── body {LIFECYCLE | RELATIONSHIP}
├── prev_event_hash
├── event_hash
└── signature (reserved)
text


**LIFECYCLE body:**

{ subject {entity_type, entity_id},
transition,
contract_ref {content_hash, location_hint} | null }
text


**RELATIONSHIP body:**

{ subject_primary {entity_type, entity_id},
subject_secondary {entity_type, entity_id},
relationship_type }
text


### 3.3 — Emission Fingerprint (RFC 6962)

**Construction:**

MTH({}) = SHA-256("")
MTH({d_0}) = SHA-256(0x00 || d_0)
MTH(D_n) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n]))
where k = largest power of two < n
text


**Leaves (in canonical order):**
1. `event_hash` for events in causally sufficient set.
2. SIBB artifact content hashes.
3. `decision_contract_content_hash`.

**Domain prefix:**

emission_fingerprint = H("ADIE:EMISSION:v1:" || merkle_root_bytes)
text


**Scope:** Construction + Emission segments only.

### 3.4 — WORM Ordering Procedure (§5.5)

**Six steps, in strict order:**

Step 1: Freeze contract content.
DecisionContract = content only. No fingerprint, no ref.

Step 2: Compute decision_contract_content_hash.
= H("ADIE:CONTRACT:v1:" || JCS(content))

Step 3: Compute emission_fingerprint.
= H("ADIE:EMISSION:v1:" || RFC6962_Merkle_Root(leaf_list))

Step 4: Store fingerprint in SIBB.
Immutable, content-addressed, WORM.

Step 5: Store contract-emission-link in SIBB.
{decision_id, decision_contract_content_hash, emission_fingerprint_ref}
DecisionContract is NOT modified.

Step 6: (implicit) The DECISION_EMITTED event is recorded,
carrying contract_ref = {content_hash, location_hint}.
text


**Critical property:** No artifact is amended. Every artifact is written exactly once.

### 3.5 — Content-Only Contract Principle

> **The `DecisionContract` is content-only.**
>
> **All outputs computed after its content is frozen live in separate SIBB
> artifacts, referenced via link artifacts — never embedded in the contract.**

**Test for future decisions:**
- Is X known at contract content freeze?
  - **Yes** → may live on the contract.
  - **No** → lives in a separate SIBB artifact.

**Already applies to:**
- `AuthorityProof` (referenced from event, not embedded).
- `emission_fingerprint` (separate SIBB artifact + link).
- `causal_set_ref` (placement deferred, likely in link).
- `lifecycle_fingerprint` (future, same pattern).
- `signature` (future, TBD).

---

## 4 — Discoveries

Fifteen distinct discoveries made during four iterations. The most consequential:

| # | Discovery | Where fixed |
|---|---|---|
| 1 | Decision boundary cannot be time-based; must be subject-based | §1.2 |
| 2 | `Outcome(D-184)` is NOT a new decision — it is continuation | §1.2 |
| 3 | `DecisionContract` frozen before `DECISION_EMITTED` → `causal_set_ref` cannot be on it | §5.8 |
| 4 | WORM ordering requires all post-freeze outputs to live outside the contract | §5.5, §0.1 |
| 5 | `lineage_fingerprint` naming too broad; renamed to `emission_fingerprint` | §5.1 |
| 6 | Merkle variants differ — must pick one explicitly (RFC 6962) | §5.2 |
| 7 | `superseded_by[]` cannot hold entity_ids — must be event_ids only | §2.1 |
| 8 | Atomic cross-chain transactions need explicit representation | §1.3, OQ-06.2-12 |
| 9 | SIBB is content-addressed WORM — field-based lookup is nontrivial | OQ-06.2-14 |
| 10 | `prev_event_hash` must be in `event_hash` for tamper-evidence | §4.4 |
| 11 | `payload_ref` must carry location hint, not content_hash | §2.1 |
| 12 | Domain prefix per hash type prevents cross-context collision | §4.3 |
| 13 | Design principle was implicit — needed to be named | §0.1 |
| 14 | Fingerprint computation point must be explicit (at EMITTED) | §5.9 |
| 15 | Reconstruction requires **Ledger + SIBB**, not Ledger alone | §7.3 |

**Meta-discovery:** Iterative review with an external reviewer caught errors
that a single pass would have missed. The v1 → v2.4 evolution is itself
evidence of the value of the review process.

---

## 5 — Open Questions (OQ-06.2-1 → OQ-06.2-14)

Deferred. They do NOT block adoption of DEC-035, but MUST be resolved before implementation.

| ID | Question | Target |
|---|---|---|
| OQ-06.2-1 | Hash algorithm (SHA-256 / SHA-3 / BLAKE3) | before impl |
| OQ-06.2-2 | Domain prefix exact string format | P-STEP-06.5 |
| OQ-06.2-4 | Causal edges stored redundantly or derived | P-STEP-06.5 |
| OQ-06.2-5 | Byte-level encoding of Merkle ordering keys | P-STEP-06.5 |
| OQ-06.2-6 | Full event type enumeration | P-STEP-06.5 |
| OQ-06.2-7 | Lamport counter scope | P-STEP-06.5 |
| OQ-06.2-8 | Query wire format, pagination, authz | P-STEP-06.5 / impl |
| OQ-06.2-9 | Full list of derived fields per entity | P-STEP-06.5 |
| OQ-06.2-10 | `payload_ref.location_hint` format | P-STEP-06.5 |
| OQ-06.2-11 | Formalize `lifecycle_fingerprint` | future phase |
| OQ-06.2-12 | Representation of atomic cross-chain transaction | P-STEP-06.5 |
| OQ-06.2-13 | Role of `EMISSION_FINGERPRINT_COMPUTED` event | P-STEP-06.5 |
| OQ-06.2-14 | Lookup path from `content_hash` to `contract-emission-link` | P-STEP-06.5 |

**Candidate (not yet formally adopted):**
- OQ-06.2-15: §5.8 recommendation vs §5.5 link schema — extend link schema
  when placement is adopted.

---

## 6 — What to Execute Next

### 6.1 — Immediate: Record DEC-035

**Action:** Add DEC-035 to `ADIE_MEMORY_03_DECISIONS.md`.

DEC-035 — Ledger / Event Model Adopted (P-STEP-06.2 v2.4)

The Ledger / Event Model design (P-STEP-06.2, v2.4) is adopted. Key decisions:

    Hybrid topology (linear within chain, DAG between decisions)

    Decision boundary by primary-subject identity

    Content-Only Contract Principle

    RFC 6962 Merkle for emission fingerprint

    WORM ordering procedure (six steps)

    One logical Ledger (multi-tenancy via tenant_id/environment_id)

    18 load-bearing decisions (see file 06 §2)

    13 open questions (OQ-06.2-1 → OQ-06.2-14)

See ADIE_MEMORY_06 for full details.
text


**Also update:**
- `ADIE_MEMORY_04_DESIGN.md` §3 (Storage Model) — fold in Ledger design summary.
- `ADIE_MEMORY_00_README.md` — add reference to file 06.

### 6.2 — Next Phase: P-STEP-06.3 (Causal Sufficiency)

**Question this phase answers:** *What is the causally sufficient set?*

**Deliverable:** Formal definition + acceptance test + prevention of causal inflation.

**Inputs from P-STEP-06.2:**
- `caused_by[]`, `required_for[]`, etc. as structural fields (§3.1).
- `causal_set_ref` field exists but placement deferred (§5.8).
- `emission_fingerprint` covers the causally sufficient set at `EMITTED` (§5.9).
- Test signature: `causal_sufficiency_test(transition, edge) → boolean` (§3.3).

**Outputs of P-STEP-06.3:**
- Formal definition of "causally sufficient."
- Algorithm for constructing the set from the Ledger.
- Constraint that the set is minimal (no causal inflation).
- Placement decision for `causal_set_ref` (on-contract vs. link).

### 6.3 — Dependencies for P-STEP-06.3

- **DEC-035 must be recorded.** The design must be frozen.
- **§0.1 Content-Only Contract Principle** must be applied consistently.
- **The `causal_sufficiency_test` signature** (§3.3) must be respected.
- **The `EMITTED` boundary** (§5.9) is the emission scope for the causal set.

---

## 7 — What P-STEP-06.2 Does NOT Cover

| Non-decision | Deferred to |
|---|---|
| Causal sufficiency formal definition | P-STEP-06.3 |
| Transition rules & actor permissions | P-STEP-06.4 |
| Entity schemas (12 entities) | P-STEP-06.5 |
| Signing system unification | separate decision (AQ-12) |
| Approval entity | after Ledger (AQ-17) |
| Trust Anchor | after Ledger (AQ-18) |
| Compaction / retention / archive | future phase |
| Migration V1 → V2 | AQ-20 |

---

## 8 — How to Continue in a New Conversation

**To restore full context:**
1. Provide files `ADIE_MEMORY_00` through `ADIE_MEMORY_06`.
2. Say: "Read in order. Continue from `ADIE_MEMORY_05_OPEN.md` §3 or `ADIE_MEMORY_06_P_STEP_06_2.md` §6."

**To continue P-STEP-06.3:**
- Read this file (§6.2, §6.3).
- Read `ADIE_MEMORY_05_OPEN.md` §2 (Priority B).
- Begin with AQ-6 (formal definition of causal sufficiency).

**To continue implementation (after all design phases):**
- All P-STEP-06.x phases must be complete.
- DEC-035 and subsequent must be recorded.
- Explicit authorization for code change required.

**Vocabulary inherited:**
- `emission_fingerprint` — covers Construction + Emission, frozen at `DECISION_EMITTED`.
- `contract-emission-link` — SIBB artifact mapping `content_hash` → `emission_fingerprint_ref`.
- `DECISION_INITIATED` — first event of decision chain, allocates `decision_id`.
- Content-Only Contract Principle — post-freeze outputs live outside the contract.

---

**End of ADIE_MEMORY_06.**
