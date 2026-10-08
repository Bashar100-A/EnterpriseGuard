# vOmega — Technical Capability Document

**Status:** Recovered / Staged / Pending Commander Review
**Recovered from:** conversation transcript (not from prior disk state)
**Evidence-reference commit:** `7683adb` (branch `vOmega`)
**Document scope (this recovery):** Part I (E1–E8) + Part II (D1–D10)
**Not included in this recovery:** D11–D12, Part III (Appendices A–H)
**Frozen upstream specifications:**
- `spec/WIRE-FORMAT-0.2.md` — SHA-256 `b2fee085562dec275572d0ed64faa30bc0375ee9a74fe319b0af984895dcf07f`
- `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md` — SHA-256 `7cb607be51b7a5d1afbb78611d66b0db3ef3c8cdc30de15ee41b3a701e4762ab`
- `spec/WIRE-FORMAT-0.2-AMENDMENT-2.md` — SHA-256 `5e02bf89cfa347b7ff4b0b798ed0e7030866dc1f2989e060e8aca54768f844ac`
- `docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md` — SHA-256 `e9c0cd35637a21b5c5bc7268b084694805a79f4c55df06d9d65859f150a36412`
- `docs/vomega/decisions/DECISION-0.4-CBOR-ENVELOPE.md` — SHA-256 `848a52d1e027637c308e092bf5b3cee29fcbecdf8c1a179c971c4efc3dfd8ba2`

---

## Table of Contents

- Part I — Executive Technical Summary
  - E1. Document Purpose and Reading Guide
  - E2. The Problem Space
  - E3. What vOmega Proves — at a Glance
  - E4. Cross-Runtime Parity — Executive View
  - E5. Governance + Trust Model — Executive View
  - E6. What vOmega Does Not Yet Prove
  - E7. Reproduction Instructions
  - E8. Terminology
- Part II — Deep Technical Body
  - D1. Wire Format: Deterministic CBOR (DCP 2.1) — *[placeholder, see note]*
  - D2. B+ Envelope: ADIE Native Hybrid CBOR Envelope
  - D3. Cross-Runtime Parity: Deep Proof
  - D4. Governance Control Plane (3B)
  - D5. Trust Status & Revocation (3C)
  - D6. End-to-End Assurance (3D / 3D-R1)
  - D7. Cryptographic Identity: Invariants Preserved
  - D8. Security Analysis
  - D9. Defect History — All 44 DEFECTs
  - D10. Positioning Against Adjacent Technologies

---

# Part I — Executive Technical Summary

## E1. Document Purpose and Reading Guide

### E1.1 Purpose

This document specifies the technical capabilities of **vOmega** — the ADIE (Adaptive Defense Intelligence Engine) wire, governance, trust, and end-to-end assurance layers — and provides traceable evidence for each claim. It is a **Technical Capability & Evidence Dossier**, not a marketing document. It contains no pricing, no timelines, and no adoption roadmaps.

Its single purpose is to answer, with evidence, the question:

> *What does vOmega actually prove, at what level of assurance, and how can an independent party verify that?*

### E1.2 Intended Readers

- **Security engineers and cryptographers** evaluating the wire and envelope layers.
- **Governance and compliance architects** evaluating the authority, trust, and decision-boundary models.
- **Independent reviewers and auditors** reproducing results locally.

The document is structured to serve all three, with explicit reading paths defined in Part III (Appendix H of the final document).

### E1.3 What This Document Proves

The document records the technical capabilities established during **Phases 3A through 3D-R1** of the vOmega implementation, along with the evidence supporting each. It documents:

- Deterministic wire behavior across three implementations.
- A governance model that separates decision lifecycle from authorization.
- A trust-status model with historical evaluation semantics.
- An end-to-end assurance path that terminates at an explicit external-execution boundary.

### E1.4 What This Document Does Not Claim

This document does **not** claim:

- Production deployment of any component.
- Cryptographic side-channel or constant-time properties.
- Compliance with any regulatory or industry standard.
- Superiority over adjacent technologies on non-measurable criteria.
- Formal verification of the protocol or its implementations.
- Any capability of vOmega components outside the documented scope.

Limitations, unresolved gaps, and non-blocking findings are recorded as first-class content in §D11 of the final document.

### E1.5 Evidence Discipline

**Rule:** *Every material technical claim carries a traceable evidence pointer.*

- Introductory and transitional statements are not artificially cited.
- Any claim about behavior, counts, or invariants must be traceable through the following chain:

  ```
  Claim
     ↓
  Exact test module / test identifier
     ↓
  Reproduction command
     ↓
  Commit 7683adb (branch vOmega)
     ↓
  Artifact hash (where applicable)
  ```

- A SHA-256 hash alone establishes artifact identity. It does not, by itself, establish that the named test was the one that produced the result. The full chain above is what makes a claim independently reconstructible.

The evidence base for this document is `vOmega-evidence-collection-v3-*.md` (see §E1.7).

### E1.6 Verification Method

An independent reader can verify every claim by:

1. Cloning the repository at commit `7683adb` (branch `vOmega`).
2. Installing the documented environment and dependencies (see Appendix F).
3. Checking frozen-artifact hashes against Appendix A.
4. Running the 46 test suites referenced in `Evidence Collection v3` §5.2 (fresh execution total: 1,070).
5. Running the regression baseline (`tests/account.py`) to reproduce 1,120 regression executions.
6. Interpreting the cross-runtime matrix output as shown in §13.2 of the evidence file.

**No network access is required for test execution once the documented environment and dependencies are installed.**

### E1.7 Canonical Sources

This document references three canonical sources:

| Source | Purpose |
|---|---|
| `docs/vomega/CONTINUITY.md` | 59-section narrative history of every closed stage |
| `docs/vomega/DEFECTS-LOG.md` | 46 DEFECT entries (44 unique numbers), 3 library evaluations, 3 open GAPs |
| `vOmega-evidence-collection-v3-*.md` | Freshly regenerated evidence tables and file hashes |

Where a conflict exists, the evidence file takes precedence for counts and hashes; the continuity log takes precedence for narrative decisions.

---

## E2. The Problem Space

### E2.1 Motivation

Decision systems that produce security-relevant or compliance-relevant outputs increasingly rely on machine-learning and policy-driven components. When such a system emits a decision, four questions recur in regulated and enterprise contexts:

1. **Representation** — Is there a canonical, deterministic way to encode the decision so that two independent readers obtain the identical byte sequence?
2. **Governance** — Is the decision's authority separated from the decision's existence, so that "this decision was created" cannot be silently equated with "this decision is authorized"?
3. **Trust over time** — When the authority that authorized a decision is later suspended or revoked, does the historical record remain intact, and does the *current* status change without rewriting the past?
4. **End-to-end verifiability** — Can a decision certificate be verified from wire bytes through cryptographic signature, governance evaluation, trust status, and manifest emission, without a trusted runtime in the middle?

These are not new questions. They are addressed partially by existing technologies. The purpose of §E2.2 is to identify which specific requirements are **not directly provided** by conventional primitives, and which are provided but require composition.

### E2.2 Requirements Not Directly Provided by Conventional Primitives

The following requirements are not satisfied by any single conventional primitive. Each is listed alongside the primitive(s) commonly considered sufficient for it, and the specific gap that motivates vOmega's layered approach.

#### E2.2.1 Byte-deterministic representation

*Primitives considered:* CBOR (RFC 8949), JSON (RFC 8259), JCS (RFC 8785).

The general CBOR data model permits multiple valid encodings for the same semantic value. **RFC 8949 §4.2 defines deterministic encoding requirements** that protocols may adopt or further restrict. JSON permits arbitrary key ordering and whitespace; JCS constrains JSON but does not extend to CBOR's additional degrees of freedom.

**Gap:** A signature computed over a CBOR document is only meaningful if the reader and the signer agree on the exact byte sequence. vOmega's **DCP 2.1 defines a stricter, protocol-specific deterministic profile** — one that excludes the encoding latitude RFC 8949 permits but leaves optional — and rejects encodings outside that profile with typed error codes. See §D1.

#### E2.2.2 Uniform governance separation

*Primitives considered:* JWT claims (`nbf`, `exp`, `aud`), CMS signed attributes, X.509 extensions.

JWT and CMS provide validity windows and audience constraints. They do not define a decision *lifecycle* distinct from a decision *authorization state*. A claim marked as valid (i.e., within its temporal window) is treated as semantically valid; there is no explicit axis for "this decision was proposed but not yet authorized."

**Gap:** In regulated workflows, "validity of the artifact" and "authorization to proceed" are distinct questions with distinct evidentiary needs. vOmega addresses this by modeling them as two independent axes (`DecisionLifecycle` and `AuthorizationStatus`) that cannot be inferred from one another. See §D4.

#### E2.2.3 Cryptographic identity and the signing framework

*Primitives considered:* COSE (RFC 9052, RFC 9964), JWS (RFC 7515).

In COSE and JWS, the signing input is defined by the respective signing framework — COSE's `Sig_structure` and JWS's JOSE signing input, respectively. Therefore, the identity covered by a signature is tied to the framework-defined signing representation rather than to an independently defined semantic certificate identity.

**Gap:** For long-lived decision records, wire transport may evolve while cryptographic identity must remain stable. vOmega addresses this by computing the To-Be-Signed (TBS) bytes from a canonical JSON representation of the certificate's semantic content — independent of the CBOR envelope used for transport. See §D2 and §D7.

#### E2.2.4 Historical vs current trust evaluation

*Primitives considered:* Certificate Revocation Lists (RFC 5280), OCSP (RFC 6960), short-lived credentials.

CRLs and OCSP provide certificate-status information with temporal metadata, but neither primitive, by itself, defines vOmega's governed append-only history model or a deterministic application-level separation between historical-at-`T` evaluation and current-status evaluation. Short-lived credentials reduce the validity window but do not address the historical question.

**Gap:** Auditing a decision authorized at time `T1` requires answering two distinct questions: "was the authority valid at `T1`?" and "is the authority valid now?" A response that conflates these two questions silently rewrites history. vOmega addresses this with a deterministic resolver that answers both, backed by an append-only assertion store. See §D5.

#### E2.2.5 Cross-language byte equivalence

*Primitives considered:* any single-language implementation of CBOR or JCS.

A single implementation can be internally consistent. What it cannot do is guarantee that a second, independently written implementation in another language will produce the *identical* byte sequence on the same input.

**Gap:** In multi-runtime deployments (e.g., Rust service, JavaScript client, Python audit tool), cross-language byte equivalence is required for signature verification to succeed. vOmega addresses this by running differential test suites across Rust, Python, and JavaScript implementations on a shared vector corpus, and by providing a validated WASM delivery path for the Rust reference implementation. See §D3.

### E2.3 The Specific Question vOmega Answers

vOmega addresses a single composed question:

> Given a decision certificate, its signatures, an authority that authorized it, and a trust-status history, can a reader — using only the wire bytes and publicly available artifacts — verify that the certificate's cryptographic identity, governance state, trust state, and manifest boundary are all consistent, and obtain deterministic answers for both the current time and any specified past time?

The value of vOmega is not that it invents capabilities absent from existing primitives. It is that it **composes** existing primitives — deterministic CBOR, canonical JSON (JCS), cryptographic signatures, structured authority and trust models — under **stricter, explicit invariants**, and then demonstrates the composition independently across three implementations.

The composition establishes:

- A stricter wire profile with deterministic rejection semantics.
- Explicit separation of semantic axes (lifecycle / authorization / trust).
- Historical evaluation semantics that do not rewrite the past.
- Cross-runtime byte equivalence with published evidence.
- An end-to-end assurance boundary that terminates before external execution.

---


---

## E3. What vOmega Proves — at a Glance

### E3.1 Scope of This Section

This section provides a one-page capability summary. Each capability is stated briefly, followed by the **level of evidence** supporting it, expressed through the evidence chain defined in §E1.5.

### E3.2 Evidence Architecture

Every capability in this document is supported by three levels of evidence, which are always distinguished:

```
Capability
   ↓
Executable Evidence
   ↓
Reproducible Artifact / Hash / Test Reference
```

- **Capability** — a statement of what vOmega does.
- **Executable Evidence** — a named, runnable test, suite, or command that demonstrates the capability.
- **Reproducible Artifact / Hash / Test Reference** — a specific file with a SHA-256 hash, or an enumerated test identifier, that a third party can independently verify.

No capability in this document is stated at the first level alone. Every entry in §E3.3–§E3.7 lists all three levels, and additionally the full evidence chain (test module, reproduction command, commit).

For capabilities supported by more than one suite, the reproduction command shown is the **full set of suites** classified to that capability. Where a shorter representative command is more practical, it is labeled explicitly as *Representative reproduction command*.

### E3.3 Deterministic Wire Representation

**Capability.** vOmega defines a strict deterministic CBOR profile (DCP 2.1) that admits only one byte encoding per semantic value for all types the profile permits, and rejects all other encodings with typed error codes.

**Executable Evidence.**

| Language | Suites | Executions |
|---|---|---|
| Python | `tests/vomega/wire/test_error.py`, `test_value.py`, `test_profile.py`, `test_rawcheck.py`, `test_encoder.py`, `test_decoder.py` | 20 + 28 + 31 + 44 + 32 + 39 = **194** |
| JavaScript | `tests/vomega/wire-js/test_error.mjs`, `test_value.mjs`, `test_profile.mjs`, `test_rawcheck.mjs`, `test_encoder.mjs`, `test_decoder.mjs`, `test_index.mjs` | 20 + 28 + 32 + 60 + 43 + 40 + 30 = **253** |
| Rust | `cargo test --release --lib cbor::` | **111** |

**Reproduction command — full set, all implementations:**

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ Python (6 suites) ═══" && \
for f in test_error test_value test_profile test_rawcheck test_encoder test_decoder; do
  PYTHONPATH=src .venv/bin/python tests/vomega/wire/$f.py
done && \
echo "═══ JavaScript (7 suites) ═══" && \
for f in test_error test_value test_profile test_rawcheck test_encoder test_decoder test_index; do
  node tests/vomega/wire-js/$f.mjs
done && \
echo "═══ Rust (cbor::) ═══" && \
cd rust/adie-primitives && cargo test --release --lib cbor:: && cd ../..
```

**Commit.** `7683adb` (branch `vOmega`).

**Reproducible Artifact / Hash.** `rust/adie-primitives/src/cbor/rawcheck.rs` — SHA-256 `bbc9c65917ba8f4aa1758b1e8e5286e1bfc250da4d2b69dd9c0fa6659365d6f0`. `protocol/wire/rawcheck.py` and `js/wire/rawcheck.mjs` are structurally equivalent.

### E3.4 Cross-Runtime Byte Parity

**Capability.** Rust, Python, and JavaScript implementations produce byte-identical output for the same semantic input over a shared test corpus. WASM provides a **validated delivery path for the Rust reference implementation** — it is not treated as a fourth independent implementation.

**Executable Evidence.** The shared vector corpus (`tests/vomega/wire/differential_vectors.json`) contains **44 unique vectors** (14 encode, 12 decode, 18 negative). Three differential test pairs are run against this corpus:

| Pair | Test module | Executions |
|---|---|---|
| Python ↔ Rust (3A.3 D.9b) | `tests/vomega/wire/test_differential.py` | 44 |
| Rust ↔ JavaScript (3A.4A D.8) | `tests/vomega/wire-js/test_differential_rust.mjs` | 45 |
| Python ↔ JavaScript (3A.4A D.9) | `tests/vomega/wire-js/test_differential_python.mjs` | 45 |

- **44 unique vectors** (shared across all three pairs).
- **134 differential executions** across the three pairs (44 + 45 + 45). The two 45s include one architectural boundary test each (A01), beyond the 44 unique vectors.
- **90** refers to the executions closed at the **3A.4A-DIFF stage only** (Rust ↔ JS + Python ↔ JS), and is used only in that stage-closure context.

Additionally:
- WASM: `tests/vomega/wasm/test_wasm_node.mjs` (45) + `test_wasm_precision.mjs` (31) = 76 executions.
- Cross-runtime matrix: `tests/vomega/wire-js/diff-matrix.mjs` — 11 vector classes × 3 languages.

**Reproduction command (all three pairs + matrix):**
```bash
cd ~/Desktop/EnterpriseGuard && \
PYTHONPATH=src .venv/bin/python tests/vomega/wire/test_differential.py && \
node tests/vomega/wire-js/test_differential_rust.mjs && \
node tests/vomega/wire-js/test_differential_python.mjs && \
node tests/vomega/wire-js/diff-matrix.mjs
```

**Commit.** `7683adb`.

**Reproducible Artifact / Hash.** Frozen spec `spec/WIRE-FORMAT-0.2.md` — SHA-256 `b2fee085562dec275572d0ed64faa30bc0375ee9a74fe319b0af984895dcf07f`.

### E3.5 Governance Separation

**Capability.** vOmega models decision state along two independent axes — `DecisionLifecycle` (artifact progression) and `AuthorizationStatus` (current authorization) — with an enforced lifecycle state machine and a single canonical `DecisionContract`. A legacy `DecisionContract` from a prior lineage is retained as a one-directional compatibility adapter and cannot itself authorize.

**Lifecycle state machine.** The state machine defines **64 possible ordered pairs** (8 states × 8 states). Of these, **13 pairs are legal transitions** and **51 are illegal**. The 51 illegal pairs are not 51 independent rules; they are the complement of the 13 legal transitions under the specified semantics.

**Executable Evidence.** All seven suites classified to the 3B governance phase:

| Suite | Executions |
|---|---|
| `test_canonical_lifecycle.py` | 24 |
| `test_lifecycle_sm.py` | 31 |
| `test_canonical_authority.py` | 20 |
| `test_canonical_contract.py` | 19 |
| `test_governance_anti_bypass.py` | 19 |
| `test_compat_b_adapter.py` | 16 |
| `test_wire_bridge.py` | 7 |
| **Total** | **136** |

**Reproduction command (all 7 suites):**
```bash
cd ~/Desktop/EnterpriseGuard && \
for f in test_canonical_lifecycle test_lifecycle_sm test_canonical_authority \
         test_compat_b_adapter test_canonical_contract test_governance_anti_bypass \
         test_wire_bridge; do
  PYTHONPATH=src .venv/bin/python tests/vomega/governance/$f.py
done
```

**Commit.** `7683adb`.

**Reproducible Artifact / Hash.** `src/enterpriseguard/adie/canonical/lifecycle.py` — SHA-256 `cf8e1a2ba7b5c7797543859006ad0c75023758c2957ea812ad08689c70aa39b3`. `src/enterpriseguard/adie/canonical/lifecycle_sm.py` — SHA-256 `cecfad8df33b1a354437975f21648823e2dfbb686e1c526016d47c75676438a6`.

### E3.6 Trust-Status Model with Historical Semantics

**Capability.** vOmega defines a trust-status axis (`ACTIVE`, `SUSPENDED`, `REVOKED`, `EXPIRED`, `SUPERSEDED`) independent of authorization. Status is resolved deterministically from an append-only assertion history, with explicit failure modes for unknown, malformed, and conflicting inputs. For a known authority with no applicable assertion, the resolver returns an explicit governed initial state (not a fallback). Historical queries remain stable as new assertions are appended.

**Resolver outcome table.**

| Input condition | Resolver outcome |
|---|---|
| Unknown authority | `UNKNOWN` (fail-closed) |
| Malformed history | `UNKNOWN` (fail-closed) |
| Conflicting authoritative assertions | `CONFLICT` (fail-closed) |
| Known authority, no applicable assertion | `RESOLVED` / `ACTIVE` with reason `GOVERNED_INITIAL_STATE` |
| Known authority, applicable assertion(s) | `RESOLVED` at the applicable status |

**Executable Evidence.** All nine suites classified to the trust phase:

| Suite | Executions |
|---|---|
| `test_status_semantics.py` | 23 |
| `test_revocation_authority.py` | 21 |
| `test_assertion.py` | 19 |
| `test_resolver.py` | 27 |
| `test_history.py` | 18 |
| `test_temporal_replay.py` | 41 |
| `test_anti_bypass_3c.py` | 13 |
| `test_decision_trust_integration.py` | 13 |
| `test_governed_initial_state.py` | 18 |
| **Total** | **193** |

**Reproduction command (all 9 suites):**
```bash
cd ~/Desktop/EnterpriseGuard && \
for f in test_status_semantics test_revocation_authority test_assertion \
         test_resolver test_history test_temporal_replay test_anti_bypass_3c \
         test_decision_trust_integration test_governed_initial_state; do
  PYTHONPATH=src .venv/bin/python tests/vomega/trust/$f.py
done
```

**Commit.** `7683adb`.

**Reproducible Artifact / Hash.** `src/enterpriseguard/adie/canonical/trust/resolver.py` — SHA-256 `4a3263dbf11c8b4dcc76a74c9ebd3d7ae9e93e918907cd75d4632b403979f6f9`. `src/enterpriseguard/adie/canonical/trust/history.py` — SHA-256 `99b14a828543acb199ebb31fb6c1411ad1ee4b3c72d59c6491856897603d78a5`.

### E3.7 End-to-End Assurance

**Capability.** vOmega provides an end-to-end evaluation path that composes wire validation, cryptographic signature verification (using the existing 3A verifier), authority scope and temporal window checks, trust evaluation against the production `TrustStatusStore`, decision formation via the canonical `DecisionContract`, lifecycle transitions, and emission of a real `ExecutionManifest` — with an explicit external-execution boundary that vOmega never crosses.

**Note on 3D vs 3D-R1.** The end-to-end assurance path was first established in Phase 3D. An independent adversarial review of that phase identified three assurance gaps: cryptographic signatures were not verified in the path, `ExecutionManifest` was represented as a plain dictionary rather than the production contract, and `TrustStatusStore` was bypassed in favor of an in-memory assertion list. All three were addressed in the corrective cycle **3D-R1**. The capability stated above describes the post-remediation state. The individual defects (DEFECT-044, DEFECT-045, DEFECT-046) are recorded in `DEFECTS-LOG.md`.

**Executable Evidence — accounting.**

| Phase | Files | Executions | Composition |
|---|---|---|---|
| 3D original | 10 suites | **196** | base E2E coverage |
| 3D-R1 (new) | 2 new suites | **+24** | `test_e2e_crypto_verification.py` (12) + `test_e2e_trust_store_real.py` (12) |
| 3D-R1 (modified) | 1 upgraded suite | **+5** | `test_e2e_manifest_boundary.py` upgraded from 14 → 19 executions |
| **Total E2E** | **12 suites** | **225** | 196 + 24 + 5 = 225 |

**Reproduction command (all 12 suites):**
```bash
cd ~/Desktop/EnterpriseGuard && \
for f in test_e2e_happy_path test_e2e_trust_matrix test_e2e_lifecycle_sm \
         test_e2e_crypto_gov_mismatch test_e2e_provenance test_e2e_legacy_bypass \
         test_e2e_replay_deterministic test_e2e_failure_injection \
         test_e2e_no_mutation test_e2e_manifest_boundary \
         test_e2e_crypto_verification test_e2e_trust_store_real; do
  PYTHONPATH=src .venv/bin/python tests/vomega/e2e/$f.py
done
```

**Commit.** `7683adb`.

**Reproducible Artifact / Hash.** `src/enterpriseguard/adie/canonical/integration/e2e.py` — SHA-256 `0f16bc2ecb04a9481f9d1950cf0c0c1d0d6aebe37ec170b0e758719e08097894`. `protocol/hybrid/verify.py` (used as the crypto verifier) — SHA-256 `2d285fc50c43ae1c08bc7dd577657925cc08faf6deb9bbd1e3e8d5c6b48a7df5`.

### E3.8 What Is Not Claimed at This Level

The following are explicitly **not** claimed by the capabilities above:

- That the total number of test executions constitutes a proof of security.
- That cross-runtime parity guarantees behavior on inputs outside the tested corpus.
- That the end-to-end path has been exercised in production.
- That the WASM delivery path is a fourth independent implementation.
- That cryptographic correctness implies governance correctness, or vice versa.

Each of these distinctions is preserved throughout the document. They are expanded in §E6 and §D11.

### E3.9 Quantitative Summary (Categorized, Not Summed)

For orientation only, and with the categories deliberately separated:

| Category | Value | Definition |
|---|---|---|
| Fresh test executions | 1,070 | Test executions in the 46-suite evidence run (`Evidence Collection v3` §5.2) |
| Regression baseline executions | 1,120 | Test executions in the regression baseline (`tests/account.py`) |
| Cross-runtime differential executions (all 3 pairs) | 134 | 44 + 45 + 45 executions across Python↔Rust, Rust↔JS, Python↔JS |
| Cross-runtime differential executions (3A.4A-DIFF stage) | 90 | Stage-closure count only; Rust↔JS + Python↔JS |
| WASM executions | 76 | `test_wasm_node.mjs` (45) + `test_wasm_precision.mjs` (31) |
| End-to-end executions | 225 | 3D + 3D-R1 suites combined |
| Governance executions | 136 | 3B suites (7 files) |
| Trust executions | 193 | 3C + 3D-R1 trust-related suites (9 files) |
| Unique differential vectors | 44 | Distinct inputs in `differential_vectors.json` |
| Unique B+ canonical vectors | 5 | `corpus.json` |
| Unique B+ expanded certificates | 25 | `corpus_v2.json` |
| NIST ACVP unique vectors (ML-DSA-65) | 55 | 25 keygen + 15 siggen + 15 sigver |
| Frozen specifications | 5 | `Evidence Collection v3` §2.1 |
| DEFECT headers in `DEFECTS-LOG.md` | 46 | Every `## DEFECT-` header |
| Unique DEFECT numbers | 44 | `005` and `030` unassigned; `017` appears twice by documented classification |
| Library evaluation entries | 3 | `CBOR-LIB-EVAL-001/002/003` |

**Classification note.** The governance and trust totals above include **all suites classified to those phases** in `Evidence Collection v3`. The file-level enumerations in §E3.5 and §E3.6 are complete — they list every suite under each category — and their sums match the totals shown here (136 for governance, 193 for trust).

**Additional Reproducibility Executions — not included in the 46-suite historical total:**

| Category | Value | Definition |
|---|---|---|
| Python wire suites | 194 | 20 + 28 + 31 + 44 + 32 + 39 (see §E3.3) |
| Rust CBOR library tests | 111 | `cargo test --release --lib cbor::` (see §E3.3) |

The 1,070 fresh-execution figure is the **historical 46-suite evidence run** recorded in `Evidence Collection v3`. It does not include the Python wire suites (194) or the Rust CBOR library tests (111), which are reproduced separately as shown above. The two categories are listed here for transparency, not summed into a new aggregate.

**Note on DEFECT numbering.** `DEFECTS-LOG.md` contains 46 top-level `DEFECT-` headers. These correspond to **44 unique DEFECT numbers**. `DEFECT-005` and `DEFECT-030` were never assigned. `DEFECT-017` appears twice: once as the original defect, and once as an architectural classification entry recorded per Commander order on 2026-10-07. `DEFECT-029-WASM` is a suffix variant of `DEFECT-029`, not a separate number. Across the vOmega work, DEFECT-044, DEFECT-045, and DEFECT-046 were recorded and closed during the 3D-R1 corrective cycle.


---

## E4. Cross-Runtime Parity — Executive View

### E4.1 The Claim

Three independent implementations of the same deterministic CBOR profile produce byte-identical output for the same semantic input over a shared test corpus. The three implementations are:

- **Rust** — the reference implementation.
- **Python** — an interoperability adapter.
- **JavaScript** — an independent interoperability adapter.

A fourth artifact, **WASM**, is a validated delivery path for the Rust reference implementation. It is not treated as a fourth independent implementation.

### E4.2 Why This Matters

In deployments where the same certificate is encoded and consumed across multiple runtimes, **byte-level parity is required for deterministic wire interoperability** and for any cryptographic operation that explicitly covers the wire bytes. In vOmega's signature model, however, the certificate signature is computed over the **canonical TBS representation** defined in §E2.2.3, not over the CBOR envelope itself. Wire parity therefore establishes **deterministic transport identity**; it is not, by itself, the precondition for vOmega signature validity.

The distinction matters because vOmega deliberately separates the two layers:

- **Transport identity** — the CBOR envelope bytes. Cross-runtime parity here ensures the envelope is byte-identical across implementations.
- **Cryptographic identity** — the TBS bytes. Cross-runtime parity here ensures the signature is computed over identical inputs across implementations.

Both are required for end-to-end interoperability. They answer different questions. Neither replaces the other.

### E4.3 Evidence Summary

| Category | Value |
|---|---|
| Shared differential corpus (unique vectors) | 44 |
| Differential executions across all three pairs | 134 |
| — Python ↔ Rust | 44 |
| — Rust ↔ JavaScript | 45 |
| — Python ↔ JavaScript | 45 |
| Cross-runtime matrix (11 classes × 3 languages) | 33 comparisons, all matched |
| WASM delivery path — Node | 45 executions |
| WASM delivery path — precision | 31 executions |
| WASM delivery path — Firefox headless | 29 assertions |

**Full detail:** §D3 and `Evidence Collection v3` §5.4.

### E4.4 What Parity Does Not Prove

Byte-level parity over a tested corpus does not imply byte-level parity for inputs outside the corpus. The corpus is fixed at 44 vectors, chosen to cover all CBOR boundary conditions the profile permits. Extensions to the corpus would need to be accompanied by corresponding extensions to the differential suites.

Parity also does not imply that the three implementations fail identically on malformed inputs. A separate rejection-parity layer is included in the differential suite (negative vectors); its results are shown in the cross-runtime matrix. For inputs outside both the positive and negative corpora, rejection behavior may differ and has not been characterized.


---

## E5. Governance + Trust Model — Executive View

### E5.1 Two Independent Axes

vOmega models decision state along two axes that are **not inferable from one another**:

- **DecisionLifecycle** — the artifact's progression through the pipeline: `PROPOSED → VALIDATED → AUTHORIZED → EMITTED → EXECUTED_EXTERNAL → OBSERVED → ASSESSED → CLOSED`.
- **AuthorizationStatus** — whether the decision is currently authorized: `PENDING | AUTHORIZED | DENIED | EXPIRED | SUPERSEDED`.

A decision may remain in an **emitted** lifecycle state after its authorization status later changes. A decision can be *authorized* without having been *executed*. The two axes answer different questions and are enforced by different code paths.

**What this does not permit.** The independence of the axes is not an authorization-bypass. The lifecycle state machine does not permit a transition to `EMITTED` while `AuthorizationStatus` is not `AUTHORIZED`; the two axes are checked independently and enforced jointly at emission time. The phrase "emitted without being authorized" describes a historical/current distinction: a decision can be authorized at `T1`, emitted at `T1`, and later have its authorization status changed to `DENIED` or `EXPIRED` at `T2`. The emitted record remains historically intact; the current authorization status reflects the change.

### E5.2 Trust as a Third, Independent Axis

`TrustStatus` — `ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED` — is a third axis, answering a different question again: **whether the relevant authority is trusted at the time of evaluation.**

The three axes are modeled as three distinct Python enum classes. Sharing a string value (e.g., `"authorized"`) across axes does not imply semantic equivalence; the enums are separate types, and the canonical contract enforces the distinction at construction time.

### E5.3 Historical vs Current Trust

The distinguishing property of the trust model is that a later revocation does not rewrite the past.

- If authority `A` was valid at time `T1`, and authority `A` is revoked at time `T2`, then:
  - Evaluating trust at `T1` returns the status that applied at `T1`.
  - Evaluating trust at `T2` or later returns the revocation.
  - A decision authorized at `T1` records `authority_status_at_authorization = <status at T1>`.
  - That record is not overwritten.

This distinction is enforced by the resolver's `resolve_at(T)` and `resolve_current()` interfaces and is evidenced by the `test_temporal_replay.py` and `test_governed_initial_state.py` suites.

### E5.4 Governed Initial State

For a known authority with no applicable assertion in the trust store, the resolver returns `ACTIVE` with the reason code `GOVERNED_INITIAL_STATE`. This is an explicit domain invariant — not a fallback. Unknown authorities, malformed histories, and conflicting assertions still fail closed:

| Input condition | Resolver outcome |
|---|---|
| Unknown authority | `UNKNOWN` (fail-closed) |
| Malformed history | `UNKNOWN` (fail-closed) |
| Conflicting authoritative assertions | `CONFLICT` (fail-closed) |
| Known authority, no applicable assertion | `RESOLVED` / `ACTIVE` with reason `GOVERNED_INITIAL_STATE` |

### E5.5 What This Enables

An auditor can ask both questions explicitly:

- *"Was authority `A` valid at the moment decision `D` was authorized?"* — historical question, answered deterministically.
- *"Is authority `A` valid now?"* — current-status question, answered deterministically.

The two answers are independent. A model that conflates them cannot answer both without inventing an implicit merge rule; vOmega does not.

### E5.6 What This Does Not Prove

The trust model does not establish that an authority *exists* in any global sense. Authority establishment is an external trust-bootstrap step; the model operates on authorities that have already been introduced. This is documented as a non-blocking finding (F-04, F-05) and expanded in §D11.

**Full detail:** §D4 and §D5.


---

## E6. What vOmega Does Not Yet Prove

This section is a first-class part of the document. It exists to make the boundary of the dossier explicit. Anything not stated as proven in §E3, §E4, or §E5 falls into one of the categories below.

### E6.1 Production Deployment

No component of vOmega has been deployed in production. All test executions reported in this document were performed in a controlled local environment (see §E7 for the exact reproduction steps). The end-to-end assurance path in particular has been exercised only against constructed fixtures and the corpus in `tests/vomega/`.

### E6.2 Cryptographic Side-Channel Resistance

No constant-time analysis, timing analysis, or side-channel evaluation has been performed on the wire, envelope, governance, trust, or end-to-end layers. The document makes no claim regarding timing behavior, cache behavior, or resistance to side-channel attacks.

### E6.3 Formal Verification

The protocol and its implementations have not been formally verified. No machine-checked proof of correctness, determinism, or protocol invariants exists. The evidence for each capability is empirical — test executions and cross-runtime differential comparisons — not deductive.

### E6.4 Compliance and Certification Status

vOmega has not been evaluated against any regulatory certification scheme (e.g., Common Criteria, ISO 27001) or any industry compliance framework. The document does not claim compliance with any external standard.

A distinct point is **algorithm validation**. The ML-DSA-65 algorithm implemented in vOmega is defined by **FIPS 204**, and the test evidence includes NIST ACVP vector executions (55 unique vectors, across three languages). ACVP vector execution demonstrates conformance to the published test vectors; it is **not** equivalent to a FIPS 140-3 module validation, a CMVP certificate, or a formal compliance attestation. The three categories — standard conformance, algorithm test-vector conformance, and certification — are kept distinct throughout this document.

### E6.5 Global Trust Root Provisioning

The trust model operates on authorities that are provided as inputs. vOmega does not, at this stage, define a mechanism for establishing a global trust root or for provisioning authorities from a root of trust. This is documented as an open gap (§D11, F-04/F-05).

### E6.6 Executor Integration

The end-to-end assurance path terminates at an explicit external-execution boundary. vOmega does not perform external execution; it does not integrate with any executor. The `EXECUTED_EXTERNAL` lifecycle state has no runtime owner by design (F-07).

### E6.7 Multi-Tenant Operation

The governance and trust layers do not currently model multi-tenant isolation. Any multi-tenant deployment would need to define authority scoping, store partitioning, and cross-tenant boundary rules beyond what is documented here.

### E6.8 Behavior Outside the Tested Corpus

Cross-runtime byte parity is established for the 44-vector differential corpus. Behavior on inputs outside the corpus — whether positive, negative, or boundary-adjacent — has not been characterized. Rejection-code classification is validated for the enumerated negative vectors; extension beyond them would require new evidence.

### E6.9 Library Trust Boundaries

The three CBOR libraries used by the implementations (`ciborium` for Rust, `cbor2` for Python, `cbor@9` for JavaScript) are treated as primitives, not as oracles. Their behavior differences from one another are documented in `CBOR-LIB-EVAL-001/002/003` and are compensated at the profile layer. None of the three libraries has been independently audited by this project.

### E6.10 Non-Blocking Findings

Additional non-blocking findings (F-06, F-08, F-09, F-10, F-11) are enumerated in §D11 and in `DEFECTS-LOG.md`. None of them blocks the capabilities claimed in §E3; each is documented so that a reader can factor it into their own assessment.

### E6.11 Change Since Freeze

This section is explicitly maintained as a moving boundary. As capabilities are added or gaps are closed, the corresponding items move from §E6 into §E3. The version of §E6 in this document reflects the state at commit `7683adb`.

---

## E7. Reproduction Instructions

### E7.1 Environment Prerequisites

| Component | Version |
|---|---|
| Operating system | (not inferred; see note) |
| Linux kernel | 7.0.0-31-generic |
| Python | 3.12.3 |
| Rust | 1.99.0 |
| Cargo | 1.99.0 |
| Node.js | 20.20.2 |
| npm | 10.9.9 |
| Firefox (for browser path) | 155.0.1 |

**Note on the operating-system line.** The kernel version above is the one under which the evidence was generated. The specific Linux distribution is not asserted here, because it cannot be inferred from the test output alone. A reader reproducing the evidence may use any Linux distribution providing the documented kernel and toolchain versions.

**Python dependencies** are pinned in `requirements.txt`. **Node.js dependencies** are pinned in `js/package.json`. **Rust dependencies** are pinned in `rust/adie-primitives/Cargo.lock`.

**No network access is required for test execution once the documented environment and dependencies are installed.**

### E7.2 Step 1 — Checkout at the Documented Commit

```bash
git clone https://github.com/Bashar100-A/EnterpriseGuard.git
cd EnterpriseGuard
git checkout 7683adb
```

**Resulting state (verify with the two commands below):**

```bash
git rev-parse --verify HEAD
# Expected: 7683adb...

git branch --show-current
# Expected: (empty output — detached HEAD)
```

**Note on branch reference.** The documented commit `7683adb` is the tip of branch `vOmega` on `origin` at the time this document was generated. To verify that the branch and the commit are still aligned:

```bash
git fetch origin vOmega
git rev-parse origin/vOmega
# Expected: 7683adb...
```

If `origin/vOmega` no longer points at `7683adb`, the branch has advanced since this document was written. The documented commit remains the authoritative reference for reproducing the evidence in this dossier; later commits on the branch are subsequent to the evidence.

**`git checkout <commit>` produces a detached HEAD.** This is intentional for reproducibility: the reader verifies the exact commit recorded in this document, not "whatever the branch currently points at."

### E7.3 Step 2 — Verify Frozen Specification Hashes

```bash
sha256sum \
  spec/WIRE-FORMAT-0.2.md \
  spec/WIRE-FORMAT-0.2-AMENDMENT-1.md \
  spec/WIRE-FORMAT-0.2-AMENDMENT-2.md \
  docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md \
  docs/vomega/decisions/DECISION-0.4-CBOR-ENVELOPE.md
```

**Expected:** five SHA-256 values matching the table in Appendix A.

### E7.4 Step 3 — Run the Python Wire Suites

```bash
for f in test_error test_value test_profile test_rawcheck test_encoder test_decoder; do
  PYTHONPATH=src .venv/bin/python tests/vomega/wire/$f.py
done
```

**Expected:** 194 executions, 0 failures.

### E7.5 Step 4 — Run the JavaScript Wire Suites

```bash
for f in test_error test_value test_profile test_rawcheck test_encoder test_decoder test_index; do
  node tests/vomega/wire-js/$f.mjs
done
```

**Expected:** 253 executions, 0 failures.

### E7.6 Step 5 — Run the Rust CBOR Library Tests

```bash
cd rust/adie-primitives
cargo test --release --lib cbor::
```

**Expected:** 111 tests passed.

### E7.7 Step 6 — Run the 46-Suite Evidence Set

The 46-suite evidence set used in `Evidence Collection v3` is the **exact enumerated suite list** documented in `Evidence Collection v3` §5.2. It must be reproduced using that enumerated manifest, **not** by interpreting `tests/vomega/` as "all suites currently present."

Aggregate count: **1,070 executions.**

The separately reproduced suites — Python wire (194 executions) and Rust CBOR library tests (111 executions) — are **not** part of this historical total. They are recorded under *Additional Reproducibility Executions* in §E3.9.

The enumeration manifest is reproduced in **Appendix F** of the final document; §E7.7 refers to it rather than re-declaring the 46-suite list inline.

### E7.8 Step 7 — Run the Regression Baseline

```bash
.venv/bin/python tests/account.py
```

**Expected:** `Grand total (unique, non-overlapping) = 1120`.

### E7.9 Step 8 — Run the Cross-Runtime Matrix

```bash
node tests/vomega/wire-js/diff-matrix.mjs
```

**Expected:** the 11-class × 3-language matrix in which every row and column matches. See `Evidence Collection v3` §13.2 for the exact expected output.

### E7.10 Step 9 — Verify a Single Claim End-to-End

For a worked example, consider the claim:

> *CBOR uint `1` is accepted; CBOR float64 `1.0` is rejected by the rawcheck gate.*

**Reproduce as follows:**

```bash
echo '{"op":"decode","cbor_hex":"01"}' | \
  .venv/bin/python protocol/wire/bin/adie-cbor.py
# Expected: {"value": {"t": "uint", "v": 1}}

echo '{"op":"decode","cbor_hex":"fb3ff0000000000000"}' | \
  .venv/bin/python protocol/wire/bin/adie-cbor.py
# Expected: {"error": "E_WIRE_FLOAT", "detail": "..."}
```

This reproduces **the same wire-level cases covered by the A01 architectural boundary test** in the JavaScript rawcheck suite (`test_rawcheck.mjs`, A01). The commands above exercise the cases through the Python CLI, not by running `test_rawcheck.mjs` itself.

### E7.11 Failure Reporting

If any expected result does not reproduce, the divergence is itself evidence. It should be reported with:

- The exact command executed.
- The exact output received.
- The expected output per this document.
- The environment (per §E7.1).

Divergences from the documented evidence are treated as defects, not as acceptable variation.


---

## E8. Terminology

### E8.1 Formatting Convention

Standard names and standards identifiers (RFC numbers, enum names, algorithm names) appear in their original form throughout this document. Terms introduced by vOmega are in mono-spaced style on first use.

### E8.2 Core Protocol Terms

| Term | Meaning |
|---|---|
| **DCP 2.1** | ADIE's Deterministic CBOR Profile, version 2.1. A stricter subset of CBOR (RFC 8949) adopted by vOmega. |
| **B+** | The ADIE Native Hybrid CBOR Envelope (Model B+). A deterministic CBOR envelope that carries an ADIE semantic certificate; **not** a `COSE_Sign` or `COSE_Sign1` object. |
| **TBS** | To-Be-Signed bytes. In vOmega, `ADIE-SIG-V2\0` ‖ JCS(certificate_without_signatures). Unchanged from Phase 1 and Phase 2. |
| **JCS** | JSON Canonicalization Scheme (RFC 8785). |
| **ClaimRoot** | The SHA-256 digest over the 13 named fields of a DCP certificate; part of the semantic identity. |
| **Wire bytes** | The byte sequence produced by the DCP 2.1 deterministic CBOR profile and carried inside the B+ envelope. |
| **Rawcheck** | The byte-level gate that runs before the semantic CBOR decoder. It is the authority for wire-level invariants that semantic decoding may erase. |
| **Profile** | The semantic layer that validates decoded values against DCP 2.1 invariants (integer-keyed maps, sorted keys, depth, types). |

### E8.3 Governance and Decision Terms

| Term | Meaning |
|---|---|
| **DecisionContract** | The canonical ADIE decision artifact, produced by `enterpriseguard.adie.decision`. |
| **DecisionLifecycle** | The artifact-progression axis: `PROPOSED` → `VALIDATED` → `AUTHORIZED` → `EMITTED` → `EXECUTED_EXTERNAL` → `OBSERVED` → `ASSESSED` → `CLOSED`. |
| **AuthorizationStatus** | The authorization axis, independent of lifecycle. Values: `PENDING`, `AUTHORIZED`, `DENIED`, `EXPIRED`, `SUPERSEDED`. |
| **Authority** | The explicit governance authority object that authorizes a decision, separate from any evidence. |
| **RevocationAuthority** | An explicit capability to assert trust-status changes on an enumerated subject, with a scope and a validity window. |
| **TrustStatus** | The trust axis, independent of lifecycle and authorization. Values: `ACTIVE`, `SUSPENDED`, `REVOKED`, `EXPIRED`, `SUPERSEDED`. |
| **TrustStatusAssertion** | An immutable record of one status change, carrying `asserted_at`, `effective_at`, `observed_at`, and the asserting authority. |
| **TrustStatusStore** | The append-only assertion history, backed by a hash-chained JSONL store. |
| **GOVERNED_INITIAL_STATE** | The reason code returned by the trust resolver when a known authority has no applicable assertion; outcome is `ACTIVE`. Not a fallback. |
| **ExecutionManifest** | The ADIE-to-execution boundary contract. Emitted by the governance layer; consumed by external systems. vOmega does not execute. |
| **E2EOutcome** | The outcome classifier of the end-to-end assurance path, distinguishing eight rejection classes plus `ACCEPTED`. |
| **EXECUTES_SECURITY_ACTIONS** | An invariant that is `False` throughout vOmega. No vOmega component performs external security actions. |

**Enum completeness (explicit list form, avoiding table-cell ambiguity):**

```
DecisionLifecycle  (8 values)
    PROPOSED, VALIDATED, AUTHORIZED, EMITTED,
    EXECUTED_EXTERNAL, OBSERVED, ASSESSED, CLOSED

AuthorizationStatus  (5 values)
    PENDING, AUTHORIZED, DENIED, EXPIRED, SUPERSEDED

TrustStatus  (5 values)
    ACTIVE, SUSPENDED, REVOKED, EXPIRED, SUPERSEDED
```

**Cross-axis note.** `AuthorizationStatus` and `TrustStatus` each contain the values `EXPIRED` and `SUPERSEDED` as strings, but they are distinct Python enum classes. Sharing a string value does not imply semantic equivalence across axes. The canonical `DecisionContract` enforces axis separation at construction time (see §E5.1).

### E8.4 Standards Referenced

| Identifier | Title |
|---|---|
| RFC 5280 | Internet X.509 Public Key Infrastructure Certificate and CRL Profile |
| RFC 6960 | X.509 Internet Public Key Infrastructure Online Certificate Status Protocol (OCSP) |
| RFC 6962 | Certificate Transparency |
| RFC 7515 | JSON Web Signature (JWS) |
| RFC 8259 | The JavaScript Object Notation (JSON) Data Interchange Format |
| RFC 8785 | JSON Canonicalization Scheme (JCS) |
| RFC 8949 | Concise Binary Object Representation (CBOR) |
| RFC 9052 | CBOR Object Signing and Encryption (COSE): Structures and Process |
| RFC 9964 | ML-DSA for JSON Object Signing and Encryption (JOSE) and CBOR Object Signing and Encryption (COSE) |
| FIPS 204 | Module-Lattice-Based Digital Signature Standard |

### E8.5 Governance Terms Used by the Repository

| Term | Meaning |
|---|---|
| **DEFECT** | An entry in `docs/vomega/DEFECTS-LOG.md` recording a discovered defect, its root cause, its fix, and the regression. |
| **CBOR-LIB-EVAL** | An entry in `DEFECTS-LOG.md` recording a CBOR library evaluation and selection rationale. |
| **GAP** | An entry in `DEFECTS-LOG.md` recording an open gap that is not a defect but is a known limitation. |
| **RISK** | An entry recording an active risk under monitoring. The only active risk tracked by vOmega is RISK-3.3 (disk headroom). |
| **CONTINUITY** | The narrative history in `docs/vomega/CONTINUITY.md`, section-numbered by phase and stage. |
| **Evidence Collection** | The regenerated evidence file `vOmega-evidence-collection-v3-*.md` on which this document's counts and hashes are based. |

### E8.6 Notational Conventions

- **Executions** refers to individual test invocations (each `check()` call, each Rust `#[test]` execution).
- **Unique vectors** refers to distinct inputs in a corpus, counted once regardless of how many test pairs consume them.
- **Regression executions** refers to the number reported by `tests/account.py` as `Grand total`.
- These three categories are never summed. See §E3.9.


---
# Part II — Deep Technical Body

<!-- ============================================================ -->
<!-- D1 — WIRE FORMAT: DETERMINISTIC CBOR (DCP 2.1)               -->
<!--                                                              -->
<!-- STATUS: PLACEHOLDER — text was frozen in a prior              -->
<!-- conversation, but the D1 Draft 01 body is NOT available in    -->
<!-- the current recovery context. Per Commander's extraction       -->
<!-- rule ("Extraction, not reinterpretation"), D1 is NOT           -->
<!-- reconstructed from cross-references. Awaits Commander          -->
<!-- paste of D1 Draft 01 text, or Commander authorization to       -->
<!-- write D1 in a separate step.                                  -->
<!--                                                              -->
<!-- What IS available about D1 (from cross-references):            -->
<!--   • §D1.1 — Specification lineage: WIRE-FORMAT-0.2 + Amt 1+2  -->
<!--   • §D1.5 — The 14 E_WIRE_* codes (see E8, D2.4)              -->
<!--   • §D1.6 — Rawcheck (wire authority) vs Profile (semantic)   -->
<!--   • §D1.7.1 — Python 194, JS 253, Rust 111 (see E3.3)         -->
<!--   • A01 architectural boundary test (see E3.4, D3.7.4)        -->
<!--   • Map ordering, integer boundaries, non-canonical rejection  -->
<!--     all reproduced and verified (see D1 verification report)   -->
<!-- ============================================================ -->

## D1. Wire Format: Deterministic CBOR (DCP 2.1)

**[PLACEHOLDER — awaiting Commander text]**

The full D1 Draft 01 text is not available in the current recovery context. The section will be inserted here once the text is provided by the Commander or explicitly authorized for reconstruction.

For the reader's orientation, the following cross-referenced facts about D1 are available elsewhere in this document:

| Cross-reference | Location |
|---|---|
| Specification lineage (WIRE-FORMAT-0.2 + Amendments) | §D2.1, this document |
| The 14 `E_WIRE_*` rejection codes | §E8.2, §D2.4 |
| Rawcheck-as-wire-authority vs Profile-as-semantic-authority | §E8.2, §D3.7 |
| Python (194), JavaScript (253), Rust (111) wire test counts | §E3.3 |
| A01 architectural boundary test | §E3.4, §D3.7.4 |
| Cross-runtime rejection-code parity | §D3.7 |

**No claims in this section are made beyond what is cited above.**

---

## D2. B+ Envelope: ADIE Native Hybrid CBOR Envelope

**Part II, Section D2.**
**Scope:** the CBOR envelope that carries a DCP 2.1 semantic certificate.
**Frozen upstream:** `WIRE-FORMAT-0.2-AMENDMENT-1.md`, `WIRE-FORMAT-0.2-AMENDMENT-2.md`, `DECISION-0.3-COSE-ARCH.md`, `DECISION-0.4-CBOR-ENVELOPE.md` (see §D2.1).

### D2.1 Specification Lineage

The B+ envelope is defined by four frozen artifacts, built on top of the base wire specification:

| Artifact | Size (bytes) | SHA-256 |
|---|---|---|
| `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md` | 8337 | `7cb607be51b7a5d1afbb78611d66b0db3ef3c8cdc30de15ee41b3a701e4762ab` |
| `spec/WIRE-FORMAT-0.2-AMENDMENT-2.md` | 9718 | `5e02bf89cfa347b7ff4b0b798ed0e7030866dc1f2989e060e8aca54768f844ac` |
| `docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md` | 2980 | `e9c0cd35637a21b5c5bc7268b084694805a79f4c55df06d9d65859f150a36412` |
| `docs/vomega/decisions/DECISION-0.4-CBOR-ENVELOPE.md` | 2655 | `848a52d1e027637c308e092bf5b3cee29fcbecdf8c1a179c971c4efc3dfd8ba2` |

**Amendment-1** records the architectural decision that the envelope is an ADIE-native deterministic CBOR object, **not** a `COSE_Sign` or `COSE_Sign1` object per RFC 9052, and specifies the terminology overrides that follow from that decision.

**Amendment-2** records the wire-content model adopted for the envelope: top-level integer-keyed CBOR, nested ADIE objects carried as canonical JCS UTF-8 byte strings, with three explicitly retained native-CBOR fields.

**DECISION-0.3** and **DECISION-0.4** record the Commander decisions that produced Amendments 1 and 2 respectively. They are preserved as narrative records.

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && sha256sum \
  spec/WIRE-FORMAT-0.2-AMENDMENT-1.md \
  spec/WIRE-FORMAT-0.2-AMENDMENT-2.md \
  docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md \
  docs/vomega/decisions/DECISION-0.4-CBOR-ENVELOPE.md
```

**Commit.** `7683adb` (branch `vOmega`).

### D2.2 Architectural Decision — Model B+

The B+ envelope is the outcome of an explicit architectural decision recorded in Amendment-1 (and DECISION-0.3). The decision is a **composition choice**, not a claim that other frameworks are incorrect or insufficient.

#### D2.2.1 The three candidate models

During the design of the vOmega wire layer, three models were considered for how to combine ADIE's semantic certificate with CBOR encoding:

| Model | Description | Source of signing input |
|---|---|---|
| **A — COSE-native** | Use RFC 9052 `COSE_Sign` or `COSE_Sign1` as the signing framework. | COSE `Sig_structure`. |
| **B — CBOR transport, ADIE-native signing** | Use CBOR strictly as a deterministic transport container; the signature is computed over the ADIE-native TBS (JCS-based). | `ADIE-SIG-V2\0 ‖ JCS(certificate_without_signatures)`. |
| **C — Hybrid** | Mix A and B: use COSE for one layer, JCS for another. | Ambiguous by construction. |

Model A was the closest to a "standards-compliant COSE implementation." Model B preserves the cryptographic identity that already exists in Phase 1 and Phase 2 of the ADIE implementation. Model C was excluded because it would silently mix two signing contexts.

#### D2.2.2 Why Model A was not selected

Model A would change the bytes over which signatures are computed — from the ADIE TBS to a COSE `Sig_structure`. That is a change in cryptographic identity:

- Every signature produced under Phase 1 and Phase 2 of the ADIE implementation would need to be re-issued.
- Every published vector would require re-publication.
- The Phase 1 and Phase 2 cryptographic evidence base would be invalidated.

This is not a claim about COSE's correctness or quality. It is a statement of what changes if the signing framework changes at this point in the ADIE implementation's history.

#### D2.2.3 Why Model B was selected

Model B (B+) preserves the ADIE cryptographic identity chain unchanged:

- Phase 1 → Phase 2 → vOmega share the same TBS definition.
- CBOR is used as a deterministic transport encoding layered above the ADIE-native signature layer.
- No existing signature is invalidated.
- No published vector requires re-issuance.

The decision is recorded in Amendment-1 §A2 and DECISION-0.3. A future COSE-native profile is reserved (Amendment-1 §A6), with a new domain tag distinct from `ADIE-SIG-V2\0`, to be specified in a separate wire format version. vOmega does not implement that future profile.

#### D2.2.4 What "ADIE-native" means here

The term *ADIE-native* in this context refers specifically to the **signing input** — the byte sequence over which RS256 and ML-DSA-65 signatures are computed. It does not describe the transport format (CBOR), nor the container structure (the B+ envelope map), nor the field encodings (nested JCS bytes).

- **Transport format:** CBOR, defined by RFC 8949, restricted by DCP 2.1.
- **Signing input:** `ADIE-SIG-V2\0 ‖ JCS(certificate_without_signatures)` — a byte sequence computed independently of the CBOR envelope.
- **Container structure:** the B+ envelope — a top-level CBOR map with 18 integer-labeled entries.

### D2.3 Wire Model

The B+ envelope is a top-level CBOR map with **18 integer-labeled entries**, defined by Amendment-2 §A2. Three categories of wire content are distinguished:

1. **Scalar top-level fields** (2 fields) — carried as native CBOR text.
2. **Nested ADIE objects** (13 fields) — carried as **canonical JCS UTF-8 byte strings**.
3. **Retained native CBOR fields** (3 fields) — `proofs`, `claim_root`, `signatures`.

#### D2.3.1 Category 1 — Scalar top-level fields

Two fields are carried as native CBOR text strings:

- `dcp_version` (label 1) — a text string, e.g., `"2.1"`.
- `claim_id` (label 2) — a text string.

These are scalars and do not need JCS wrapping.

#### D2.3.2 Category 2 — Nested ADIE objects as JCS byte strings

Thirteen fields are carried as CBOR byte strings whose payload is the **canonical JCS UTF-8 representation** of the corresponding nested JSON object:

- `issuer` (label 3)
- `subject` (label 4)
- `request` (label 5)
- `context` (label 6)
- `policy` (label 7)
- `model` (label 8)
- `data` (label 9)
- `runtime` (label 10)
- `output` (label 11)
- `binding` (label 12)
- `temporal` (label 13)
- `evidence` (label 14)
- `authoring` (label 15)

**Why JCS bytes?** The base specification (`WIRE-FORMAT-0.2.md` §7) requires that all CBOR maps use unsigned-integer keys. The nested ADIE objects, as defined in Phase 1 and Phase 2, use text-string keys (e.g., `{"model_id": "credit-v7"}`). Two resolutions were considered:

| Resolution | Description |
|---|---|
| **R1** | Register integer labels for every nested key. |
| **R2** | Carry nested objects as canonical JCS byte strings. |
| **R3** | Permit text keys in nested maps. |

R1 requires a large label registry with its own versioning and collision management, essentially a second serialization language. R3 weakens the map-key discipline established in the base specification. **R2 was selected** (DECISION-0.4), and is recorded in Amendment-2 §A2.

Under R2, the CBOR envelope carries two parallel identities:

- **CBOR transport identity** — the deterministic byte sequence that constitutes the envelope.
- **JCS semantic identity** — the canonical JSON bytes carried inside the envelope, which are the same bytes consumed by the TBS builder.

This is a deliberate separation. It allows the CBOR layer to evolve (for example, adding envelope-level metadata) without altering the semantic identity that signatures cover.

#### D2.3.3 Category 3 — Retained native CBOR fields

Three fields are carried as native CBOR types, not as JCS byte strings:

| Label | Field | Wire type | Rationale |
|---|---|---|---|
| 16 | `proofs` | CBOR array | The current version permits only the empty array. Non-empty `proofs` semantics are reserved for a future amendment. |
| 17 | `claim_root` | CBOR byte string (32 bytes) | The semantic value is `sha256:<64-hex>`. Carrying the raw 32-byte digest on the wire avoids redundant hex encoding. |
| 18 | `signatures` | CBOR array of signature objects | Each signature object is a CBOR map with three integer labels: `1` = `alg` (text), `2` = `key_id` (text), `3` = `value` (bytes). The `value` field carries the raw signature bytes, not a base64 representation. |

The `signatures` field's inner labels (`1`, `2`, `3`) are registered in the base specification §4.2. They are distinct from the top-level label space (`1..18`); the two namespaces do not overlap because they appear at different map nesting levels.

### D2.4 The 18-Label Registry

The full top-level registry, per Amendment-2 §A2:

| Label | Field | Wire type |
|---|---|---|
| 1 | `dcp_version` | CBOR text |
| 2 | `claim_id` | CBOR text |
| 3 | `issuer` | CBOR byte string (canonical JCS UTF-8) |
| 4 | `subject` | CBOR byte string (canonical JCS UTF-8) |
| 5 | `request` | CBOR byte string (canonical JCS UTF-8) |
| 6 | `context` | CBOR byte string (canonical JCS UTF-8) |
| 7 | `policy` | CBOR byte string (canonical JCS UTF-8) |
| 8 | `model` | CBOR byte string (canonical JCS UTF-8) |
| 9 | `data` | CBOR byte string (canonical JCS UTF-8) |
| 10 | `runtime` | CBOR byte string (canonical JCS UTF-8) |
| 11 | `output` | CBOR byte string (canonical JCS UTF-8) |
| 12 | `binding` | CBOR byte string (canonical JCS UTF-8) |
| 13 | `temporal` | CBOR byte string (canonical JCS UTF-8) |
| 14 | `evidence` | CBOR byte string (canonical JCS UTF-8) |
| 15 | `authoring` | CBOR byte string (canonical JCS UTF-8) |
| 16 | `proofs` | CBOR array (empty only, current version) |
| 17 | `claim_root` | CBOR byte string (32 raw bytes) |
| 18 | `signatures` | CBOR array of {1: text, 2: text, 3: bytes} |

The envelope's top-level map keys are therefore **all integers in the range 1..18**. No text keys appear at the top level.

### D2.5 TBS and Cryptographic Identity — Unchanged

The B+ envelope does not participate in signature computation. The To-Be-Signed bytes are defined by `spec/HYBRID-CRYPTO-0.1.md` §5:

```
TBS = "ADIE-SIG-V2\0" ‖ JCS(certificate_without_signatures)
```

where:

- `"ADIE-SIG-V2\0"` is the 12-byte domain tag, unchanged from Phase 1 and Phase 2.
- `JCS(certificate_without_signatures)` is the RFC 8785 canonical JSON of the certificate with the `signatures` field removed (not nulled).

The TBS is computed from the **semantic certificate**, not from the CBOR envelope. The envelope is a transport representation; it carries the semantic certificate but does not define its cryptographic identity.

This property is preserved across vOmega's three implementation languages:

- The Python builder consumes a certificate dictionary and produces TBS bytes.
- The JavaScript builder does the same.
- The Rust reference and the envelope endpoint operate on the same TBS via the `protocol/hybrid/tbs.py` and `protocol/hybrid/tbs.mjs` implementations.

**Verification.** The domain tag is exactly 12 bytes:

```bash
python3 -c "
from protocol.hybrid.tbs import DOMAIN_TAG
print('len:', len(DOMAIN_TAG))
print('hex:', DOMAIN_TAG.hex())
"
```

Expected:

```
len: 12
hex: 414449452d5349472d563200
```

**Executable evidence:**

| Language | Suite | Tests |
|---|---|---|
| Python | `tests/vomega/hybrid/test_tbs.py` | 12 executions covering TBS construction |
| Python | `tests/vomega/hybrid/test_e2e.py` | 11 executions covering end-to-end signing & verification |
| Python | `tests/vomega/b-plus/test_bplus_e2e.py` | 10 executions; H09 confirms TBS byte-identity after envelope round-trip |
| Python | `tests/vomega/e2e/test_e2e_happy_path.py` | 14 executions (post-3D-R1) |

**Reproduction (TBS byte-identity check via B+ E2E):**

```bash
cd ~/Desktop/EnterpriseGuard && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_e2e.py | grep "H09"
```

Expected:

```
[PASS] H09 TBS byte-identical after envelope round-trip
```

### D2.6 Deterministic Envelope Bytes

For a fixed semantic certificate, the B+ envelope is a deterministic byte sequence. The size and content depend only on the certificate's fields, not on runtime, platform, or encoding order.

#### D2.6.1 Envelope size on the reference corpus

The B+ canonical corpus (`tests/vomega/b-plus/corpus.json`) contains 5 real DCP 2.1 certificates. For each certificate, the envelope size is:

```
5,203 bytes
```

The size is identical across all 5 corpus entries because the corpus is constructed with the same shape (same number of fields, same field structures). The size is reported by the size baseline suite:

```bash
cd ~/Desktop/EnterpriseGuard && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_sizes.py
```

The suite reports:

- JSON certificate: 6,658 bytes
- Sum of JCS field bytes: 1,367 bytes
- Raw signature bytes (RS256 + ML-DSA-65): 3,565 bytes
- B+ envelope: 5,203 bytes
- Delta vs JSON: −1,455 bytes

The negative delta is explained by the removal of base64 overhead: the CBOR envelope carries signature bytes as raw bytes, whereas the JSON certificate carries them as base64-encoded text, adding approximately 33% overhead to a 3,565-byte payload.

#### D2.6.2 Determinism

For a fixed certificate, repeated encoding produces identical bytes. This is tested by:

- `test_encoder.mjs` — E31 (`deterministic repeated encoding`).
- `test_bplus_e2e.py` — H01 (`envelope build`) — builds the envelope for a corpus entry, then rebuilds it and compares.

**Reproduction:**

```bash
cd ~/Desktop/EnterpriseGuard && \
node tests/vomega/wire-js/test_encoder.mjs | grep "E31"
```

Expected:

```
[PASS] E31 deterministic repeated encoding
```

#### D2.6.3 What "deterministic" covers

Determinism covers:

- **Byte-level identity.** Same semantic certificate → identical envelope bytes across runs.
- **Field ordering.** The top-level labels are emitted in ascending order (1, 2, 3, …, 18). This is enforced by DCP 2.1's map-key ordering rules (§D1.4).
- **JCS canonicality.** The nested byte strings are canonical JCS; any deviation is rejected at parse time (see §D2.3.2 and the validator described in Amendment-2 §A3).

Determinism does not cover:

- **Cross-certificate identity.** Different certificates produce different envelopes. Trivially, the envelope is a function of its input.
- **Stability under field addition.** Adding a new field to the certificate changes the envelope. This is by design — the envelope carries the certificate's actual content.

### D2.7 Cross-Runtime Byte Parity

For each certificate in the B+ canonical corpus, the envelope is byte-identical across Rust, Python, and JavaScript implementations.

#### D2.7.1 Parity result

Across the 5 certificates in `tests/vomega/b-plus/corpus.json`:

| Pair | Result |
|---|---|
| Rust ↔ Python | 5/5 byte-identical |
| Rust ↔ JavaScript | 5/5 byte-identical |

Each pair is verified by independent subprocess runs of the corresponding envelope endpoint. The comparison is on complete byte strings, not on digests.

**Reproduction:**

```bash
cd ~/Desktop/EnterpriseGuard && \
python3 -c "
import json, subprocess
from pathlib import Path

ROOT = Path('.').resolve()
RUST = ROOT / 'rust/adie-primitives/target/release/adie-cbor-envelope'
PY_S = ROOT / 'protocol/wire/bin/adie-cbor-envelope.py'
JS_S = ROOT / 'js/wire/bin/adie-cbor-envelope.mjs'

corpus = json.loads((ROOT / 'tests/vomega/b-plus/corpus.json').read_text())
for v in corpus['positive']:
    cert = v['certificate']
    payload = json.dumps({'op': 'build', 'certificate_json': json.dumps(cert)})
    r = json.loads(subprocess.run([str(RUST)], input=payload, capture_output=True, text=True).stdout)
    p = json.loads(subprocess.run([str(ROOT/'.venv/bin/python'), str(PY_S)], input=payload, capture_output=True, text=True, cwd=str(ROOT)).stdout)
    j = json.loads(subprocess.run(['node', str(JS_S)], input=payload, capture_output=True, text=True).stdout)
    print(f\"{v['id']}: Rust=Py={r['envelope_hex']==p['envelope_hex']} Rust=JS={r['envelope_hex']==j['envelope_hex']}\")
"
```

Expected:

```
P01: Rust=Py=True Rust=JS=True
P02: Rust=Py=True Rust=JS=True
P03: Rust=Py=True Rust=JS=True
P04: Rust=Py=True Rust=JS=True
P05: Rust=Py=True Rust=JS=True
```

#### D2.7.2 Round-trip parity

Beyond encoding parity, the envelope is also verified to support byte-stable **round-trips**:

```
encode(cert) → envelope_bytes
decode(envelope_bytes) → recovered_cert
encode(recovered_cert) → envelope_bytes' (must equal envelope_bytes)
```

This is tested for each corpus entry. A round-trip divergence would indicate that the parser does not recover the certificate faithfully.

**Reproduction:**

```bash
cd ~/Desktop/EnterpriseGuard && \
python3 -c "
import json, subprocess
from pathlib import Path
ROOT = Path('.').resolve()
RUST = ROOT / 'rust/adie-primitives/target/release/adie-cbor-envelope'
corpus = json.loads((ROOT / 'tests/vomega/b-plus/corpus.json').read_text())
for v in corpus['positive']:
    cert = v['certificate']
    payload = json.dumps({'op': 'build', 'certificate_json': json.dumps(cert)})
    b1 = json.loads(subprocess.run([str(RUST)], input=payload, capture_output=True, text=True).stdout)['envelope_hex']
    p2 = json.dumps({'op': 'parse', 'envelope_hex': b1})
    recovered = json.loads(subprocess.run([str(RUST)], input=p2, capture_output=True, text=True).stdout)['certificate_json']
    p3 = json.dumps({'op': 'build', 'certificate_json': recovered})
    b2 = json.loads(subprocess.run([str(RUST)], input=p3, capture_output=True, text=True).stdout)['envelope_hex']
    print(f\"{v['id']}: round-trip byte-identical={b1==b2}\")
"
```

Expected: all `True`.

#### D2.7.3 Negative parity

The B+ negative matrix (`tests/vomega/b-plus/test_bplus_negative.py`) verifies that rejection behavior is consistent across the three implementations for a set of malformed or non-canonical inputs. The suite covers 15 cases:

| Case | Category |
|---|---|
| W01 | trailing bytes |
| W02 | truncated envelope |
| W03 | wrong type for `dcp_version` |
| W04 | unknown top-level label |
| W05 | empty map (all fields missing) |
| W06 | missing signatures |
| W07 | missing `subject` |
| W08 | `claim_root` wrong type |
| W09 | non-shortest integer label |
| W10 | tag in place of a value |
| W11 | float in place of a value |
| W12 | indefinite-length construct |
| W13 | duplicate top-level label |
| C01 | baseline parses (control) |
| C02 | envelope accepts short RS256 as wire-only |

All 15 cases are rejected (or accepted, for controls) identically across Rust, Python, and JavaScript. See `Evidence Collection v3` §5.2 for the exact failure counts.

### D2.8 Evidence Summary

#### D2.8.1 Test suites covering D2

| Language | Suite | Executions | File |
|---|---|---|---|
| Python | `tests/vomega/b-plus/test_bplus_e2e.py` | 10 | envelope round-trip; H09 TBS byte-identity |
| Python | `tests/vomega/b-plus/test_bplus_negative.py` | 15 | negative matrix |
| Python | `tests/vomega/b-plus/test_bplus_sizes.py` | (baseline reporting only; not counted in TOTALS) | size baseline |
| Python | `tests/vomega/hybrid/test_e2e.py` | 11 | hybrid signing & verification |
| Python | `tests/vomega/hybrid/test_tbs.py` | 12 | TBS construction |
| Python | `tests/vomega/hybrid/test_sign.py` | 16 | signing primitives |
| Python | `tests/vomega/hybrid/test_verify.py` | 20 | verification primitives |
| Python | `tests/vomega/hybrid/test_rust_parity.py` | 13 | Rust ↔ Python parity |
| Rust | `rust/adie-primitives/src/cbor/envelope.rs` (lib tests) | (included in the 111 `cbor::` executions; see D1.7.1) | envelope build/parse |
| Rust | `rust/adie-primitives/src/bin/adie-cbor-envelope.rs` | endpoint; verified via the differential |
| JavaScript | `js/wire/bin/adie-cbor-envelope.mjs` | endpoint; verified via the differential |

**Note on category separation.** The counts listed above are test **executions**, not unique vectors. The B+ corpus contains 5 unique certificates; each is exercised by multiple executions across multiple suites. See §E3.9 for the taxonomy.

#### D2.8.2 Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `rust/adie-primitives/src/cbor/envelope.rs` | `c2cb978dee16f6c0ae53b70dc81cf8710c9f1bb7f9392f38f9ff5aed9f93d049` |
| `rust/adie-primitives/src/bin/adie-cbor-envelope.rs` | `50919d5b77e100e1c7afa07041d5c3d30e52582ad81244f410fa9b848da65697` |
| `js/wire/bin/adie-cbor-envelope.mjs` | `5b4ba51fe790bda14a8057f0210370b0645f1aab5bb15fc464ba0126a3c907a2` |
| `protocol/wire/bin/adie-cbor-envelope.py` | (see Appendix B) |
| `protocol/hybrid/tbs.py` | `fe6e14d503c3f2e8d224ec058eb5744603778d5b7803fd8d6d6d612296c836e3` |
| `protocol/hybrid/verify.py` | `2d285fc50c43ae1c08bc7dd577657925cc08faf6deb9bbd1e3e8d5c6b48a7df5` |

#### D2.8.3 Reproduction — full D2 set

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ B+ E2E (10 executions) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_e2e.py && \
echo "═══ B+ negative (15 executions) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_negative.py && \
echo "═══ B+ size baseline ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_sizes.py && \
echo "═══ hybrid legacy (72 executions) ═══" && \
for f in test_e2e test_sign test_verify test_tbs test_rust_parity; do
  PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/$f.py
done
```

**Expected:** B+ E2E: 10/10; B+ negative: 15/15; size baseline reports 5,203-byte envelope; hybrid legacy: 72/72.

**Commit.** `7683adb` (branch `vOmega`).

### D2.9 What D2 Does Not Claim

- D2 does not claim that the B+ envelope is a COSE object. Amendment-1 §A2 explicitly establishes that it is not.
- D2 does not claim that the B+ envelope is the only way to carry an ADIE semantic certificate over a binary channel. It is the way vOmega adopts.
- D2 does not claim that the 5,203-byte size is optimal. It is the deterministic size of the envelope on the reference corpus.
- D2 does not claim that the envelope supports arbitrary nested CBOR structures. The nested ADIE objects are carried as canonical JCS byte strings, not as native CBOR maps. Any deviation from JCS is rejected at parse time.
- D2 does not claim that the current `proofs` array handles non-empty values. The current version permits only the empty array; non-empty `proofs` semantics are reserved for a future amendment (Amendment-2 §A4.1).
- D2 does not claim that a future COSE-native profile is implemented. Amendment-1 §A6 reserves the design; vOmega does not implement it.


---

## D3. Cross-Runtime Parity: Deep Proof

**Part II, Section D3.**
**Scope:** byte-level, semantic, and rejection parity across Rust, Python, and JavaScript implementations of DCP 2.1; WASM as validated delivery path.
**Upstream:** the frozen wire and envelope specifications (see §D3.1); the differential corpus at `tests/vomega/wire/differential_vectors.json`.

### D3.1 Specification Lineage

The parity claim is not defined by a standalone document; it is defined by the **same frozen artifacts** that define the wire format itself (D1) and the envelope (D2):

| Artifact | SHA-256 | Role |
|---|---|---|
| `spec/WIRE-FORMAT-0.2.md` | `b2fee085562dec275572d0ed64faa30bc0375ee9a74fe319b0af984895dcf07f` | wire model and rejection codes |
| `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md` | `7cb607be51b7a5d1afbb78611d66b0db3ef3c8cdc30de15ee41b3a701e4762ab` | ADIE-native envelope decision |
| `spec/WIRE-FORMAT-0.2-AMENDMENT-2.md` | `5e02bf89cfa347b7ff4b0b798ed0e7030866dc1f2989e060e8aca54768f844ac` | envelope content model |

**The parity claim is a claim about behavior.** It states that the three implementations — Rust, Python, JavaScript — agree on: the byte sequence produced by encoding, the semantic value produced by decoding, and the specific rejection code produced by rejecting. The specification defines the intended behavior; the differential corpus defines what is checked.

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && sha256sum \
  spec/WIRE-FORMAT-0.2.md \
  spec/WIRE-FORMAT-0.2-AMENDMENT-1.md \
  spec/WIRE-FORMAT-0.2-AMENDMENT-2.md
```

**Commit.** `7683adb` (branch `vOmega`).

### D3.2 The Three Implementations and Their Roles

vOmega maintains three implementations of the DCP 2.1 wire profile. Their roles are distinct and their relationship is deliberate.

| Implementation | Language | Location | Role |
|---|---|---|---|
| **Reference** | Rust | `rust/adie-primitives/src/cbor/` | The reference implementation against which parity is established. |
| **Interoperability adapter (Python)** | Python | `protocol/wire/` | Consumes and produces the same wire bytes; used in server-side and audit tooling. |
| **Independent adapter (JavaScript)** | JavaScript (Node.js) | `js/wire/` | Independently written. Verified against the Rust reference via differential testing. |

**A fourth artifact** — WASM, produced from the Rust source — is a **validated delivery path for the Rust reference implementation**. It is not treated as a fourth independent implementation. See §D3.9.

The three implementations were developed against the same specification, and each is tested against a **shared corpus** (see §D3.3). Byte-level and semantic parity are the observable properties this corpus checks.

### D3.3 The Shared Differential Corpus

The corpus is stored at `tests/vomega/wire/differential_vectors.json`. It contains **44 unique vectors**, distributed across three classes:

| Class | Count | Purpose |
|---|---|---|
| Encode vectors | 14 | Given a semantic value, produce canonical CBOR bytes. |
| Decode vectors | 12 | Given canonical CBOR bytes, produce the corresponding semantic value. |
| Negative vectors | 18 | Given malformed or non-canonical CBOR bytes, produce the corresponding rejection code. |
| **Total** | **44** | |

Each vector has a stable identifier (`E01`–`E14`, `D01`–`D12`, `N01`–`N18`) referenced by all differential suites.

**The corpus is deliberately small.** Its purpose is to cover **categories** of behavior — integer boundaries, string encodings, map ordering, malformed inputs of each rejection class — not to enumerate every possible input. Category coverage is more important than raw count for establishing parity of behavior; count is addressed in §D3.7.

**Reproduction (inspect corpus):**

```bash
cd ~/Desktop/EnterpriseGuard && python3 -c "
import json
d = json.load(open('tests/vomega/wire/differential_vectors.json'))
print('encode:', len(d['encode_vectors']))
print('decode:', len(d['decode_vectors']))
print('negative:', len(d['negative_vectors']))
"
```

Expected:

```
encode: 14
decode: 12
negative: 18
```

### D3.4 The Three Differential Pairs

Parity is established by three differential test pairs. Each pair drives the same corpus through two of the three implementations and compares the results.

| Pair | Test module | Corpus usage | Executions |
|---|---|---|---|
| **Python ↔ Rust** | `tests/vomega/wire/test_differential.py` | all 44 vectors | **44** |
| **Rust ↔ JavaScript** | `tests/vomega/wire-js/test_differential_rust.mjs` | 44 vectors + A01 architectural test | **45** |
| **Python ↔ JavaScript** | `tests/vomega/wire-js/test_differential_python.mjs` | 44 vectors + A01 architectural test | **45** |

**Total differential executions across all three pairs:** 44 + 45 + 45 = **134**.

**Note on the two "45" counts.** The Rust↔JS and Python↔JS pairs include one additional test each — labeled `A01` — which exercises the architectural boundary between rawcheck and semantic decoding (see §D1.6). It is not a vector from the corpus; it is a single-input test of a specific architectural property. The 44 vectors remain the same across all three pairs.

**Note on the stage-closure number "90".** An earlier stage (`3A.4A-DIFF`) closed at **90** executions, corresponding to the two pairs added at that stage (Rust↔JS + Python↔JS). That number is a **stage-closure count**, not the total differential execution count. The full cross-pair total for the current state of the corpus is 134. Both numbers are correct in their respective contexts; this document uses 134 for parity and reserves 90 for the historical stage record. See §E3.9.

**Reproduction (all three pairs):**

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ Python ↔ Rust (44) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/wire/test_differential.py && \
echo "═══ Rust ↔ JavaScript (45) ═══" && \
node tests/vomega/wire-js/test_differential_rust.mjs && \
echo "═══ Python ↔ JavaScript (45) ═══" && \
node tests/vomega/wire-js/test_differential_python.mjs
```

Expected: `TOTAL: 44 | PASS: 44 | FAIL: 0`, `TOTAL: 45 | PASS: 45 | FAIL: 0`, `TOTAL: 45 | PASS: 45 | FAIL: 0`.

**Commit.** `7683adb`.

### D3.5 Encode Parity

**Claim.** For every vector in the encode corpus, Python, Rust, and JavaScript produce byte-identical CBOR.

#### D3.5.1 What is compared

The comparison is **complete byte equality**, not a digest comparison. Each implementation produces a `Vec<u8>` (Rust), `bytes` (Python), or `Uint8Array` (JavaScript); the differential suite compares the full byte arrays element by element. A digest would conceal differences that occur at any position within the byte string, so it is not used.

#### D3.5.2 Coverage

The 14 encode vectors cover:

| Class of input | Vectors |
|---|---|
| Integers (0, 23, 24, 256, 65536, u64::MAX) | E01–E06 |
| Negative integers (-1, -25) | E07–E08 |
| Text strings (empty, "hello") | E09–E10 |
| Byte strings (empty) | E11 |
| Arrays (mixed simple values) | E12 |
| Maps (integer-keyed, sorted insertion, unsorted insertion) | E13–E14 |

Together these cover every CBOR major type that DCP 2.1 admits, at every integer boundary the profile permits.

#### D3.5.3 Parity result

| Pair | Passing | Total |
|---|---|---|
| Python ↔ Rust | 14 | 14 |
| Rust ↔ JavaScript | 14 | 14 |
| Python ↔ JavaScript | 14 | 14 |

The encode parity is 3-way: for every encode vector, all three implementations produce identical bytes.

### D3.6 Decode Parity

**Claim.** For every vector in the decode corpus, Python, Rust, and JavaScript produce semantically equal values.

#### D3.6.1 What is compared

The comparison is **semantic equality**, not textual equality. Each implementation produces a value in its native form:

- Rust: `AdieValue` enum.
- Python: `AdieValue` class hierarchy.
- JavaScript: tagged plain objects of the form `{t: "uint", v: <value>}`.

The differential suite normalizes each into a common canonical JSON representation and compares those.

#### D3.6.2 Why not byte comparison

Byte comparison on the decoded value is not meaningful — the three languages represent integers, strings, and maps differently in memory. What matters is that the **semantic content** is the same: an integer `256` decoded from a given CBOR byte string must be reported as `256` in all three, not as `256` in one and `256n` (BigInt) in another.

The normalization handles this: for a `uint` or `int` field, the value is compared as a decimal string; for a `bytes` field, as a hex string; for `text`, as a UTF-8 string; for `map`, as an ordered list of `[key, value]` pairs.

#### D3.6.3 Coverage

The 12 decode vectors cover:

| Class of input | Vectors |
|---|---|
| Simple values (null, true, false) | D01–D03 |
| Integers at canonical boundaries | D04–D08 |
| Negative integers | D09 |
| Strings (bytes and text) | D10–D11 |
| Containers (arrays, maps) | D12 |

Each vector is a canonical byte string that parses to a semantic value with a known structure.

#### D3.6.4 Parity result

| Pair | Passing | Total |
|---|---|---|
| Python ↔ Rust | 12 | 12 |
| Rust ↔ JavaScript | 12 | 12 |
| Python ↔ JavaScript | 12 | 12 |

The decode parity is 3-way.

### D3.7 Rejection Parity

**Claim.** For every vector in the negative corpus, Python, Rust, and JavaScript reject the input and produce the **same rejection code**.

#### D3.7.1 What is compared

The comparison is on the **specific typed rejection code** — one of the 14 `E_WIRE_*` codes defined in D1.5. A rejection with a different code is a parity failure even if both rejections occur.

The reason this matters: rejection codes are part of the wire contract. A consumer that sees `E_WIRE_NONCANONICAL_INT` can infer a specific class of malformation; a consumer that sees only "rejected" cannot. Parity at the code level is what makes cross-runtime rejection behavior meaningful for downstream tooling.

#### D3.7.2 Coverage

The 18 negative vectors cover, at minimum:

| Class of input | Vectors |
|---|---|
| Tag rejection | N07, N08, N09 |
| Float rejection (float16, float32, float64) | N05, N06 |
| Indefinite-length items | N03, N04 |
| Duplicate map keys | N10 |
| Trailing bytes | N01, N02 |
| Non-shortest integer encodings | N11, N12 |
| Non-canonical map order | N13 |
| Invalid key types (text key) | N14 |
| Invalid key types (bytes key) | N15 |
| Invalid UTF-8 | N16 |
| Undefined value | N17 |
| Truncated input | N18 |

Additional malformed-input coverage is provided by the D1.5 rejection matrix and by the B+ negative matrix (D2.7.3).

#### D3.7.3 Parity result

| Pair | Passing | Total |
|---|---|---|
| Python ↔ Rust | 18 | 18 |
| Rust ↔ JavaScript | 18 | 18 |
| Python ↔ JavaScript | 18 | 18 |

The rejection parity is 3-way.

#### D3.7.4 Classification priority

When multiple violations are present in a single input, DCP 2.1 defines a **priority order** for which rejection code applies. This is not a free choice; it is a specification requirement (see `WIRE-FORMAT-0.2.md` §9 and the architectural note in `DEFECT-036`).

The priority is enforced across all three implementations. An input that carries both a non-shortest integer and a duplicate key must be rejected with the code specified for that combination in all three implementations. A divergence would be a parity failure even if both implementations rejected the input with different codes.

The A01 architectural test in the JavaScript suites checks one specific case of this: a byte string that decodes to `Number 1` in JavaScript may have come from either a CBOR integer `0x01` or a CBOR float `0xfb3ff0000000000000`. The float must be rejected at the wire level before decoding; the integer must be accepted.

### D3.8 The Cross-Runtime Matrix

The three pairs above establish 3-way parity on the differential corpus. A separate diagnostic — `diff-matrix.mjs` — provides a **single-view summary** across a broader set of vector classes: **11 classes × 3 languages = 33 comparisons**.

#### D3.8.1 The 11 classes

| # | Class | Expected outcome |
|---|---|---|
| 1 | Valid encode | all OK |
| 2 | Valid decode | all OK |
| 3 | Float rejection | all `E_WIRE_FLOAT` |
| 4 | Tag rejection | all `E_WIRE_TAG` |
| 5 | Duplicate keys | all `E_WIRE_DUP_KEY` |
| 6 | Indefinite length | all `E_WIRE_INDEFINITE` |
| 7 | Trailing bytes | all `E_WIRE_TRAILING` |
| 8 | Non-shortest integer | all `E_WIRE_NONCANONICAL_INT` |
| 9 | Invalid UTF-8 | all `E_WIRE_INVALID_UTF8` |
| 10 | Invalid key type | all `E_WIRE_TYPE_MISMATCH` |
| 11 | Invalid value type | all `E_WIRE_MALFORMED` |

#### D3.8.2 The matrix output

For each class, the matrix prints the outcome as reported by Rust, Python, and JavaScript. All 33 cells match.

```
CLASS                        | RUST              | PYTHON            | JAVASCRIPT
------------------------------------------------------------------------------------
Valid encode                 | OK                | OK                | OK
Valid decode                 | OK                | OK                | OK
Float rejection              | E_WIRE_FLOAT      | E_WIRE_FLOAT      | E_WIRE_FLOAT
Tag rejection                | E_WIRE_TAG        | E_WIRE_TAG        | E_WIRE_TAG
Duplicate keys               | E_WIRE_DUP_KEY    | E_WIRE_DUP_KEY    | E_WIRE_DUP_KEY
Indefinite length            | E_WIRE_INDEFINITE | E_WIRE_INDEFINITE | E_WIRE_INDEFINITE
Trailing bytes               | E_WIRE_TRAILING   | E_WIRE_TRAILING   | E_WIRE_TRAILING
Non-shortest integer         | E_WIRE_NONCANONICAL_INT | E_WIRE_NONCANONICAL_INT | E_WIRE_NONCANONICAL_INT
Invalid UTF-8                | E_WIRE_INVALID_UTF8 | E_WIRE_INVALID_UTF8 | E_WIRE_INVALID_UTF8
Invalid key type             | E_WIRE_TYPE_MISMATCH | E_WIRE_TYPE_MISMATCH | E_WIRE_TYPE_MISMATCH
Invalid value type           | E_WIRE_MALFORMED  | E_WIRE_MALFORMED  | E_WIRE_MALFORMED
```

**Reproduction:**

```bash
cd ~/Desktop/EnterpriseGuard && node tests/vomega/wire-js/diff-matrix.mjs
```

Expected: the matrix above, with every row consistent across the three columns.

#### D3.8.3 Relationship to the differential corpus

The matrix is **not** a replacement for the differential suites. It reports outcomes at a coarse level (one input per class). The differential suites test the full 44-vector corpus and cover every boundary case the profile admits. The matrix is a **diagnostic summary** intended for quick inspection; the differential suites are the primary evidence.

### D3.9 WASM: A Validated Delivery Path

WASM is built from the Rust reference implementation. It is not an independent implementation; it shares the reference's source code and logic. It is used as a **delivery path**: a portable artifact that can run in environments where native Rust binaries cannot be deployed.

#### D3.9.1 Architecture

```
Rust Reference (rust/adie-primitives/)
        │
        ▼ wasm-bindgen
    WASM module (js/wasm-pkg-node/)
        │
        ├──► Node.js
        │
        └──► Browser (Firefox headless)
```

The WASM module exposes the same `encode` / `decode` interface as the native Rust reference, plus a JSON-based ABI. It does not introduce new semantics; it delivers the reference implementation's semantics to browser and Node.js consumers.

#### D3.9.2 Native Rust ↔ WASM byte parity

For each test vector, the WASM module produces byte-identical output to the native Rust reference. This is verified by `tests/vomega/wasm/test_wasm_node.mjs` (45 executions) and `tests/vomega/wasm/test_wasm_precision.mjs` (31 executions).

**Reproduction:**

```bash
cd ~/Desktop/EnterpriseGuard && \
node tests/vomega/wasm/test_wasm_node.mjs && \
node tests/vomega/wasm/test_wasm_precision.mjs
```

Expected: `TOTAL: 45 | PASS: 45 | FAIL: 0` and `TOTAL: 31 | PASS: 31 | FAIL: 0`.

#### D3.9.3 Browser path

The WASM module is exercised in a real browser (Firefox headless) via an HTML test page and a Node.js HTTP server that captures the browser's machine-readable result. The output is the string `PASS=29 FAIL=0`, parsed from the DOM — not from a screenshot.

| Component | Detail |
|---|---|
| HTML page | `tools/wasm/browser-test/index.html` |
| Server | `tools/wasm/browser-test/server.mjs` |
| Runner | Firefox headless, version 155.0.1 |
| Method | DOM output posted back to the server; parsed; asserted on |
| Assertions | 29 (10 u64 encode + 10 u64 decode + i64::MIN + 1 decode test + 6 rejections + 1 architectural) |

The browser path confirms that the WASM module executes correctly under a real JavaScript engine in a real browser, not only under Node.js.

#### D3.9.4 What WASM does not prove

- It does not prove that the WASM module is an independent implementation. It is built from the Rust source.
- It does not prove side-channel or timing properties. No such analysis was performed.
- It does not prove performance. No benchmarks were run.
- It does not prove that the WASM module replaces any of the three native implementations. It is a delivery path for one of them.

### D3.10 Evidence Summary

#### D3.10.1 Test suites covering D3

| Suite | Executions | Role |
|---|---|---|
| `tests/vomega/wire/test_differential.py` | 44 | Python ↔ Rust differential |
| `tests/vomega/wire-js/test_differential_rust.mjs` | 45 | Rust ↔ JavaScript differential |
| `tests/vomega/wire-js/test_differential_python.mjs` | 45 | Python ↔ JavaScript differential |
| `tests/vomega/wire-js/diff-matrix.mjs` | (matrix report; 33 comparisons) | cross-runtime summary |
| `tests/vomega/wasm/test_wasm_node.mjs` | 45 | WASM Node.js differential |
| `tests/vomega/wasm/test_wasm_precision.mjs` | 31 | WASM precision boundary |
| Browser (Firefox headless) | 29 | WASM browser path |

**Differential executions across the three pairs:** 44 + 45 + 45 = **134**.

**Additional WASM executions (Node + precision):** 45 + 31 = **76**.

**Browser executions:** **29**.

**Note on category separation.** The three differential pairs share the same 44-vector corpus. The WASM suites exercise a different corpus (the wasm-specific vectors) whose size is 45 vectors (Node) and 31 vectors (precision). None of these numbers are additive into a "cross-runtime tests" total; they are executions in distinct test contexts. See §E3.9.

#### D3.10.2 Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `protocol/wire/rawcheck.py` | (see Appendix B) |
| `js/wire/rawcheck.mjs` | `c46d22bed334a53ce66d5652e300c6c93fe2a5e44f8e5c0461ae671036c35e52` |
| `rust/adie-primitives/src/cbor/rawcheck.rs` | `bbc9c65917ba8f4aa1758b1e8e5286e1bfc250da4d2b69dd9c0fa6659365d6f0` |
| `protocol/wire/value.py` | (see Appendix B) |
| `js/wire/value.mjs` | (see Appendix B) |
| `rust/adie-primitives/src/cbor/value.rs` | (see Appendix B) |
| `rust/adie-wasm/src/lib.rs` | (see Appendix B) |

The full per-language hashes are enumerated in Appendix B.

#### D3.10.3 Reproduction — full D3 set

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ Python ↔ Rust (44) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/wire/test_differential.py && \
echo "═══ Rust ↔ JavaScript (45) ═══" && \
node tests/vomega/wire-js/test_differential_rust.mjs && \
echo "═══ Python ↔ JavaScript (45) ═══" && \
node tests/vomega/wire-js/test_differential_python.mjs && \
echo "═══ WASM Node.js (45) ═══" && \
node tests/vomega/wasm/test_wasm_node.mjs && \
echo "═══ WASM precision (31) ═══" && \
node tests/vomega/wasm/test_wasm_precision.mjs && \
echo "═══ Cross-runtime matrix ═══" && \
node tests/vomega/wire-js/diff-matrix.mjs
```

**Expected:** the differential pairs at 44/45/45, WASM at 45/31, and the matrix showing all rows consistent.

**Commit.** `7683adb` (branch `vOmega`).

### D3.11 What D3 Does Not Claim

- D3 does not claim that Rust, Python, and JavaScript are equivalent as **implementations**. They share behavior over a tested corpus; their internal code, structure, and error paths differ.
- D3 does not claim that the parity extends to inputs **outside the 44-vector corpus**. Extending the corpus would require corresponding extensions to the differential suites; absent such extensions, behavior on non-corpus inputs is not characterized.
- D3 does not claim that rejection behavior is characterized for all possible malformed inputs. The negative corpus enumerates 18 categories; additional malformed-input classes may exist outside those categories.
- D3 does not claim that the differential corpus is statistically representative of any real-world input distribution. Its coverage is structured by category, not by frequency.
- D3 does not claim that WASM is a fourth independent implementation. It is a delivery path for the Rust reference; see §D3.9.
- D3 does not claim that the browser path exercises the same vectors as the Node path. The browser page uses a fixed set of 29 assertions; it is not a re-run of the full corpus in the browser.


---

## D4. Governance Control Plane (3B)

**Part II, Section D4.**
**Scope:** the canonical governance model introduced in Phase 3B — dual decision axes, canonical `DecisionContract`, lifecycle state machine, authority model, legacy compatibility adapter, and one-directional wire bridge.

### D4.1 Scope and Lineage

Phase 3B did not modify the wire format or the envelope. It introduced a **new governance layer** at the semantic level, above the wire. The layer defines:

- A canonical decision artifact with two independent axes.
- A lifecycle state machine with single ownership of legal transitions.
- An authority model explicitly distinct from evidence.
- A one-directional compatibility adapter for a legacy decision contract.
- A one-directional wire bridge from the governance layer to the frozen wire layer.

The upstream specifications remain unchanged: `WIRE-FORMAT-0.2.md`, Amendment-1, and Amendment-2 all have the same SHA-256 values as in §D1.1 and §D2.1. The governance layer consumes the wire layer; it does not modify it.

**Phase-close commit.** `134e6be` (branch `vOmega`) — 3B was closed at this commit.

**Evidence-reference commit.** `7683adb` (branch `vOmega`) — this is the state on which all reproduction instructions in this document operate. The governance layer is unchanged between `134e6be` and `7683adb`.

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && git log --oneline -1 134e6be
# 134e6be vOmega 3B: Canonical governance — A-lineage DecisionContract + axis decomposition ...
```

### D4.2 Architectural Decision — Canonical A-lineage `DecisionContract`

At the start of Phase 3B, the repository contained **two parallel `DecisionContract` implementations**:

| Lineage | Module | Version | Role at time of discovery |
|---|---|---|---|
| **A** | `src/enterpriseguard/adie/decision.py` | 3.0.1 | Produced by the canonical ADIE decision engine; declared as canonical by `execution_manifest.py`, but with limited runtime consumers. |
| **B** | `src/enterpriseguard/decision/contracts.py` | 2.0.0 | Exercised by SDK, API, and Response layers; used by 24 legacy tests. |

Both classes share the name `DecisionContract` but differ in fields, lifecycle vocabulary, and status model. This was documented as DEFECT-036 (cross-runtime vocabulary drift), and a canonicalization decision was required before further work.

The Commander's decision (recorded in `docs/vomega/CONTINUITY.md` §56) was:

- **A is canonical.** The A-lineage `DecisionContract` remains the single authoritative decision artifact.
- **B is retained as a legacy compatibility adapter.** It is not deleted, but it cannot itself authorize decisions.
- **No third `DecisionContract`** is introduced.

This decision is what makes §D4.3 through §D4.7 meaningful. The 3B layer is the implementation of that decision.

### D4.3 The Two Independent Axes

Phase 3B decomposes decision state along **two axes that are not inferable from one another**:

#### D4.3.1 Axis L — DecisionLifecycle

The artifact-progression axis. Eight states, in a linear order:

```
PROPOSED
  → VALIDATED
  → AUTHORIZED
  → EMITTED
  → EXECUTED_EXTERNAL
  → OBSERVED
  → ASSESSED
  → CLOSED
```

Each state describes where the artifact is in the pipeline. The lifecycle does **not** express permission.

#### D4.3.2 Axis A — AuthorizationStatus

The authorization axis. Five states:

```
PENDING | AUTHORIZED | DENIED | EXPIRED | SUPERSEDED
```

Each state describes whether the decision currently has authority for the governed mode. It does **not** express progression.

#### D4.3.3 Why the split matters

Before 3B, a single status enum mixed progression and permission. That conflation creates ambiguity: a decision marked `APPROVED` could be interpreted as either "the artifact has passed review" or "the decision is authorized to proceed." Those are different questions.

After 3B, the two questions are answered separately:

- The lifecycle says *where the artifact is*.
- The authorization status says *whether it may proceed*.

Neither axis can be derived from the other. This is enforced by construction: the two axes are distinct Python enum classes, and the canonical `DecisionContract` records both without inferring one from the other.

#### D4.3.4 String overlap is intentional

`EXPIRED` and `SUPERSEDED` appear as string values in **both** `AuthorizationStatus` and `TrustStatus` (D5). They do not appear in `DecisionLifecycle`. The two occurrences are semantically distinct: an authorization can expire because the artifact's authorization window has ended, whereas a trust binding can expire because the authority's validity window has ended. The overlapping strings are intentional; the enums are separate types.

### D4.4 Canonical `DecisionContract` Structure

The canonical `DecisionContract` (A-lineage) is a frozen dataclass. Its fields fall into three groups:

#### D4.4.1 Core decision fields

| Field | Type | Purpose |
|---|---|---|
| `decision_id` | text | Stable identifier for the decision. |
| `intent` | `DecisionIntent` | The defensive intent (`ALLOW`, `MONITOR`, `ALERT`, `CONTAIN`, `ISOLATE`, `DEFER`). |
| `lifecycle` | `DecisionLifecycle` | Position on Axis L. |
| `decision_score` | float in [0, 1] | Output of the decision engine. |
| `confidence` | float in [0, 1] | Confidence of the underlying evaluation. |
| `prediction_id` | text | Reference to the prediction that contributed to the decision. |
| `policy_id` | text | Reference to the policy that governed the decision. |
| `rationale` | text | Free-text rationale. |
| `reason_codes` | tuple of text | Structured reason codes. |
| `created_at` | timestamp | Creation time, timezone-aware. |

#### D4.4.2 Governance provenance fields (added in 3B)

| Field | Type | Default | Purpose |
|---|---|---|---|
| `evidence_set_id` | text or null | null | Reference to the evidence set. |
| `state_id` | text or null | null | Reference to the state. |
| `authority_id` | text or null | null | Reference to the authorizing `Authority`. |
| `checkpoint_id` | text or null | null | Reference to the checkpoint. |
| `execution_manifest_id` | text or null | null | Reference to the emitted `ExecutionManifest`. |
| `outcome_id` | text or null | null | Reference to the observed outcome. |
| `authorization_status` | `AuthorizationStatus` | `PENDING` | Position on Axis A. |

These fields are **optional**. Their presence is not required for a `DecisionContract` to be valid; when present, they are validated for type and consistency.

#### D4.4.3 Trust-at-authorization fields (added in 3C)

| Field | Type | Default | Purpose |
|---|---|---|---|
| `authority_status_at_authorization` | `TrustStatus` or null | null | The trust status of the authorizing authority at the moment the decision was authorized. |
| `authority_status_at_authorization_time` | timestamp or null | null | The timestamp of that evaluation. |

These fields are also optional. When set, they are never overwritten. They record a **historical** fact, distinct from any subsequent trust evaluation.

#### D4.4.4 Validation invariants

The `DecisionContract.__post_init__` enforces:

- `decision_score` and `confidence` are in [0, 1], finite, non-boolean.
- `created_at` is timezone-aware.
- `executes_security_actions` is `False` (any attempt to set it to `True` raises `DecisionContractError`).
- `authorization_status` is an instance of `AuthorizationStatus`.
- **Axis-separation invariant:** if `authorization_status is AUTHORIZED`, then `lifecycle` must be one of `AUTHORIZED`, `EMITTED`, `EXECUTED_EXTERNAL`, `OBSERVED`, `ASSESSED`, `CLOSED`. Attempting to set `authorization_status=AUTHORIZED` with `lifecycle=PROPOSED` or `lifecycle=VALIDATED` raises `DecisionContractError`.

The last invariant is what makes the two-axis model coherent: a contract cannot claim authorization before it has reached the AUTHORIZED lifecycle state.

### D4.5 Lifecycle State Machine

The lifecycle state machine is implemented in `src/enterpriseguard/adie/canonical/lifecycle_sm.py`. It is a **single-ownership** implementation: legal transitions are defined in one place, and every transition attempt is routed through the same function.

#### D4.5.1 The 13 legal transitions

The state machine defines exactly 13 legal ordered pairs:

| # | Source | Destination |
|---|---|---|
| 1 | `PROPOSED` | `VALIDATED` |
| 2 | `PROPOSED` | `CLOSED` |
| 3 | `VALIDATED` | `AUTHORIZED` |
| 4 | `VALIDATED` | `CLOSED` |
| 5 | `AUTHORIZED` | `EMITTED` |
| 6 | `AUTHORIZED` | `CLOSED` |
| 7 | `EMITTED` | `EXECUTED_EXTERNAL` |
| 8 | `EMITTED` | `CLOSED` |
| 9 | `EXECUTED_EXTERNAL` | `OBSERVED` |
| 10 | `EXECUTED_EXTERNAL` | `CLOSED` |
| 11 | `OBSERVED` | `ASSESSED` |
| 12 | `OBSERVED` | `CLOSED` |
| 13 | `ASSESSED` | `CLOSED` |

Two properties are visible in this table:

- **Forward progression:** the main chain `PROPOSED → VALIDATED → AUTHORIZED → EMITTED → EXECUTED_EXTERNAL → OBSERVED → ASSESSED → CLOSED` appears in order.
- **Early abort:** every non-terminal state can transition to `CLOSED`. This is not a defect; it is a deliberate decision that a decision may be closed at any point in its pipeline.

`CLOSED` is terminal: it has no outgoing transitions.

#### D4.5.2 The 51 illegal transitions

Of the 64 possible ordered pairs (8 × 8), 13 are legal and 51 are illegal. The 51 illegal pairs are **the complement of the 13 legal ones**, not 51 independent rules. Examples of illegal pairs:

- `PROPOSED → AUTHORIZED` (skips `VALIDATED`)
- `PROPOSED → EMITTED` (skips two stages)
- `PROPOSED → EXECUTED_EXTERNAL`
- `VALIDATED → EMITTED`
- `EMITTED → AUTHORIZED` (backward)
- `AUTHORIZED → VALIDATED` (backward)
- `CLOSED → *` (from terminal state)

#### D4.5.3 `EXECUTED_EXTERNAL` requires an external-observation flag

Transitioning to `EXECUTED_EXTERNAL` is not a normal transition. It represents the observation of an event that occurred outside the ADIE boundary. The state machine enforces this with a required flag:

```python
transition(L.EMITTED, L.EXECUTED_EXTERNAL, external_observation=True)
```

An attempt to make this transition without `external_observation=True` raises `LifecycleTransitionError`. This is the code-level encoding of the invariant that ADIE does not perform external execution.

#### D4.5.4 Transition records

Each successful transition returns a `LifecycleTransition` record:

```python
@dataclass(frozen=True)
class LifecycleTransition:
    src: DecisionLifecycle
    dst: DecisionLifecycle
    external: bool  # True if this is an external-boundary observation
```

The `external` flag is `True` only when the destination is `EXECUTED_EXTERNAL`.

### D4.6 Authority Model

The authority model is implemented in `src/enterpriseguard/adie/canonical/authority.py`. Its purpose is to make the authority that authorizes a decision **explicit and separate from evidence**.

#### D4.6.1 The `Authority` dataclass

| Field | Type | Purpose |
|---|---|---|
| `authority_id` | text | Stable identifier. |
| `authority_kind` | `AuthorityKind` | `MACHINE`, `HUMAN`, or `DUAL`. |
| `policy_id` | text | The policy that grants authority. |
| `policy_version` | text | The policy version. |
| `scope` | text | The operation the authority permits. |
| `valid_from` | timestamp | Start of validity. |
| `valid_until` | timestamp | End of validity. |
| `provenance` | mapping | Free-form provenance metadata. |

#### D4.6.2 Validation

The `__post_init__` enforces:

- `authority_id`, `policy_id`, `policy_version`, `scope` are non-empty strings.
- `authority_kind` is an instance of `AuthorityKind`.
- `valid_from` and `valid_until` are timezone-aware timestamps.
- `valid_until > valid_from`.
- `provenance` is a `MappingProxyType` (deep-frozen).

#### D4.6.3 Methods

| Method | Returns | Purpose |
|---|---|---|
| `is_active(at=None)` | bool | `valid_from <= at < valid_until`. |
| `requires_scope(requested)` | raises `AuthorityScopeMismatchError` if mismatched | Enforces the scope field. |
| `fingerprint()` | 71-char hex string | SHA-256 over a canonical JSON serialization of the authority's identity fields (excluding provenance). |

#### D4.6.4 The `Evidence ≠ Authority` invariant

The authority model is deliberately **not** derivable from evidence. There is no constructor of `Authority` that takes a `DecisionEvidence` object and produces an authority. An authority must be constructed by a caller that supplies the authority's identity, kind, policy reference, scope, and validity window.

This is the code-level encoding of the invariant:

> Evidence is what the system observed. Authority is who is allowed to act. The two are not the same, and neither can be inferred from the other.

### D4.7 Legacy B Compatibility Adapter

The B-lineage `DecisionContract` (in `src/enterpriseguard/decision/contracts.py`) is retained as a compatibility surface. It is used by SDK, API, and Response layers that have not yet migrated to the canonical A-lineage.

Phase 3B introduces a **one-directional adapter** at `src/enterpriseguard/adie/canonical/compat_decision_b.py`. The adapter has two functions:

#### D4.7.1 `legacy_status_to_authorization(legacy_status_value)`

Maps a B-lineage `DecisionStatus` string to the canonical `AuthorizationStatus`:

| Legacy B value | Canonical A value |
|---|---|
| `pending` | `PENDING` |
| `authorized` | `AUTHORIZED` |
| `denied` | `DENIED` |
| `expired` | `EXPIRED` |
| `superseded` | `SUPERSEDED` |

Unknown legacy values raise `LegacyAdapterError`.

#### D4.7.2 `legacy_contract_to_neutral(legacy)`

Extracts a neutral dictionary from a legacy `DecisionContract`. The dictionary contains:

- `legacy_decision_id`
- `evaluation_id`
- `policy_id`
- `authorization_status` (the mapped value from the previous function)
- `legacy_authorized_claim` (the legacy `authorized` boolean, preserved as-is)
- `target_resource_id`
- `expires_at`

#### D4.7.3 The critical omission

The adapter **deliberately does not promote** the legacy `authorized` boolean to an `Authority` object. The legacy boolean is preserved as `legacy_authorized_claim`, which is a factual field of the legacy contract, but it is not translated into a canonical `Authority`.

The reason: in the canonical model, authorization requires an explicit `Authority` with a scope and a validity window. A boolean claim in a legacy contract does not carry that information. The adapter does not fabricate it.

Consequence: a caller that consumes a neutral dict and needs canonical authorization must supply an explicit `Authority` separately. The adapter cannot grant authorization on its own.

### D4.8 Wire Bridge (adie → protocol)

The wire bridge is implemented at `src/enterpriseguard/adie/canonical/wire_bridge.py`. Its role is to allow the governance layer to consume and produce wire-format artifacts produced by the `protocol/` layer.

#### D4.8.1 Dependency direction

The dependency direction is fixed:

```
protocol/           ← wire / crypto / proof (frozen)
    ▲
    │  consumed by
    │
enterpriseguard/adie/canonical/    ← governance
    ▲
    │  consumed by
    │
enterpriseguard/adie/decision.py   ← canonical DecisionContract
```

The reverse direction is prohibited. `protocol/` does not import from `enterpriseguard/adie/`. This is verified by a test in the wire-bridge suite (`test_wire_bridge.py`, test W02).

#### D4.8.2 Bridge API

Two functions are exposed:

| Function | Purpose |
|---|---|
| `envelope_from_certificate(cert)` | Given an ADIE semantic certificate, produce the corresponding B+ envelope bytes. |
| `parse_envelope_to_certificate(envelope_bytes)` | Given a B+ envelope, produce the ADIE semantic certificate. |

Both functions delegate to the wire-layer endpoint at `protocol/wire/bin/adie-cbor-envelope.py` via a subprocess call. The subprocess boundary is deliberate: it keeps the two layers decoupled, so that the governance layer does not acquire a direct import dependency on the wire layer's internal structure.

#### D4.8.3 What the bridge does not do

- It does not modify the wire format.
- It does not interpret the certificate semantics.
- It does not perform cryptographic verification (that is done separately — see §D6).
- It does not create a second certificate parser.

The bridge is a transport adapter, not a second authority.

### D4.9 Anti-Bypass Invariants

Phase 3B introduced a suite of anti-bypass tests (`tests/vomega/governance/test_governance_anti_bypass.py`) that verify a set of invariants at the code level. The invariants are:

| # | Invariant | Test |
|---|---|---|
| X01 | Evidence does not carry an `authority_id` attribute. | `DecisionEvidence` has no `authority_id`. |
| X02 | Evidence does not carry an `authorization_status` attribute. | `DecisionEvidence` has no `authorization_status`. |
| X03 | Evidence does not carry an `authorized` attribute. | `DecisionEvidence` has no `authorized`. |
| X04 | Policy-denied decision remains in `PROPOSED`. | `policy_allowed=False` → `lifecycle is PROPOSED`. |
| X05 | Policy-denied decision is not `AUTHORIZED`. | `policy_allowed=False` → `authorization_status != AUTHORIZED`. |
| X06–X08 | Illegal lifecycle transitions raise. | `PROPOSED → AUTHORIZED` raises; `PROPOSED → EMITTED` raises; `VALIDATED → EXECUTED_EXTERNAL` raises. |
| X09 | Authority scope mismatch raises. | `requires_scope("execute")` on an authority with scope `decide` raises `AuthorityScopeMismatchError`. |
| X10 | Early-`AUTHORIZED` claim raises. | `DecisionContract(authorization_status=AUTHORIZED, lifecycle=PROPOSED)` raises `DecisionContractError`. |
| X11 | Legacy adapter emits no `Authority`. | The neutral dict has no `authority` or `authority_id` key. |
| X12 | Legacy claim preserved as factual field. | The neutral dict has `legacy_authorized_claim`. |
| X13 | `EXECUTES_SECURITY_ACTIONS` is `False`. | Module-level constant. |
| X14 | `EXECUTED_EXTERNAL` requires `external_observation=True`. | Transition without the flag raises `LifecycleTransitionError`. |
| X15 | Backward lifecycle jumps raise. | `AUTHORIZED → VALIDATED` raises. |
| X16 | `AUTHORIZED` values differ across axes. | `AuthorizationStatus.AUTHORIZED.value != DecisionLifecycle.EXECUTED_EXTERNAL.value`. |
| X17 | Lifecycle has no `denied` value. | Set of lifecycle values does not contain `"denied"`. |
| X18 | Authorization has no `emitted` value. | Set of authorization values does not contain `"emitted"`. |
| X19 | `executes_security_actions` remains `False`. | Any constructed contract reports `False`. |

Each invariant is tested behaviorally. The suite has 19 executions; all pass.

### D4.10 Evidence Summary

#### D4.10.1 Test suites covering D4

| Suite | Executions | Role |
|---|---|---|
| `tests/vomega/governance/test_canonical_lifecycle.py` | 24 | axis-separation invariants |
| `tests/vomega/governance/test_lifecycle_sm.py` | 31 | state machine: 13 legal / 51 illegal / boundaries |
| `tests/vomega/governance/test_canonical_authority.py` | 20 | authority validation and fingerprint |
| `tests/vomega/governance/test_compat_b_adapter.py` | 16 | legacy adapter behavior |
| `tests/vomega/governance/test_canonical_contract.py` | 19 | `DecisionContract` field and invariant validation |
| `tests/vomega/governance/test_governance_anti_bypass.py` | 19 | anti-bypass invariants |
| `tests/vomega/governance/test_wire_bridge.py` | 7 | one-directional bridge and dependency direction |
| **Governance subtotal** | **136** | |

**Note on category separation.** The 136 executions are executions, not unique vectors. See §E3.9 for the taxonomy.

#### D4.10.2 Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `src/enterpriseguard/adie/canonical/lifecycle.py` | `cf8e1a2ba7b5c7797543859006ad0c75023758c2957ea812ad08689c70aa39b3` |
| `src/enterpriseguard/adie/canonical/lifecycle_sm.py` | `cecfad8df33b1a354437975f21648823e2dfbb686e1c526016d47c75676438a6` |
| `src/enterpriseguard/adie/canonical/authority.py` | `01e60e37b6bc582ce1c41ab65ad994ba858e984ea02e623cd1bd25b74600c52a` |
| `src/enterpriseguard/adie/canonical/compat_decision_b.py` | (see Appendix B) |
| `src/enterpriseguard/adie/canonical/wire_bridge.py` | (see Appendix B) |
| `src/enterpriseguard/adie/decision.py` | `532fef99c023a6275bdec0ee4cf2a174df7b724dc499fe23f5ae63c5834fcfee` |

#### D4.10.3 Reproduction — full D4 set

```bash
cd ~/Desktop/EnterpriseGuard && \
for f in test_canonical_lifecycle test_lifecycle_sm test_canonical_authority \
         test_compat_b_adapter test_canonical_contract test_governance_anti_bypass \
         test_wire_bridge; do
  PYTHONPATH=src .venv/bin/python tests/vomega/governance/$f.py
done
```

**Expected:** 24 + 31 + 20 + 16 + 19 + 19 + 7 = 136 executions, 0 failures.

**Commit.** `7683adb` (branch `vOmega`). The governance layer itself was introduced at commit `134e6be` and is unchanged between that commit and `7683adb`.

### D4.11 What D4 Does Not Claim

- D4 does not claim that the A-lineage `DecisionContract` is equivalent to the B-lineage contract. They differ in fields, status vocabulary, and lifecycle model. The canonical model is A; B is retained for compatibility.
- D4 does not claim that the lifecycle state machine covers all decision scenarios. It covers the states and transitions the vOmega profile requires; extensions may require a new version.
- D4 does not claim that the `Authority` model is a substitute for a trust root. Authority establishment is an external step; the model operates on authorities that are provided as inputs. See §D5 and §D11.
- D4 does not claim that the wire bridge is a second envelope implementation. It is a subprocess adapter that invokes the wire layer's endpoint. The wire layer remains authoritative for the envelope.
- D4 does not claim that the anti-bypass suite covers all possible bypass attempts. It covers 19 classes of bypass that were identified during the design of 3B; additional classes may exist outside that set.
- D4 does not claim that the `Authority` fingerprint identifies the authority globally. It is a SHA-256 over a canonical serialization of the authority's identity fields within a given deployment.

---

## D5. Trust Status & Revocation (3C)

**Part II, Section D5.**
**Scope:** the trust-status axis introduced in Phase 3C — the `TrustStatus` enum, `RevocationAuthority`, `TrustStatusAssertion`, the append-only `TrustStatusStore`, the deterministic resolver, the governed initial state, and the historical-vs-current distinction.

### D5.1 Scope and Lineage

Phase 3C introduced a **third independent semantic axis** at the governance layer. Like the two axes of D4, this axis answers a distinct question:

- **`DecisionLifecycle` (D4)** answers: *where is the artifact in its pipeline?*
- **`AuthorizationStatus` (D4)** answers: *is the decision currently authorized?*
- **`TrustStatus` (D5)** answers: *is the relevant authority trusted at the time of evaluation?*

The three axes are modeled as three distinct Python enum classes. None is derivable from the others.

**Phase-close commit.** `9f9bd9b` (branch `vOmega`) — 3C was closed at this commit, with **175 trust executions across 8 suites**.

**Evidence-reference commit.** `7683adb` (branch `vOmega`) — this is the state on which all reproduction instructions in this document operate. At this commit the trust layer reports **193 executions across 9 suites**.

**Documentation convention (per Commander's note on D4).** The 3C phase was **closed** at `9f9bd9b` with **175 trust executions across 8 suites**. The `test_governed_initial_state.py` suite (18 executions) was added later, during Phase **3D** (close commit `7c0c36a`), as test coverage for DEFECT-043. The evidence-reference commit for this dossier is `7683adb`, at which the trust layer reports **193 executions across 9 suites**. Both figures are correct in their respective contexts: 175 is the historical 3C close; 193 is the current evidence state.

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && git log --oneline -1 9f9bd9b
# 9f9bd9b vOmega 3C: Trust Status & Revocation — TrustStatus axis + RevocationAuthority + ...
```

### D5.2 The TrustStatus Axis

The trust axis is defined at `src/enterpriseguard/adie/canonical/trust/status.py`. It has five states.

#### D5.2.1 The five values

| Value | Meaning | Terminal? | Reversible? |
|---|---|---|---|
| `ACTIVE` | The trust subject is currently trustworthy within its scope. | No | Yes |
| `SUSPENDED` | The subject is temporarily withheld; a future assertion may return it to `ACTIVE`. | No | Yes |
| `REVOKED` | The subject has been permanently terminated by an explicit authority. | Yes | No |
| `EXPIRED` | The subject's temporal window has ended. | Yes | No |
| `SUPERSEDED` | The subject has been replaced by a newer binding. | Yes | No |

The module exports two frozen sets for use by callers:

- `TERMINAL = {REVOKED, EXPIRED, SUPERSEDED}`
- `REVERSIBLE = {ACTIVE, SUSPENDED}`

The two sets are disjoint and their union is the full `TrustStatus` enum.

#### D5.2.2 Cross-axis string overlap

Two strings — `"expired"` and `"superseded"` — appear as values in both `TrustStatus` and `AuthorizationStatus` (D4.3.2). The strings are identical, but the enums are separate classes, and the semantic meaning is distinct:

- `AuthorizationStatus.EXPIRED` refers to the ending of the decision's authorization window.
- `TrustStatus.EXPIRED` refers to the ending of the trust binding's validity window.

No code path treats the two as interchangeable; the canonical `DecisionContract` validation enforces axis separation at construction time (see §D4.4.4).

### D5.3 Trust Status Assertions

The trust model operates on **assertions** — immutable records of a status change. The `TrustStatusAssertion` is defined at `src/enterpriseguard/adie/canonical/trust/assertion.py`.

#### D5.3.1 The three timestamps

Every assertion carries three timestamps. Each serves a distinct purpose.

| Field | Type | Meaning |
|---|---|---|
| `asserted_at` | aware timestamp | When the actor decided to make the assertion. |
| `effective_at` | aware timestamp | When the assertion takes effect. May be in the past or future relative to `asserted_at`. |
| `observed_at` | aware timestamp | When the assertion entered the store. Usually equal to or later than `asserted_at`, but not required to be. |

**Why three?** A single `created_at` would conflate the actor's decision time with the time the change takes effect. In practice these can differ:

- A revocation may be decided today (`asserted_at = now`) but scheduled to take effect in the past (`effective_at = some_past_time`) — for example, if the revocation is backdated following an audit finding.
- A revocation may be decided today and scheduled for the future — for example, a planned suspension of an authority at the end of a fiscal period.
- The `observed_at` field allows a reader to distinguish the actor's asserted time from the time the assertion became visible in the store, which may differ if an assertion is delayed in transit.

The resolver uses `effective_at` for time-based evaluation. The other two are preserved for audit and provenance.

#### D5.3.2 The assertion kind

Every assertion carries a `RevocationKind`:

| Kind | Resulting `TrustStatus` | Notes |
|---|---|---|
| `SUSPEND` | `SUSPENDED` | Reversible. |
| `REVOKE` | `REVOKED` | Terminal. |
| `SUPERSEDE` | `SUPERSEDED` | Terminal. |
| `EXPIRE` | `EXPIRED` | Terminal. |

The mapping is fixed in the module. A caller cannot assert an arbitrary `TrustStatus` directly; the status is derived from the kind.

#### D5.3.3 Additional fields

| Field | Purpose |
|---|---|
| `assertion_id` | Stable identifier for the assertion. |
| `subject_id` | The trust subject the assertion applies to (e.g., an authority ID). |
| `authority_ref` | A reference to the governing actor (e.g., `gov-root`). |
| `authority_id` | The specific revocation authority that made the assertion. |
| `policy_id` | Optional policy reference. |
| `reason` | Free-text reason. |
| `provenance` | Optional free-form metadata. |

#### D5.3.4 Assertion validation

The assertion's `__post_init__` enforces:

- Non-empty string fields for `assertion_id`, `subject_id`, `authority_ref`, `authority_id`.
- `kind` is a `RevocationKind`.
- All three timestamps are timezone-aware.
- `provenance` is deep-frozen.

#### D5.3.5 Fingerprint

Each assertion has a `fingerprint()` method that returns a `sha256:<64-hex>` digest over a canonical JSON serialization of the assertion's identity fields (excluding `provenance`). The fingerprint is deterministic for the same assertion fields.

### D5.4 Revocation Authority

The trust model separates **who may assert a status change** from **what the status change is**. The authority is modeled by `RevocationAuthority` at `src/enterpriseguard/adie/canonical/trust/authority_to_revoke.py`.

#### D5.4.1 Rationale

A party that can authorize a decision is not automatically entitled to revoke every trust subject. Revocation is a privileged operation with its own scope and its own list of subjects on which it may operate. The `RevocationAuthority` object encodes this separation.

#### D5.4.2 Fields

| Field | Type | Purpose |
|---|---|---|
| `revocation_authority_id` | text | The authority's own identifier. |
| `revocation_authority_ref` | text | A reference to the governing actor (e.g., an `authority_id` from D4). |
| `permitted_kinds` | frozenset of `RevocationKind` | Which kinds of assertions this authority may make. |
| `revocable_subject_ids` | frozenset of text | An explicit allow-list of subjects the authority may operate on. |
| `valid_from` | aware timestamp | Start of the authority's validity window. |
| `valid_until` | aware timestamp | End of the authority's validity window. |

#### D5.4.3 `permits` method

The `permits(subject_id, kind, at=None)` method raises `RevocationNotPermittedError` if any of the following hold:

- The authority is not active at the given `at` time (defaults to current time).
- The requested `kind` is not in `permitted_kinds`.
- The requested `subject_id` is not in `revocable_subject_ids`.

The method returns `None` on success. It does not silently return a boolean; failure is always an exception.

#### D5.4.4 Relationship to `Authority` (D4)

`RevocationAuthority` and `Authority` are distinct classes. An `Authority` with `scope="decide"` cannot revoke anything by virtue of that scope. A caller that wishes to revoke must supply an explicit `RevocationAuthority` with the appropriate `permitted_kinds` and `revocable_subject_ids`.

This separation is tested by X01–X20 in §D5.9.

### D5.5 The Append-Only Trust Status Store

The trust model's history is stored in `TrustStatusStore` at `src/enterpriseguard/adie/canonical/trust/history.py`.

#### D5.5.1 Design

The store is **append-only**. Assertions may be added but never modified or removed. The current trust status of a subject is **not stored**; it is derived on demand from the store's assertion history by the resolver.

#### D5.5.2 Backing

The store can operate:

- **In-memory** (no persistence): constructed with `TrustStatusStore()`; assertions held in a list.
- **Persisted**: constructed with `TrustStatusStore(log_path=...)`; assertions appended to a JSONL file with a hash chain.

#### D5.5.3 Persistence format

Each line in the JSONL file is a JSON object containing:

- The serialized assertion.
- The previous line's hash.
- The current line's hash (SHA-256 over the canonical JSON of the previous two fields).

The hash chain follows the same design pattern as `monitoring/audit.py`: each line links to the previous, so tampering with any line breaks the chain from that point onward.

#### D5.5.4 API

| Method | Purpose |
|---|---|
| `append(assertion, revocation_authority=None, authorization_time=None)` | Append an assertion. If a `RevocationAuthority` is supplied, the authority's `permits()` method is called before the assertion is appended; failure raises. Duplicate `assertion_id` raises. |
| `assertions_for(subject_id)` | Return a copy of the assertions for a given subject. |
| `all_assertions()` | Return a copy of all assertions. |
| `resolve_current(subject_id, now=None, known_authority_ids=None)` | Resolve current status. See §D5.6. |
| `resolve_at(subject_id, query_time, known_authority_ids=None)` | Resolve status at a specified time. |
| `verify_integrity()` | Re-read the JSONL file and verify the hash chain. Returns `{"valid": bool, "assertions_checked": int, "error": str or null}`. |

#### D5.5.5 Integrity gate

When a `log_path` is supplied, `resolve_at` and `resolve_current` run the integrity check on every call. If the persisted chain has been tampered with, resolution returns `UNKNOWN` with a reason code of the form `integrity_check_failed: <detail>`. This is a fail-closed behavior: a tampered store does not produce a trusted answer.

### D5.6 The Deterministic Resolver

The resolver is defined at `src/enterpriseguard/adie/canonical/trust/resolver.py`. Its interface is deterministic: for the same assertion history and the same query time, it returns the same result.

#### D5.6.1 Outcomes

Every resolution returns a `ResolvedStatus` with one of three outcome values:

| Outcome | Meaning |
|---|---|
| `RESOLVED` | A trust status was determined, with an optional source assertion ID. |
| `UNKNOWN` | No applicable assertion exists, or the input is malformed, or an integrity gate failed. The result is fail-closed. |
| `CONFLICT` | Two or more assertions disagree at the same effective/observed time with different kinds. The result is fail-closed. |

#### D5.6.2 The decision table

| Input condition | Outcome | Status | Reason |
|---|---|---|---|
| Unknown authority (subject not in `known_authority_ids`) | `UNKNOWN` | — | `no_assertion_effective_at_or_before_query_time` |
| Known authority, no applicable assertion | `RESOLVED` | `ACTIVE` | `GOVERNED_INITIAL_STATE` |
| Malformed assertion input (non-`TrustStatusAssertion` in list) | `UNKNOWN` | — | `malformed_assertion_input` |
| Conflicting authoritative assertions at same time | `CONFLICT` | — | `conflicting assertions at ...` |
| Known authority with applicable assertion(s) | `RESOLVED` | as asserted | — |
| Integrity check failed on persisted store | `UNKNOWN` | — | `integrity_check_failed: ...` |

#### D5.6.3 The governed initial state

The rule for a **known authority with no applicable assertion** is the most subtle part of the resolver. It is:

```
Known + valid authority
+ no trust status assertion yet
    → GOVERNED_INITIAL_STATE
    → ACTIVE
```

This is not a fallback. It is an explicit domain invariant:

- The `Authority` object passed into the resolver **is** the establishment of a known authority. Its existence is the fact that grounds the initial `ACTIVE` state.
- The resolver distinguishes this case from `UNKNOWN` by requiring the caller to supply `known_authority_ids`. A subject not in that set cannot reach the initial state, regardless of history.
- The reason code `GOVERNED_INITIAL_STATE` is preserved on the resolution record so that a caller can distinguish an initial `ACTIVE` from an asserted `ACTIVE`.

#### D5.6.4 Historical vs current

The two interfaces `resolve_at(T)` and `resolve_current()` answer different questions:

- `resolve_at(T)` — *what was the status at time `T`?*
- `resolve_current()` — *what is the status now?*

The two answers are computed from the same history. If `T` is in the past and no subsequent assertion has an `effective_at <= T`, the two answers will differ only if a new assertion has been appended since `T`.

A **historical query does not change** as new assertions are appended:

- `resolve_at(T)` filters to assertions with `effective_at <= T`.
- Appending an assertion with `effective_at > T` does not affect a query at `T`.

This property is tested exhaustively by `test_temporal_replay.py` (41 executions).

#### D5.6.5 The conflict rule

Two assertions conflict if they have the same `effective_at` and the same `observed_at` but **different** `kinds`. The resolver returns `CONFLICT` in that case. If the kinds are the same, no conflict is raised — a duplicate assertion of the same kind is a no-op for resolution purposes.

The conflict rule is deterministic. There is no "last writer wins" or "first writer wins" interpretation. A conflicting history is a fail-closed condition.

### D5.7 The Distinct Questions

The trust layer adds a third axis to the two from D4. The three-way distinction is:

| Axis | Question answered | Enforced by |
|---|---|---|
| `DecisionLifecycle` | *Where is the artifact?* | `lifecycle_sm.transition()` |
| `AuthorizationStatus` | *Is the decision currently authorized?* | `DecisionContract.__post_init__` |
| `TrustStatus` | *Is the relevant authority trusted at the time of evaluation?* | `TrustStatusResolver.resolve_at/current` |

The three axes are independent. No substitution between them is accepted by the code:

- An assertion of `TrustStatus.REVOKED` does not cause the lifecycle to become `BLOCKED` (there is no such lifecycle value).
- An `AuthorizationStatus.DENIED` does not cause `TrustStatus.REVOKED`.
- A `DecisionLifecycle.AUTHORIZED` does not cause `TrustStatus.ACTIVE`.

Any correspondence between values on different axes must be made explicitly by an application, not by enum-name inference.

### D5.8 Temporal Semantics in Detail

#### D5.8.1 Case A — active at T1, revoked at T2

Given a timeline:

- `T1` — decision authorized; trust state `ACTIVE`.
- `T2` — revocation asserted; `effective_at = T2`.
- `T3` — current time, later than `T2`.

Then:

- `resolve_at(T1)` returns `RESOLVED / ACTIVE`.
- `resolve_at(T2+)` returns `RESOLVED / REVOKED`.
- `resolve_at(T3)` returns `RESOLVED / REVOKED`.
- A `DecisionContract` constructed at `T1` records `authority_status_at_authorization = ACTIVE`. That record is not overwritten by the later revocation.

#### D5.8.2 Case B — revocation effective in the past

Given:

- `T_effective = 2025-01-01` (a past time).
- `T_asserted = 2026-01-01` (the current time at which the revocation is written).
- `T_observed = 2026-01-01`.

Then a query at `2025-06-01` returns `RESOLVED / REVOKED`, because the assertion's `effective_at` is before the query time. The assertion applies retroactively **to the extent of its effective timestamp**; it does not apply to times earlier than `effective_at`.

#### D5.8.3 Case C — conflicting assertions

Given two assertions with identical `effective_at` and `observed_at`, but kinds `REVOKE` and `SUSPEND`:

- A query at or after that time returns `CONFLICT`, not one of the two statuses.
- The resolver does not silently choose one.

#### D5.8.4 Case D — unauthorized revocation

If a caller attempts to append a revocation without a `RevocationAuthority`, or with an authority that does not permit that subject/kind, the store raises `RevocationNotPermittedError`. No assertion is appended.

#### D5.8.5 Case E — replay

Repeated calls with identical inputs return identical results. The resolver has no internal state; the outcome is a pure function of `(subject_id, query_time, assertions, known_authority_ids)`.

### D5.9 Anti-Bypass Invariants

The 3C anti-bypass suite is `tests/vomega/trust/test_anti_bypass_3c.py`. It tests 13 classes of bypass; these are supplemented by the anti-bypass assertions in `test_status_semantics.py`, `test_resolver.py`, and `test_governed_initial_state.py`. The combined coverage includes:

| # | Invariant |
|---|---|
| X01 | Append without a `RevocationAuthority` is permitted only as an explicit `None` call (documented exception for test use). |
| X02 | Out-of-scope subject rejection. |
| X03 | Forged `RevocationKind` rejection. |
| X04 | Empty `subject_id` rejection. |
| X05 | Naive datetime rejection. |
| X06 | Empty `authority_ref` rejection. |
| X07 | Conflicting assertions → `CONFLICT`. |
| X08 | Inactive authority rejection (before window). |
| X09 | Inactive authority rejection (after window). |
| X10 | Inactive authority rejection (other cases). |
| X12 | Historical query at `T` unaffected by later assertions. |
| X17 | Unknown subject does not fall open. |
| X19 | Replay identical. |
| X20 | Distinct authorities have distinct IDs. |

Together with the 41 executions of `test_temporal_replay.py` (Cases A–E) and the 18 executions of `test_governed_initial_state.py` (G01–G18), the trust layer's rejection and temporal behavior is exercised comprehensively.

### D5.10 Evidence Summary

#### D5.10.1 Test suites covering D5

| Suite | Executions | Role |
|---|---|---|
| `tests/vomega/trust/test_status_semantics.py` | 23 | `TrustStatus` axis semantics |
| `tests/vomega/trust/test_revocation_authority.py` | 21 | `RevocationAuthority` validation and `permits` |
| `tests/vomega/trust/test_assertion.py` | 19 | assertion validation and fingerprint |
| `tests/vomega/trust/test_resolver.py` | 27 | resolver determinism and outcomes |
| `tests/vomega/trust/test_history.py` | 18 | store append/persist/integrity |
| `tests/vomega/trust/test_temporal_replay.py` | 41 | Cases A–E, historical/current distinction |
| `tests/vomega/trust/test_anti_bypass_3c.py` | 13 | 3C anti-bypass classes |
| `tests/vomega/trust/test_decision_trust_integration.py` | 13 | integration with canonical `DecisionContract` |
| `tests/vomega/trust/test_governed_initial_state.py` | 18 | DEFECT-043 boundaries (known/unknown/malformed/conflict) |
| **Trust subtotal** | **193** | |

**Note on category separation.** The 193 executions are executions, not unique vectors. See §E3.9.

#### D5.10.2 Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `src/enterpriseguard/adie/canonical/trust/status.py` | `a3975f7f7365dbe9029e8ec46eaa0eca9890c5a3d185c1a73ec2808eb55ceeb4` |
| `src/enterpriseguard/adie/canonical/trust/resolver.py` | `4a3263dbf11c8b4dcc76a74c9ebd3d7ae9e93e918907cd75d4632b403979f6f9` |
| `src/enterpriseguard/adie/canonical/trust/history.py` | `99b14a828543acb199ebb31fb6c1411ad1ee4b3c72d59c6491856897603d78a5` |
| `src/enterpriseguard/adie/canonical/trust/assertion.py` | (see Appendix B) |
| `src/enterpriseguard/adie/canonical/trust/authority_to_revoke.py` | (see Appendix B) |
| `src/enterpriseguard/adie/canonical/trust/__init__.py` | (see Appendix B) |

#### D5.10.3 Reproduction — full D5 set

```bash
cd ~/Desktop/EnterpriseGuard && \
for f in test_status_semantics test_revocation_authority test_assertion \
         test_resolver test_history test_temporal_replay test_anti_bypass_3c \
         test_decision_trust_integration test_governed_initial_state; do
  PYTHONPATH=src .venv/bin/python tests/vomega/trust/$f.py
done
```

**Expected:** 23 + 21 + 19 + 27 + 18 + 41 + 13 + 13 + 18 = 193 executions, 0 failures.

**Commit.** `7683adb` (branch `vOmega`). The trust layer itself was introduced at commit `9f9bd9b`.

### D5.11 What D5 Does Not Claim

- D5 does not claim that the trust model is a certificate revocation system in the X.509 sense. It is a governed, append-only status-assertion model. See §E2.2.4 for the distinction.
- D5 does not claim that `RevocationAuthority` is a substitute for a global trust root. The authority is established by the caller; its existence is a precondition for the model's operations. This is a documented assumption (F-04, F-05; see §E6.5 and §D11).
- D5 does not claim that the resolver's `CONFLICT` outcome covers all possible disagreement scenarios. It covers the specific case of two assertions with identical effective and observed times and different kinds. Other configurations may resolve to a single status by the ordering rules.
- D5 does not claim that the append-only store's hash chain is a full tamper-evidence mechanism against an adversary with write access. As with `monitoring/audit.py`, the chain provides tamper evidence, not authenticity against a full-file rewrite.
- D5 does not claim that the `GOVERNED_INITIAL_STATE` rule is a universal convention. It is the rule vOmega adopts, established as an explicit domain invariant in DEFECT-043. A different profile might define a different rule; the reason code exists precisely to make the rule visible.
- D5 does not claim performance characteristics. The resolver's integrity gate runs `verify_integrity()` on each call, which is O(N) in the size of the store. This is documented as a known scaling limitation (F-08; see §E6.10 and §D11).

---

## D6. End-to-End Assurance (3D / 3D-R1)

**Part II, Section D6.**
**Scope:** the end-to-end assurance path introduced in Phase 3D and corrected in Phase 3D-R1 — the composition of wire validation, cryptographic verification, evidence, authority, trust evaluation, decision formation, lifecycle transitions, and manifest emission, terminating at an explicit external-execution boundary.

### D6.1 Scope and Lineage

Phase 3D introduced the **end-to-end assurance path** — a composition of the layers documented in D1–D5 that terminates at an explicit external-execution boundary. Phase 3D-R1 was a corrective cycle triggered by an independent adversarial review of 3D.

The two phases are distinct and both are documented here:

| Phase | Close commit | Suites | Executions | Outcome |
|---|---|---|---|---|
| **3D** (initial path) | `7c0c36a` | 10 | **196** | Path established; three assurance gaps identified by review. |
| **3D-R1** (remediation) | `7683adb` | 12 | **225** | Three gaps closed (DEFECT-044, DEFECT-045, DEFECT-046). |

**Documentation convention (per Commander's guidance on D4 and D5).** The 3D phase was **closed** at `7c0c36a` with 196 executions across 10 suites. The 3D-R1 remediation cycle was **closed** at `7683adb` with 225 executions across 12 suites. In this instance, the evidence-reference commit for the dossier (`7683adb`) coincides with the 3D-R1 phase close. Both figures are correct in their respective contexts.

The 3D close commit `7c0c36a` reports **196 E2E executions across 10 suites**, plus the trust-side `test_governed_initial_state.py` suite (18 executions, counted in §D5). This document's §D6.3 uses the E2E-only figure (196) for the end-to-end path; the full 3D close scope is 10 E2E suites + 1 trust suite.

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && \
git log --oneline -1 7c0c36a && \
git log --oneline -1 7683adb
```

### D6.2 The End-to-End Chain

The end-to-end path is implemented in `src/enterpriseguard/adie/canonical/integration/e2e.py`. It composes the following stages in a fixed order. Each stage may either accept the input and pass it to the next stage, or reject it with a specific `E2EOutcome` value.

```
Stage 1     Wire round-trip            ─── REJECTED_WIRE on failure
                ↓
Stage 1.5   Cryptographic verification ─── REJECTED_CRYPTO on failure
                ↓
Stage 2     Evidence check             ─── REJECTED_EVIDENCE on failure
                ↓
Stage 3     Authority check            ─── REJECTED_AUTHORITY on failure
                ↓
Stage 4     Trust-status evaluation    ─── REJECTED_TRUST on failure
                ↓
Stage 5     Decision formation         ─── REJECTED_EVIDENCE / REJECTED_POLICY
                ↓
Stage 6     Lifecycle transitions      ─── REJECTED_LIFECYCLE on failure
                ↓
Stage 7     Manifest emission          ─── REJECTED_MANIFEST on failure
                ↓
            ACCEPTED
                ↓
        EXTERNAL EXECUTION BOUNDARY (not crossed)
```

#### D6.2.1 Stage 1 — Wire round-trip

The certificate is passed through the B+ envelope:

- Encode the certificate into an envelope via `envelope_from_certificate`.
- Parse the envelope back via `parse_envelope_to_certificate`.
- Verify that the recovered `claim_id` matches the original.

Any failure returns `REJECTED_WIRE`. This stage is optional: it can be skipped by setting `require_wire_roundtrip=False` (used by some tests where the certificate is already known to be envelope-clean).

#### D6.2.2 Stage 1.5 — Cryptographic verification

When `require_crypto_verification=True`, the certificate is passed to the 3A cryptographic verifier (`protocol/hybrid/verify.py`):

- The TBS is recomputed from the certificate body (without `signatures`).
- The RS256 and ML-DSA-65 signatures are verified against that TBS.
- Both signatures must validate; the hybrid policy requires both.

Any failure returns `REJECTED_CRYPTO`. Missing public keys are also a `REJECTED_CRYPTO` result, with a `crypto` stage reason code of `missing_keys`.

**This stage was added in 3D-R1** (DEFECT-044). In the original 3D path, crypto verification was not performed; this is the first of the three gaps closed by the corrective cycle.

#### D6.2.3 Stage 2 — Evidence check

The `evidence` input must be a `DecisionEvidence` instance (from D4). Any other type returns `REJECTED_EVIDENCE`. This is a type-check, not a semantic evaluation.

#### D6.2.4 Stage 3 — Authority check

The `authority` input must be a non-`None` `Authority` instance (from D4). Additionally:

- The authority must be active at the evaluation time.
- The authority's `scope` must match the caller-supplied scope.

Any failure returns `REJECTED_AUTHORITY`.

#### D6.2.5 Stage 4 — Trust-status evaluation

The trust status of the authority is resolved via the trust layer (D5):

- If a `trust_store` is supplied, the resolver runs against the store; the store's integrity gate participates.
- Otherwise, the resolver runs against the in-memory `trust_assertions` list.
- The `known_authority_ids` set includes the authority's ID (establishing it as a known authority).

Any `UNKNOWN` or `CONFLICT` outcome returns `REJECTED_TRUST`. A status other than `ACTIVE` also returns `REJECTED_TRUST`, with the specific status recorded in the `provenance`.

**The ability to pass a `trust_store` was added in 3D-R1** (DEFECT-046). In the original 3D path, only the in-memory assertions list was used; the store's append-only history and integrity gate were not exercised.

#### D6.2.6 Stage 5 — Decision formation

The `DecisionEngine` (from D4) evaluates the evidence and produces a `DecisionContract` in the `PROPOSED` lifecycle state. A policy-denied evidence leads to `REJECTED_POLICY`, with the contract not progressing further.

#### D6.2.7 Stage 6 — Lifecycle transitions

The contract is transitioned through the canonical lifecycle:

- `PROPOSED → VALIDATED`
- `VALIDATED → AUTHORIZED`

The authorization status is set to `AUTHORIZED`, and the trust status at the moment of authorization is recorded in `authority_status_at_authorization`.

Illegal transitions raise `LifecycleTransitionError`, which the integration wraps as `REJECTED_LIFECYCLE`.

#### D6.2.8 Stage 7 — Manifest emission

When a `manifest_context` is supplied, the integration constructs a real `ExecutionManifest` via `ExecutionManifest.from_intent`. The manifest carries:

- The canonical `DecisionReference` (pointing at `adie.decision.DecisionContract` version 3.0.1).
- The decision's lifecycle state.
- The authority identity and the trust status at authorization, in `governance_metadata`.

When `manifest_context` is not supplied, no manifest is emitted — a deliberate choice that avoids a parallel dict-shaped manifest (see §D6.5.3).

**The real `ExecutionManifest` was adopted in 3D-R1** (DEFECT-045). In the original 3D path, a hand-rolled dict was used in place of the production contract.

#### D6.2.9 The external-execution boundary

The end-to-end path terminates at the point where a manifest is emitted. It does not call any executor. The lifecycle value `EXECUTED_EXTERNAL` is not set by this path — it is defined as a separate state to be set by an external observer (see §D4.5.3).

### D6.3 Phase 3D — Initial Path

Phase 3D established the end-to-end path with ten suites totalling **196 executions**:

| Suite | Executions | Role |
|---|---|---|
| `test_e2e_happy_path.py` | 14 | accept and reject basic paths |
| `test_e2e_trust_matrix.py` | 18 | trust status permutations |
| `test_e2e_lifecycle_sm.py` | 28 | lifecycle transition matrix |
| `test_e2e_crypto_gov_mismatch.py` | 9 | adversarial cross-layer cases (A–F) |
| `test_e2e_provenance.py` | 11 | provenance trace on accept and reject |
| `test_e2e_legacy_bypass.py` | 11 | legacy and malformed input routing |
| `test_e2e_replay_deterministic.py` | 72 | deterministic replay under fixed and altered inputs |
| `test_e2e_failure_injection.py` | 11 | failure at each layer |
| `test_e2e_no_mutation.py` | 8 | immutability proof |
| `test_e2e_manifest_boundary.py` | 14 | manifest content, execution-boundary invariants |
| **3D subtotal** | **196** | |

Phase 3D was closed at commit `7c0c36a`. Its initial evidence base is documented in `docs/vomega/CONTINUITY.md` §58.

### D6.4 The Adversarial Review

Following Phase 3D, an independent adversarial review was performed on the complete 3A → 3D chain. The review was **read-only** and **posture-as-adversary**: it assumed the claims were unsupported until traced to concrete code paths.

The review found three assurance gaps in the 3D path. All three had the same character: the stage's own documentation claimed a behavior that the code path did not actually enforce.

| Finding | Severity | Claim in 3D | Actual behavior in 3D |
|---|---|---|---|
| **F-01** | CRITICAL | "Cryptographic verification is part of the end-to-end path." | Crypto verification was never invoked. A structurally valid certificate with garbage signatures could reach `ACCEPTED`. |
| **F-02** | HIGH | "The end-to-end path uses the production `ExecutionManifest`." | A hand-rolled dict was used. The production `ExecutionManifest` class was imported but never instantiated. |
| **F-03** | HIGH | "The end-to-end path exercises the production trust store." | An in-memory assertions list was passed directly to the resolver. The append-only store, its hash chain, and its integrity gate were not involved. |

Additionally, the review recorded several non-blocking findings (F-04 through F-11), documented in §D11.

**The three blocking findings were addressed in 3D-R1.** The non-blocking findings remain documented as known limitations.

### D6.5 Phase 3D-R1 — Remediation

The 3D-R1 cycle was designed to close only the three blocking findings. It did not redesign the end-to-end path; it filled in the parts that the path had been claiming without exercising.

#### D6.5.1 F-01 — Cryptographic verification (DEFECT-044)

The end-to-end integration was extended with an optional cryptographic verification stage (`require_crypto_verification=True`). When enabled:

- The 3A verifier (`protocol.hybrid.verify.verify_hybrid`) is invoked on the certificate.
- The verifier is passed the certificate body (without `signatures`), the signatures array, and the caller-supplied public keys.
- The hybrid policy requires both RS256 and ML-DSA-65 to validate.

A new outcome value `REJECTED_CRYPTO` was added to `E2EOutcome`. Failures at this stage — including missing public keys, malformed base64, wrong signature bytes, tampered signatures, or downgrade attempts — return `REJECTED_CRYPTO` and never reach `ACCEPTED`.

**Test coverage.** A new suite, `test_e2e_crypto_verification.py`, was added with 12 executions covering:

| # | Case |
|---|---|
| C01 | valid hybrid accepted |
| C02 | corrupted RS256 rejected |
| C03 | RS256-only rejected (downgrade) |
| C04 | corrupted ML-DSA-65 rejected |
| C05 | ML-DSA-65-only rejected (downgrade) |
| C06 | both signatures tampered rejected |
| C07 | empty signatures array rejected |
| C08 | malformed base64 in signature rejected |
| C09 | all-zero signature bytes rejected |
| C10 | valid crypto + revoked trust → `REJECTED_TRUST` (not `REJECTED_CRYPTO`) |
| C11 | missing public keys rejected |

C10 is the load-bearing case: it confirms that the crypto layer and the trust layer remain **separate**. A cryptographically valid certificate with a revoked authority is rejected by the **trust** layer, not by the crypto layer. The two layers do not collapse into one.

**DEFECT record.** DEFECT-044 in `DEFECTS-LOG.md`.

#### D6.5.2 F-03 — Real trust store (DEFECT-046)

The end-to-end integration was extended with an optional `trust_store` parameter. When supplied:

- The resolver runs against the store, not against an in-memory list.
- The store's `_integrity_gate` runs on each resolution.
- A tampered JSONL chain produces `UNKNOWN` with reason code `integrity_check_failed: ...`, which the integration maps to `REJECTED_TRUST`.

The rejection reason now propagates the resolver's own reason string, so callers can distinguish `integrity_check_failed` from `no_assertion_effective_at_or_before_query_time`.

**Test coverage.** A new suite, `test_e2e_trust_store_real.py`, was added with 12 executions covering:

| # | Case |
|---|---|
| TS01 | empty store → accepted (governed initial state) |
| TS01b | stages confirm `trust_source=store` |
| TS01c | manifest is real `ExecutionManifest` |
| TS02 | revoke via store → `REJECTED_TRUST` |
| TS03 | historical query at time before revocation → accepted |
| TS04 | suspend effective later does not override an earlier revoke |
| TS05 | store integrity valid |
| TS06 | tampered store → `REJECTED_TRUST` with integrity reason |
| TS07 | in-memory store works |
| TS08 | two E2E runs against same store are deterministic |

**DEFECT record.** DEFECT-046 in `DEFECTS-LOG.md`.

#### D6.5.3 F-02 — Real `ExecutionManifest` (DEFECT-045)

The end-to-end integration was extended with an optional `manifest_context` parameter. When supplied:

- An `ExecutionIntent` is constructed.
- The production `ExecutionManifest.from_intent(...)` is called.
- The resulting `ExecutionManifest` instance is returned as `E2EResult.manifest`.

When `manifest_context` is not supplied, `manifest` is `None`. **No parallel dict-shaped manifest is emitted.** This is the deliberate choice that closes F-02: the path either emits the production contract, or emits nothing — it never emits a substitute.

**Test coverage.** The existing `test_e2e_manifest_boundary.py` was rewritten to assert:

- `isinstance(manifest, ExecutionManifest)` when a context is supplied.
- `manifest.decision_reference.contract_type == "adie.decision.DecisionContract"`.
- `manifest.decision_reference.contract_version == "3.0.1"`.
- `manifest.status is ManifestStatus.DRAFT`.
- `manifest.eligibility is ExecutionEligibility.NOT_ELIGIBLE`.
- `manifest.governance_metadata` carries the trust status and authority ID.
- `manifest is None` on the reject paths.

The rewritten suite has 19 executions (up from 14 in 3D).

**DEFECT record.** DEFECT-045 in `DEFECTS-LOG.md`.

#### D6.5.4 Accounting for the 225 executions

The 3D-R1 suite total is composed as follows:

| Source | Suites | Executions |
|---|---|---|
| 3D initial | 10 | 196 |
| 3D-R1 new suites (`crypto_verification`, `trust_store_real`) | +2 | +24 |
| 3D-R1 upgrade of `manifest_boundary` (14 → 19) | — | +5 |
| **3D-R1 total** | **12** | **225** |

The `+24` and `+5` are the direct measure of the 3D-R1 remediation in test-execution terms.

### D6.6 The `E2EOutcome` Classifier

The end-to-end integration returns an `E2EResult` whose `outcome` field is one of nine values:

| Outcome | Meaning |
|---|---|
| `ACCEPTED` | All stages passed; a decision was emitted. |
| `REJECTED_WIRE` | Wire round-trip failed. |
| `REJECTED_CRYPTO` | Cryptographic verification failed or was not possible. |
| `REJECTED_EVIDENCE` | Evidence input was not a valid `DecisionEvidence`. |
| `REJECTED_AUTHORITY` | Authority was missing, invalid, inactive, or out of scope. |
| `REJECTED_TRUST` | Trust status was `UNKNOWN`, `CONFLICT`, or a non-`ACTIVE` value. |
| `REJECTED_LIFECYCLE` | A lifecycle transition was illegal. |
| `REJECTED_POLICY` | Policy denied the decision at the decision stage. |
| `REJECTED_MANIFEST` | Manifest emission failed. |

An `E2EResult` also carries:

- `decision`: the accepted `DecisionContract` (or `None`).
- `manifest`: the accepted `ExecutionManifest` (or `None`).
- `envelope_bytes`: the envelope bytes from Stage 1 (or `None`).
- `stages`: a mapping of stage name → status string (e.g., `{"wire": "accepted", "crypto": "verified", ...}`).
- `provenance`: a mapping of provenance keys to values.

**A rejection with a specific outcome value is not a generic "rejected".** The typed outcomes are the entire point: a caller can distinguish a cryptographic failure from a governance failure from a trust failure from a policy failure, and route the response accordingly.

### D6.7 Cross-Layer Adversarial Cases

The suite `test_e2e_crypto_gov_mismatch.py` (9 executions) and the extended coverage in the 3D-R1 suites exercise specific adversarial combinations. The load-bearing cases are:

| Case | Description | Expected outcome |
|---|---|---|
| **A** | Crypto valid, authority revoked | `REJECTED_TRUST` — governance unauthorized, not crypto |
| **B** | Crypto invalid, authority active | `REJECTED_CRYPTO` — crypto failure must not be silently absorbed by an active authority |
| **C** | Valid artifact, future-effective revocation | `ACCEPTED` — governed initial state applies at the current time |
| **D** | Valid artifact, no trust history | `ACCEPTED` — governed initial state applies |
| **E** | Valid artifact, conflicting trust assertions | `REJECTED_TRUST` — conflict is fail-closed |
| **F** | Past-effective revocation vs future-effective revocation | Distinction preserved — the two produce different outcomes at the current time |

Cases A and B together are the core demonstration: **crypto validity and governance validity are independent**. Neither can substitute for the other. A cryptographically valid certificate with a revoked authority fails at the trust stage; a cryptographically invalid certificate with an active authority fails at the crypto stage.

This is the same architectural property that the two-axis model of D4 establishes at the governance level, extended now to a third axis (trust) and to a fourth layer (crypto).

### D6.8 Determinism and Replay

The end-to-end path is deterministic. For the same inputs — same certificate, same evidence, same authority, same trust history, same time — the same outcome and the same decision ID are produced.

The `test_e2e_replay_deterministic.py` suite (72 executions) verifies:

- **20× accept replay.** The same inputs produce the same `E2EResult` outcome, the same `decision_id`, and the same provenance on every run.
- **10× reject replay.** The same rejection inputs produce the same rejection outcome on every run.
- **Single-input divergence.** When exactly one input changes (trust assertion, evidence policy, authority scope), the outcome diverges in the expected direction, deterministically.

The determinism property does not depend on external state or on wall-clock variance within a single run. Given the same inputs and the same `at` timestamp, the outcome is reproducible.

### D6.9 Failure Injection

The `test_e2e_failure_injection.py` suite (11 executions) exercises a failure at each stage of the pipeline:

| # | Failure | Stage that rejects |
|---|---|---|
| FI01 | malformed wire (subject not object) | Stage 1 |
| FI02 | missing `binding` field | Stage 1 |
| FI03 | invalid `claim_root` | Stage 1 or later |
| FI04 | missing authority | Stage 3 |
| FI05 | inactive authority window | Stage 3 |
| FI06 | policy denied | Stage 5 |
| FI07 | revoked authority | Stage 4 |
| FI08 | conflicting trust assertions | Stage 4 |
| FI09 | invalid evidence type | Stage 2 |
| FI10 | empty target resource (documented, returns result) | not rejected |
| FI11 | naive datetime (raises) | input validation |

The suite verifies that **each failure is caught at the earliest stage capable of detecting it**. A failure in wire format does not reach trust evaluation; a failure in trust does not reach the decision stage; a policy denial at the decision stage does not incorrectly appear as a crypto failure.

### D6.10 Evidence Summary

#### D6.10.1 Test suites covering D6

| Suite | Executions | Role | Phase |
|---|---|---|---|
| `test_e2e_happy_path.py` | 14 | accept and reject basics | 3D, upgraded in 3D-R1 |
| `test_e2e_trust_matrix.py` | 18 | trust status permutations | 3D |
| `test_e2e_lifecycle_sm.py` | 28 | lifecycle transition matrix | 3D |
| `test_e2e_crypto_gov_mismatch.py` | 9 | adversarial cross-layer cases | 3D |
| `test_e2e_provenance.py` | 11 | provenance trace | 3D |
| `test_e2e_legacy_bypass.py` | 11 | legacy/malformed routing | 3D |
| `test_e2e_replay_deterministic.py` | 72 | deterministic replay | 3D |
| `test_e2e_failure_injection.py` | 11 | failure at each layer | 3D |
| `test_e2e_no_mutation.py` | 8 | input immutability | 3D |
| `test_e2e_manifest_boundary.py` | 19 | manifest content, execution-boundary invariants | 3D, upgraded in 3D-R1 |
| `test_e2e_crypto_verification.py` | 12 | crypto verification (F-01) | 3D-R1 |
| `test_e2e_trust_store_real.py` | 12 | real store in path (F-03) | 3D-R1 |
| **3D-R1 total** | **225** | | |

**Note on category separation.** The 225 executions are executions, not unique vectors. See §E3.9.

#### D6.10.2 Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `src/enterpriseguard/adie/canonical/integration/e2e.py` | `0f16bc2ecb04a9481f9d1950cf0c0c1d0d6aebe37ec170b0e758719e08097894` |
| `protocol/hybrid/verify.py` | `2d285fc50c43ae1c08bc7dd577657925cc08faf6deb9bbd1e3e8d5c6b48a7df5` |
| `src/enterpriseguard/adie/execution_manifest.py` | (see Appendix B) |
| `src/enterpriseguard/adie/execution_contract.py` | (see Appendix B) |

#### D6.10.3 Reproduction — full D6 set

```bash
cd ~/Desktop/EnterpriseGuard && \
for f in test_e2e_happy_path test_e2e_trust_matrix test_e2e_lifecycle_sm \
         test_e2e_crypto_gov_mismatch test_e2e_provenance test_e2e_legacy_bypass \
         test_e2e_replay_deterministic test_e2e_failure_injection \
         test_e2e_no_mutation test_e2e_manifest_boundary \
         test_e2e_crypto_verification test_e2e_trust_store_real; do
  PYTHONPATH=src .venv/bin/python tests/vomega/e2e/$f.py
done
```

**Expected:** 14 + 18 + 28 + 9 + 11 + 11 + 72 + 11 + 8 + 19 + 12 + 12 = **225 executions, 0 failures**.

**Commit.** `7683adb` (branch `vOmega`).

#### D6.10.4 Historical note on the 3D vs 3D-R1 accounting

The 3D phase's initial evidence base (documented in `CONTINUITY.md` §58) reports **196 executions** across 10 suites. The 3D-R1 remediation reports **225 executions** across 12 suites. The difference (29) decomposes as:

- **+24** from two new suites: `test_e2e_crypto_verification.py` (12) and `test_e2e_trust_store_real.py` (12).
- **+5** from upgrading `test_e2e_manifest_boundary.py` from 14 to 19 executions.

Both figures are historically accurate. The 3D close figure (196) is not retroactively adjusted; the 3D-R1 close figure (225) is the current evidence state.

### D6.11 What D6 Does Not Claim

- D6 does not claim that the end-to-end path is production-ready. It composes the D1–D5 layers in a controlled local environment; production deployment is documented as outside scope (§E6.1).
- D6 does not claim that the 3D path was wrong and the 3D-R1 path is right. It documents that the 3D path had three assurance gaps that its own documentation did not reflect; the 3D-R1 cycle corrected the code to match the documentation, and the corrected code is what §D6.2 describes.
- D6 does not claim that the end-to-end path performs external execution. It terminates at the manifest-emission boundary; the `EXECUTED_EXTERNAL` lifecycle state is not set by this path (§D4.5.3).
- D6 does not claim that the crypto layer subsumes the trust layer, or vice versa. Cases A and B in §D6.7 are the specific demonstration that the layers are independent.
- D6 does not claim that the path is complete relative to any external specification. The path is complete relative to vOmega's own architectural layers; extensions to those layers would require extensions to this path.
- D6 does not claim that the DeepSeek review found every gap. It found the gaps that were present at the time of review; additional gaps may exist outside the review's coverage.
- D6 does not claim that the 3D-R1 correction was free of its own defects. The DEFECT-044/045/046 records document the gaps and their corrections; a subsequent adversarial review of 3D-R1 was not performed as part of this dossier. The absence of such a review is itself a fact recorded in §D11.

---


## D7. Cryptographic Identity — Invariants Preserved

**Part II, Section D7.**
**Scope:** The cryptographic-identity invariants preserved unchanged across Phase 1, Phase 2, and vOmega.
**Frozen upstream:** `spec/HYBRID-CRYPTO-0.1.md` §5 (TBS definition, unchanged by vOmega); §D2.5 of this document; §E2.2.3.

---

### D7.1 Scope and Lineage

Phase 1 defined the ADIE certificate and the ClaimRoot identity. Phase 2 introduced the hybrid signature scheme (RS256 + ML-DSA-65) and the TBS construction. Phase 3 (vOmega) added a deterministic wire layer and a CBOR envelope above the certificate, without changing the bytes over which signatures are computed.

This section documents the **invariants preserved unchanged** across all three phases. It is a section about **what did not change**.

**What D7 does not do.**

- D7 does not introduce a new cryptographic primitive.
- D7 does not claim that the B+ envelope redesigned the signature scheme.
- D7 does not claim that the TBS construction is novel.
- D7 records the preservation of the existing cryptographic identity model across Phase 1 → Phase 2 → B+ integration.

**Phase-close references.**

| Phase | Reference | Status |
|---|---|---|
| Phase 1 | `PHASE-1-CLOSURE.md` | Closed |
| Phase 2 | `PHASE-2-CLOSURE.md` | Closed |
| vOmega (3A–3D-R1) | `7683adb` (branch `vOmega`) | Current evidence state |

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && \
git log --oneline -1 7683adb && \
head -30 docs/vomega/PHASE-1-CLOSURE.md && \
head -30 docs/vomega/PHASE-2-CLOSURE.md
```

---

### D7.2 TBS Invariants

The To-Be-Signed bytes are defined by `spec/HYBRID-CRYPTO-0.1.md` §5:

```
TBS = "ADIE-SIG-V2\0" ‖ JCS(certificate_without_signatures)
```

The definition did not change across phases. The invariants are:

#### D7.2.1 Invariant 1 — Domain tag prefix

The TBS begins with the 12-byte domain tag. It is not nulled, not replaced, not reordered. It is a strict prefix of the TBS byte sequence.

#### D7.2.2 Invariant 2 — JCS canonicalization of the certificate body

The certificate body that follows the tag is canonicalized per RFC 8785 (JSON Canonicalization Scheme). The canonicalization is:

- **Deterministic** — the same certificate body yields the same JCS bytes.
- **Sorted-key** — object keys are sorted by UTF-16 code unit as specified in RFC 8785.
- **Minimal-escape** — escaping is minimal, as specified in RFC 8785.
- **No trailing whitespace** — there is no BOM, no leading or trailing whitespace.

#### D7.2.3 Invariant 3 — The `signatures` field is removed, not nulled

The certificate used to compute the TBS has its `signatures` field **removed** — not set to `null`, not set to `[]`, not set to `{}`. This distinction is material: a certificate with `"signatures": []` produces a different TBS than the same certificate with the field absent.

This is tested by `tests/vomega/hybrid/test_tbs.py` (T05, T06).

#### D7.2.4 Invariant 4 — No CBOR envelope participation

The TBS is computed from the semantic certificate. It does not include the CBOR envelope. The envelope carries the semantic certificate but does not define its cryptographic identity.

See §D2.5 and §D7.5.

#### D7.2.5 Evidence

| Language | Suite | Executions | Role |
|---|---|---|---|
| Python | `tests/vomega/hybrid/test_tbs.py` | 12 | TBS construction: tag, JCS, field removal |
| Python | `tests/vomega/hybrid/test_e2e.py` | 11 | Full issue/sign/verify cycle |
| Python | `tests/vomega/b-plus/test_bplus_e2e.py` | 10 | **H09 — TBS byte-identity after envelope round-trip** |

**Reproduction — TBS invariants:**

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ TBS construction (12) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_tbs.py && \
echo "═══ E2E hybrid (11) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_e2e.py && \
echo "═══ H09 — TBS byte-identity after envelope round-trip ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_e2e.py | grep "H09"
```

**Expected:**

- TBS construction: `TOTAL: 12 | PASS: 12 | FAIL: 0`
- E2E hybrid: `TOTAL: 11 | PASS: 11 | FAIL: 0`
- H09: `[PASS] H09 TBS byte-identical after envelope round-trip`

**Commit.** `7683adb` (branch `vOmega`).

**Reproducible Artifact / Hash.** `protocol/hybrid/tbs.py` — SHA-256 `fe6e14d503c3f2e8d224ec058eb5744603778d5b7803fd8d6d6d612296c836e3`.

---

### D7.3 Domain Tag Invariants

| Property | Value |
|---|---|
| String form | `"ADIE-SIG-V2\0"` (11 visible characters + NUL) |
| Byte length | **12 bytes** |
| Hex form | `414449452d5349472d563200` |
| Position in TBS | Prefix (bytes 0..11) |
| Definition source | `spec/HYBRID-CRYPTO-0.1.md` §5 |

#### D7.3.1 Why the tag exists

The tag is a **domain-separation marker**. Its purpose is to ensure that a signature produced over an ADIE certificate cannot be valid for any other protocol whose TBS construction happens to coincide with a JCS-canonicalized JSON document. The tag declares the protocol version and isolates the signing domain.

`V2` in the tag indicates the second-generation TBS construction.

#### D7.3.2 Why it is 12 bytes

The string `"ADIE-SIG-V2\0"` is 11 visible ASCII characters plus one NUL terminator = **12 bytes**. The NUL terminator is intentional: it provides an unambiguous boundary between the tag and the JCS bytes that follow, so that a tag like `"ADIE-SIG-V2"` (no NUL, 11 bytes) cannot be confused with a certificate that starts with the byte `\x00`.

This was the subject of **DEFECT-013**, whose closure is recorded in `DEFECTS-LOG.md`. DEFECT-013 is a **historical defect closure**; it is not an independent cryptographic evidence source.

#### D7.3.3 Cross-phase stability

The tag has been the same byte sequence in:

- Phase 1 — as the identity marker for the certificate format.
- Phase 2 — as the TBS prefix for the hybrid signature scheme.
- vOmega — unchanged; the wire layer does not touch it.

A future COSE-native profile (Amendment-1 §A6) would use a **different** tag. The current tag is not repurposed. vOmega does not implement that future profile.

#### D7.3.4 Evidence

| Suite | Test IDs | What the test demonstrates |
|---|---|---|
| `test_tbs.py` | T01, T02 | Tag length = 12; exact byte sequence |
| `test_tbs.py` | T03, T04 | TBS starts with tag; body is JCS |
| `test_bplus_e2e.py` | **H10** | Domain tag **preserved** through B+ round-trip (12 bytes) |

**On the interpretation of H10.** H10 does not demonstrate signature validity. It demonstrates **preservation of the domain tag** through a full envelope round-trip. Signature validity is a separate claim, evidenced by H03 and the verification suites (§D7.4).

**Reproduction:**

```bash
cd ~/Desktop/EnterpriseGuard && \
python3 -c "
import sys
sys.path.insert(0, '.')
from protocol.hybrid.tbs import DOMAIN_TAG
print('len:', len(DOMAIN_TAG))
print('hex:', DOMAIN_TAG.hex())
assert len(DOMAIN_TAG) == 12
assert DOMAIN_TAG.hex() == '414449452d5349472d563200'
print('OK — domain tag invariant holds')
"
```

**Expected:**

```
len: 12
hex: 414449452d5349472d563200
OK — domain tag invariant holds
```

---

### D7.4 Phase 1 and Phase 2 Signatures Remain Valid

A central claim of this document is that **signatures produced under Phase 1 and Phase 2 remain valid under vOmega**, without re-issuance, without modification, and without a version bump on the certificate.

#### D7.4.1 What would invalidate a signature

A signature becomes invalid if the bytes over which it was computed change. The bytes are the TBS. The TBS is a function of:

- The domain tag (unchanged — §D7.3).
- The certificate body (canonicalized by JCS — §D7.2).

The certificate body is what the issuer signed. vOmega does not modify it when the certificate is carried over the wire. The CBOR envelope is a transport representation; it carries the same semantic certificate (§D2.3.2).

#### D7.4.2 What would not invalidate a signature

- Adding a CBOR envelope around the certificate.
- Changing the CBOR library that produces the envelope.
- Changing the wire profile version — provided the certificate body remains canonically recoverable.
- Storing the certificate in a different container format (e.g., a file), as long as the semantic content is preserved.

None of these operations alter the TBS.

#### D7.4.3 The compatibility claim, stated precisely

The claim is not "a Phase 1 signature verifies under a Phase 3 verifier" in an unconditional sense. The claim is:

> Given a Phase 1 or Phase 2 certificate, its original signatures, and the corresponding public keys, a vOmega verifier computes the same TBS as the Phase 1 or Phase 2 signer computed, and verifies the signatures against it.

The "same TBS" phrase is the load-bearing part. It is what **H09** tests: after a full envelope round-trip (certificate → envelope → certificate), the recovered certificate's TBS is byte-identical to the original.

#### D7.4.4 The determinism claim, stated precisely

The signing path is **not** claimed to produce deterministic signatures in a general FIPS 204 sense. The claim is limited to the tested implementation:

> **S11** (in `tests/vomega/hybrid/test_sign.py`) confirms that the **vOmega ML-DSA-65 signing path** used in this implementation operates deterministically for the tested inputs. Deterministic ML-DSA signing is a **permitted mode** under FIPS 204; the test does not imply that all FIPS 204 ML-DSA signatures are deterministic, nor that all implementations of ML-DSA-65 produce identical signatures for identical inputs.

The test bounds the observation to: **this implementation, these inputs**. Extrapolation to other implementations, other inputs, or the standard itself is not made.

#### D7.4.5 Evidence

| Suite | Test ID | What is demonstrated |
|---|---|---|
| `test_bplus_e2e.py` | **H09** | TBS byte-identity after envelope round-trip |
| `test_bplus_e2e.py` | H03 | Hybrid verification VALID (both signatures) |
| `test_rust_parity.py` | R01 | Rust and Python verifiers both return VALID |
| `test_verify.py` | V01 | Both signatures valid |
| `test_sign.py` | **S11** | The vOmega signing path is deterministic for tested inputs |
| `test_e2e.py` | E01–E11 | End-to-end issue/sign/verify cycle |

**Reproduction:**

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ H09 + H03 — B+ round-trip and hybrid verification ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_e2e.py | grep "H03\|H09" && \
echo "═══ S11 — determinism (scoped) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_sign.py | grep "S11" && \
echo "═══ Rust ↔ Python verifier parity (13) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_rust_parity.py
```

**Expected:**

```
[PASS] H03 hybrid verify VALID (both sigs)
[PASS] H09 TBS byte-identical after envelope round-trip
[PASS] S11 ML-DSA-65 deterministic
...
TOTAL: 13 | PASS: 13 | FAIL: 0
```

---

### D7.5 Wire Encoding Does Not Redefine Cryptographic Identity

This is the negative statement of §D7.4. It is the central architectural commitment of Model B+.

#### D7.5.1 The commitment

> **TBS = `ADIE-SIG-V2\0` ‖ JCS(certificate_without_signatures)`.** The CBOR envelope does not participate in signature computation. The cryptographic identity of a certificate is defined by its TBS. B+ / DCP 2.1 are transport representations above that identity.

#### D7.5.2 What this rules out

- The envelope is **not** used as the signing input.
- The envelope's CBOR encoding is **not** part of the TBS.
- The envelope's label order, label values, or JCS byte strings do **not** affect the TBS.
- Changing the envelope's encoding (e.g., a future wire-format version) does **not** invalidate signatures computed over the certificate body.

#### D7.5.3 Why this matters — briefly

If the envelope were part of the signing input, every transport-layer decision (CBOR library, wire version, envelope label registry) would become a cryptographic decision, invalidating prior signatures whenever the transport changed. Model B+ avoids this by pinning cryptographic identity to the semantic certificate, not to the envelope that carries it.

The full architectural argument, including why Model A (COSE-native) was not selected, is in §D2.2.

#### D7.5.4 Cross-runtime TBS parity — bounded claim

The verification suites establish **parity of verification outcomes** across Rust and Python: for the same input, both verifiers return the same result (VALID or a specific rejection code). This is what `test_rust_parity.py` (13 executions) tests.

The verification suites **do not** establish direct byte-for-byte parity of the TBS corpus across implementations, because `test_rust_parity.py` compares **verification outcomes** (VALID/INVALID + code), not the TBS bytes themselves.

**What can be claimed with the current evidence:**

| Claim | Evidence |
|---|---|
| Rust and Python verifiers return the same outcome (VALID or specific code) for the same input | `test_rust_parity.py` — 13 executions |
| TBS bytes are byte-identical after a B+ round-trip (within one implementation) | `test_bplus_e2e.py` — H09 |
| Direct byte-for-byte parity of TBS across Rust and Python | **Not established by current tests** |

The last row is stated as a limit. A direct cross-runtime TBS-byte corpus would be needed to lift it; the current suite does not include one.

#### D7.5.5 The specific comparison

| Aspect | Model A (not selected) | Model B+ (selected) |
|---|---|---|
| Signing input | COSE `Sig_structure` | `ADIE-SIG-V2\0 ‖ JCS(cert)` |
| Envelope participates in signature? | Yes | No |
| Changing the transport invalidates signatures? | Yes | No |
| Phase 1 / Phase 2 signatures remain valid? | No (would require re-issuance) | Yes |

The right-hand column is what vOmega implements. The left-hand column is preserved as a possible future profile (Amendment-1 §A6), with a distinct domain tag.

#### D7.5.6 Evidence

| Evidence type | Source |
|---|---|
| Amendment-1 records the Model B+ decision | `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md` — SHA-256 `7cb607be...` |
| DECISION-0.3 records the Commander decision | `docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md` — SHA-256 `e9c0cd35...` |
| H09 confirms wire round-trip does not change the TBS bytes | `tests/vomega/b-plus/test_bplus_e2e.py` |
| H03 confirms hybrid verification is VALID | `tests/vomega/b-plus/test_bplus_e2e.py` |
| R01–R13 confirm Rust ↔ Python verifier outcome parity | `tests/vomega/hybrid/test_rust_parity.py` |

---

### D7.6 Evidence Summary

#### D7.6.1 Hybrid legacy suites — accounting

The **hybrid legacy suites** are five Python test modules. Their executions are:

| Suite | Executions |
|---|---|
| `tests/vomega/hybrid/test_tbs.py` | 12 |
| `tests/vomega/hybrid/test_sign.py` | 16 |
| `tests/vomega/hybrid/test_verify.py` | 20 |
| `tests/vomega/hybrid/test_e2e.py` | 11 |
| `tests/vomega/hybrid/test_rust_parity.py` | 13 |
| **Hybrid legacy subtotal** | **72** |

The subtotal **72** covers these five suites only. It does not include the B+ E2E suite.

#### D7.6.2 B+ E2E suite — separate, additional evidence

| Suite | Executions | Role |
|---|---|---|
| `tests/vomega/b-plus/test_bplus_e2e.py` | 10 | H09 (TBS byte-identity after envelope round-trip) and H10 (domain tag preserved through B+ round-trip) |

The B+ E2E suite is **not** added to the 72-execution subtotal. Its purpose is narrow: to provide H09 and H10 as direct evidence for §D7.2 and §D7.3. It is not part of the hybrid legacy count.

**Why the separation matters.** The 72-execution subtotal is the hybrid legacy count as defined by the five suites that were part of the Phase 2 hybrid work. Adding the B+ suite would conflate two distinct accounting categories and would risk double-counting if a later section (e.g., §D2) also cites the B+ suite.

#### D7.6.3 Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `protocol/hybrid/tbs.py` | `fe6e14d503c3f2e8d224ec058eb5744603778d5b7803fd8d6d6d612296c836e3` |
| `protocol/hybrid/verify.py` | `2d285fc50c43ae1c08bc7dd577657925cc08faf6deb9bbd1e3e8d5c6b48a7df5` |
| `protocol/hybrid/sign.py` | (see Appendix B) |
| `spec/HYBRID-CRYPTO-0.1.md` | (referenced; not modified by vOmega) |
| `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md` | `7cb607be51b7a5d1afbb78611d66b0db3ef3c8cdc30de15ee41b3a701e4762ab` |
| `docs/vomega/decisions/DECISION-0.3-COSE-ARCH.md` | `e9c0cd35637a21b5c5bc7268b084694805a79f4c55df06d9d65859f150a36412` |

#### D7.6.4 Reproduction — full D7 set

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ Hybrid legacy: tbs (12) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_tbs.py && \
echo "═══ Hybrid legacy: sign (16) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_sign.py && \
echo "═══ Hybrid legacy: verify (20) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_verify.py && \
echo "═══ Hybrid legacy: e2e (11) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_e2e.py && \
echo "═══ Hybrid legacy: rust parity (13) ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/hybrid/test_rust_parity.py && \
echo "═══ B+ E2E (10) — separate evidence ═══" && \
PYTHONPATH=src .venv/bin/python tests/vomega/b-plus/test_bplus_e2e.py
```

**Expected:** 12 + 16 + 20 + 11 + 13 = **72 hybrid legacy executions**, then B+ E2E **10 executions** (separate). All 0 failures.

**Commit.** `7683adb` (branch `vOmega`).

---

### D7.7 What D7 Does Not Claim

- D7 does not claim **formal verification**. No machine-checked proof of the TBS construction, the domain tag, or the phase-compatibility property exists.
- D7 does not claim **side-channel resistance or constant-time behavior**. No timing or cache analysis was performed on the signing or verification path.
- D7 does not claim **parity outside the tested corpus**. Cross-runtime verification-outcome parity is established only for the inputs in the test suites. Inputs outside those suites are not characterized.
- D7 does not claim that **all ML-DSA usage is deterministic**. S11's determinism observation is bounded to the vOmega signing path on the tested inputs (see §D7.4.4).
- D7 does not claim that the **envelope bytes** are the basis of cryptographic identity in vOmega. They are not. The basis is the TBS (§D7.5).
- D7 does not claim that the **72 hybrid legacy executions** (or the additional 10 B+ E2E executions) constitute a proof of security. They are evidence that specific properties hold for specific inputs.
- D7 does not claim that a future wire format cannot change the TBS. Amendment-1 §A6 reserves the COSE-native option; that option would use a **different** domain tag and would require re-issuance of all prior signatures. D7 documents the invariants of the **current** profile.
- D7 does not claim that preserving the TBS is sufficient for signature validity. Validity also requires the correct public key, the correct signature bytes, and a verifier that computes the same TBS. D7 addresses only the TBS side.
- D7 does not claim that `spec/HYBRID-CRYPTO-0.1.md` is unmodifiable. It is referenced, not frozen by vOmega. A future revision of that spec could change the TBS, in which case the domain tag would also change.
- D7 does not claim that the absence-of-envelope-participation is enforced by a cryptographic mechanism. It is enforced by construction: the envelope is produced **after** signing, from the certificate; the verifier recomputes the TBS from the certificate body, not from the envelope.
- D7 does not claim that the phase-compatibility claim was tested against certificates issued in Phase 1 or Phase 2 in a real deployment. It is tested against certificates constructed under the same TBS definition; the definition itself is what carries the compatibility claim.
- D7 does not claim that the **12-byte domain tag length** is optimal. It is the length of `"ADIE-SIG-V2\0"`. A future tag could be a different length. The 12-byte value is fixed for the current profile.

---

**End of D7.**


---

## D8. Security Analysis

**Part II, Section D8.**
**Scope:** The threat model vOmega addresses, the threats it does not address, the library trust boundaries, the class of library-default defects, and bounded fuzz behavior.
**Constraint:** D8 makes **no** claim of security proof, formal verification, or side-channel resistance. It documents what was tested, what was observed, and what remains out of scope.

---

### D8.1 Scope and Lineage

D8 has a narrower purpose than a conventional security chapter. It documents the following, and only the following:

1. **The threat model vOmega addresses** — a bounded list of threats that the architecture and its tests are intended to mitigate.
2. **The threats vOmega does not address** — an equally explicit list of out-of-scope threats.
3. **The library trust boundaries** — how the three CBOR codec libraries are treated (primitives, not oracles), and what that implies.
4. **A recurring class of library-default defects** — patterns observed during development (DEFECT-021, 025, 026, 027, 028, 039).
5. **Bounded fuzzing and classification behavior** — the scope and limits of the 10,000-mutation fuzz campaign (3A.6).
6. **Explicit non-claims** — what the reader must not infer from this section.

**What D8 is not.** D8 is not a security proof, not a penetration test report, not a cryptographic audit, and not a compliance statement. It is a bounded technical analysis with explicit limits.

**Upstream references.**

| Reference | Role |
|---|---|
| `docs/vomega/CONTINUITY.md` §55 | 3A.6 fuzzing narrative |
| `docs/vomega/DEFECTS-LOG.md` | Library-default defects and their closures |
| `spec/WIRE-FORMAT-0.2.md` §9 | The 14 `E_WIRE_*` rejection codes |
| §E6 of this document | What vOmega does not yet prove |
| §D7 of this document | Cryptographic identity invariants |

**Evidence-reference commit.** `7683adb` — reproducibility baseline. `origin/vOmega` is checked separately (see §E7.2).

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && \
git log --oneline -1 7683adb && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | \
grep -E "^## (DEFECT-021|DEFECT-025|DEFECT-026|DEFECT-027|DEFECT-028|DEFECT-039|DEFECT-040)"
```

---

### D8.2 Threat Model — What vOmega Addresses

This section lists the threats that the architecture and its tests are intended to **mitigate** (in the specific sense: reduce the probability that a specific class of failure occurs, given the specified inputs). It does not claim complete coverage.

#### D8.2.1 T-01 — Malformed or non-canonical wire input

**Threat.** A byte sequence that is syntactically valid CBOR but violates the DCP 2.1 profile — non-shortest integers, indefinite-length items, floats, tags, duplicate keys, trailing bytes, invalid UTF-8 — is processed as if it were canonical.

**Consequence if unmitigated.** Two readers may disagree on the semantic content of the same wire bytes, or a signature computed over canonical bytes may be verified against non-canonical bytes with the same semantic content.

**Mitigation.** The `rawcheck` gate rejects at the byte level before the semantic decoder runs. The 14 `E_WIRE_*` codes classify each rejection category. Rejection behavior is verified against the same corpus across Rust, Python, and JavaScript.

**Evidence.** `test_rawcheck.py` (44 executions), `test_rawcheck.mjs` (60), Rust `cbor::rawcheck::tests::*`, and the negative differential vectors N01–N18 (see §D3.7).

#### D8.2.2 T-02 — Cross-runtime semantic drift

**Threat.** The same wire bytes decode to different semantic values across Rust, Python, and JavaScript, or the same semantic value encodes to different bytes.

**Consequence if unmitigated.** A certificate signed by one runtime fails verification in another, or verifications succeed with divergent interpretations.

**Mitigation.** Three differential test pairs use the **44-vector core corpus**; the JavaScript-involving pairs additionally exercise **A01**, producing **45 executions** per such pair. Byte-level encode parity and semantic decode parity are checked. Rejection-code parity is checked at the specific code level.

**Evidence.** §D3.5, §D3.6, §D3.7 — 134 differential executions across three pairs (44 Python↔Rust + 45 Rust↔JS + 45 Python↔JS).

#### D8.2.3 T-03 — Signature downgrade attacks

**Threat.** An attacker presents a certificate with only one of the two required signatures (RS256 or ML-DSA-65) and expects the verifier to accept it.

**Consequence if unmitigated.** Silent fallback from hybrid to single-signature verification.

**Mitigation.** The hybrid policy requires both signatures by default. Missing signatures produce `E_SIGNATURE_HYBRID_MISSING`; a downgrade attempt produces `E_SIGNATURE_DOWNGRADE`. Silent fallback is forbidden.

**Evidence.** `test_verify.py` V04, V07, V14, V15, V19; `test_rust_parity.py` R05, R06, R07; `test_e2e_crypto_verification.py` C03, C05.

#### D8.2.4 T-04 — Wire-vs-identity confusion

**Threat.** A signing or verification path accidentally computes the cryptographic input from the CBOR envelope rather than from the semantic certificate, coupling cryptographic identity to the wire format.

**Consequence if unmitigated.** Signatures become dependent on envelope bytes; any transport change invalidates prior signatures; portability is lost.

**Mitigation.** TBS is computed from the semantic certificate (via JCS), not from the envelope. See §D7.5. H09 confirms the TBS is byte-identical after a full envelope round-trip.

**Evidence.** `test_bplus_e2e.py` H09; §D7.5.

#### D8.2.5 T-05 — Governance bypass (evidence-as-authority)

**Threat.** A code path treats an evidence object as if it were an authority, or infers authorization from the presence of evidence.

**Consequence if unmitigated.** Any party who can produce evidence can authorize decisions.

**Mitigation.** `DecisionEvidence` carries no `authority_id`, no `authorization_status`, and no `authorized` attribute. The legacy adapter does not fabricate an `Authority`. The canonical `DecisionContract` rejects `authorization_status=AUTHORIZED` when the lifecycle has not reached `AUTHORIZED`.

**Evidence.** `test_governance_anti_bypass.py` X01–X19; `test_canonical_contract.py` D05–D08.

#### D8.2.6 T-06 — Trust-status rewrite

**Threat.** A later revocation silently changes the historical record of a decision, or a trust query returns the current status when a historical status was asked for.

**Consequence if unmitigated.** The audit trail loses its integrity; past decisions appear to have been made under a status that never applied.

**Mitigation.** The trust resolver exposes two interfaces — `resolve_at(T)` and `resolve_current()` — with distinct semantics. Historical queries are stable as new assertions are appended. A decision records `authority_status_at_authorization`, which is not overwritten.

**Evidence.** `test_temporal_replay.py` (41 executions), `test_decision_trust_integration.py` (13), `test_governed_initial_state.py` (18).

#### D8.2.7 T-07 — Crypto bypass in the end-to-end path

**Threat.** The end-to-end path accepts a certificate without verifying its signatures.

**Consequence if unmitigated.** A structurally valid certificate with garbage signatures reaches an accepted decision.

**Mitigation.** Stage 1.5 of the end-to-end path performs cryptographic verification (added in 3D-R1, DEFECT-044). Failures produce `REJECTED_CRYPTO` with a specific reason code.

**Evidence.** `test_e2e_crypto_verification.py` (12 executions, including C10 which confirms crypto and trust layers remain independent).

#### D8.2.8 T-08 — Library-default permissiveness

**Threat.** A CBOR codec library, by default, accepts inputs that the ADIE profile forbids — semantic tags, indefinite-length items, floats, non-shortest integers, duplicate keys. If the library's default behavior is taken as the protocol behavior, the profile degrades silently.

**Consequence if unmitigated.** The wire profile's guarantees are weakened without any visible change in the code.

**Mitigation.** All three codec paths apply explicit decoder/profile-facing controls appropriate to their runtime (for example: `allow_indefinite=False` in Python's `cbor2`; `allow_duplicate_keys=False` where applicable; `tag_hook=raise` in Python as defense-in-depth). `rawcheck` remains **authoritative for wire-level rules** and runs before semantic decoding. Library behavior is not treated as protocol behavior. The precise configuration for each runtime is enumerated in `CBOR-LIB-EVAL-001/002/003` and in the respective decoder modules.

**Evidence.** `CBOR-LIB-EVAL-001/002/003`; §D8.4 below; the defect class in §D8.5.

#### D8.2.9 What the threat model does not include

This is not a complete threat model in the security-engineering sense. It lists **eight** threats that the architecture is designed to mitigate. It does not claim that any of them is fully mitigated, nor that the list is exhaustive. Additional threats are addressed in §D8.3 (out-of-scope threats) and §D8.7 (non-claims).

---

### D8.3 Threat Model — What vOmega Does Not Address

The following threats are explicitly **out of scope** for the current vOmega implementation. Listing them here is part of the discipline: the document does not claim coverage it does not have.

#### D8.3.1 Side-channel threats

No constant-time analysis, timing analysis, cache analysis, or power analysis has been performed on any layer. The document makes no claim that the wire encoder, decoder, envelope builder, governance layer, trust resolver, or end-to-end path is safe against side-channel observation.

#### D8.3.2 Formal-verification threats

No machine-checked proof of correctness, determinism, or invariant preservation exists for any layer. The evidence base is empirical — test executions and differential comparisons — not deductive.

#### D8.3.3 Runtime-compromise threats

If the process executing the vOmega code is compromised (arbitrary code execution, memory corruption, hostile injection), vOmega's guarantees do not survive. No isolation mechanism, sandboxing, or hardening against a compromised runtime is claimed.

#### D8.3.4 Authority-compromise threats

If the private keys corresponding to an `Authority` are compromised, an attacker can authorize decisions. vOmega does not detect or mitigate this; it presumes the authority's keys are held by the legitimate party.

#### D8.3.5 Trust-root-compromise threats

The trust model operates on authorities provided as inputs. If those inputs are the result of a compromised trust-bootstrap step, the trust layer's determinations are based on forged inputs. vOmega does not define a trust root; it consumes the authorities it is given (see §E6.5, F-04/F-05).

#### D8.3.6 Network-layer threats

vOmega operates on byte sequences. Attacks at the network layer (interception, replay at the protocol level, TCP-level manipulation, TLS downgrade) are outside the scope of the wire profile.

#### D8.3.7 Application-layer DoS threats

The document does not claim bounded CPU or memory consumption under adversarial inputs at the application layer. The fuzz campaign (§D8.6) exercises 10,000 mutations but does not characterize worst-case resource consumption or DoS resistance.

The trust store's integrity gate runs `verify_integrity()` on every resolution call and is O(N) in the size of the store. This is documented as a known scaling limitation (F-08, §D11). No mitigation is claimed.

#### D8.3.8 Multi-tenant isolation

No mechanism is defined for isolating authorities, trust stores, or decision artifacts across tenants. Multi-tenant deployment would require additional design (§E6.7).

#### D8.3.9 Compromised or malicious library

The three CBOR libraries (`ciborium`, `cbor2`, `cbor@9`) are treated as primitives. The document does not claim they are free of vulnerabilities, backdoors, or future-introduced defects. They are not audited by this project. If a library is compromised, the ADIE profile layer's guarantees may be weakened.

#### D8.3.10 Hostile input outside the tested corpus

Rejection behavior is validated for the enumerated negative vectors and the fuzz corpus. Inputs outside those corpora are not characterized. See §E6.8.

#### D8.3.11 Compliance and certification

No regulatory compliance (Common Criteria, ISO 27001, FIPS 140-3) is claimed. ACVP vector execution demonstrates conformance to published test vectors; it is not equivalent to a certification. See §E6.4.

---

### D8.4 Library Trust Boundaries

vOmega uses three CBOR codec libraries. Their roles and trust boundaries are as follows.

#### D8.4.1 The three libraries

| Layer | Library | Version | License | Role |
|---|---|---|---|---|
| Rust | `ciborium` | `=0.2.2` | Apache-2.0 | Codec primitive for the Rust reference implementation. |
| Python | `cbor2` | `==6.1.5` | MIT | Codec primitive for the Python adapter. |
| JavaScript | `cbor` | `9.0.2` | MIT | Codec primitive for the JavaScript adapter. |

Rationales for each selection are recorded in `CBOR-LIB-EVAL-001` (ciborium), `CBOR-LIB-EVAL-002` (cbor2), and `CBOR-LIB-EVAL-003` (cbor@9).

#### D8.4.2 What "primitive" means here

Each library is treated as a **codec primitive** — a source of `encode` and `decode` operations — not as an **oracle** for the ADIE profile. The profile is defined by the frozen specification and enforced by the ADIE-owned layers:

- `rawcheck` (byte-level authority) — runs before the codec.
- `profile` (semantic authority) — runs after the codec.
- The encoder sorts map keys explicitly before calling the codec.

A change to a library's default behavior does not change the profile. If a library's behavior is incompatible with the profile, the ADIE layer compensates.

#### D8.4.3 Library defaults — the baseline

All three libraries ship permissive defaults. Their defaults accept inputs that DCP 2.1 forbids. This is not a criticism of the libraries; it is a property of general-purpose CBOR codecs, which serve a broader community than ADIE.

| Library | Non-shortest int | Indefinite items | Floats | Tags | Duplicate keys | Trailing bytes |
|---|---|---|---|---|---|---|
| `ciborium` 0.2.2 | Accepted | Accepted | Accepted | Accepted | Accepted | Accepted |
| `cbor2` 6.1.5 | Accepted | Accepted | Accepted | **Interpreted** | Accepted | Accepted |
| `cbor` 9.0.2 | Accepted | Accepted | Accepted | **Interpreted** | Accepted | **Rejected** |

"Interpreted" for tags means the library converts a tagged value to a native type (e.g., a `datetime` in Python) rather than returning a `Tagged` wrapper. This is the DEFECT-021 pattern.

#### D8.4.4 The compensating layers

Every default listed above is overridden at the ADIE layer:

| Default behavior | Compensated by |
|---|---|
| Non-shortest integers accepted | `rawcheck` rejects non-shortest encodings |
| Indefinite items accepted | `rawcheck` rejects; codec configured with `allow_indefinite=False` |
| Floats accepted | `rawcheck` rejects float major type |
| Tags interpreted | `rawcheck` rejects major type 6; `tag_hook=raise` as defense-in-depth |
| Duplicate keys accepted | `rawcheck` rejects; codec configured with `allow_duplicate_keys=False` |
| Trailing bytes accepted (Rust, Python) | `rawcheck` verifies full-buffer consumption |

#### D8.4.5 What is not claimed about the libraries

- The libraries are **not** audited by this project.
- The libraries are **not** claimed to be free of vulnerabilities.
- The libraries are **not** claimed to be equivalent to one another; their behaviors are documented and compensated, not merged.
- A library upgrade is a potential source of behavior change; the differential suites are intended to detect drift, not to prevent it.

#### D8.4.6 Evidence

| Evidence | Source |
|---|---|
| ciborium probe results | `CBOR-LIB-EVAL-001` in `DEFECTS-LOG.md` |
| cbor2 probe results | `CBOR-LIB-EVAL-002` |
| cbor@9 probe results | `CBOR-LIB-EVAL-003` |
| Codec configuration | `protocol/wire/decoder.py`, `js/wire/decoder.mjs`, `rust/adie-primitives/src/cbor/decoder.rs` |

---

### D8.5 Library-Default Defects as a Class

The following closed defects are included because they exposed differences between library behavior, runtime behavior, process behavior, and ADIE protocol assumptions.

#### D8.5.1 The observed defects

| ID | Library | Pattern | Closure |
|---|---|---|---|
| DEFECT-021 | `cbor2` | Silently interprets known semantic tags as native types | `rawcheck` rejects major type 6 at byte level; `tag_hook` defense-in-depth |
| DEFECT-025 | `cbor` (npm) | CommonJS module — named exports not visible to ESM `import * as` | Use `import CBOR from 'cbor'` (default import) |
| DEFECT-026 | `cbor` (npm) | Profile coerced non-integral `Number` values without rejection | Explicit type check; `1.5` now throws `Float_` |
| DEFECT-027 | `rawcheck` | Duplicate keys not detected at wire level (relied on codec) | `rawcheck` now walks maps and rejects duplicates |
| DEFECT-028 | `cbor` (npm) | Mixed output — CBOR maps decoded as JS `Map` in some cases, plain objects in others | Decoder normalizes; profile rejects non-`Map` inputs |
| DEFECT-039 | `cbor` (npm) | `walkTag` skipped shortest-form check on tag number | Enforce shortest-form on tag number before `TagErr` |
| DEFECT-040 | (process) | Commit message claimed 0/10k mismatch while 1/10k existed | Corrected in subsequent commit |

#### D8.5.2 The common pattern

Most entries above share a broader pattern:

> A library default, interface behavior, or runtime type behavior differed from an ADIE protocol assumption, and the discrepancy became visible only when exercised by explicit tests.

The instances fall into distinct sub-classes:

- **Rejection-permissiveness** — the library accepts input that the ADIE profile forbids. Examples: DEFECT-021, DEFECT-026, DEFECT-027, DEFECT-039.
- **Interface shape** — the library's module structure or API does not expose the operations the ADIE layer expects. Example: DEFECT-025 (CommonJS named-export visibility).
- **Runtime type normalization** — the library returns a runtime-native type that the ADIE profile did not anticipate. Example: DEFECT-028 (mixed `Map` / plain object output).

**DEFECT-040 is a process/evidence-recording defect** rather than a library-default defect. It is included only because it affected the accuracy of the recorded fuzzing result (see §D8.6). It is not an example of a library-vs-profile divergence.

#### D8.5.3 The mitigation as a class

The response is architectural, not case-by-case:

1. **`rawcheck`** runs before the codec and enforces byte-level rules that do not depend on the codec's defaults.
2. **The profile layer** runs after the codec and enforces semantic rules that do not depend on the codec's type model.
3. **Cross-runtime differential tests** drive the same input through three implementations and compare outcomes. A library-default divergence that affects one runtime is detected as a parity failure.

No single library's default is trusted as the protocol default.

#### D8.5.4 Evidence

| Evidence | Source |
|---|---|
| Per-defect records | `DEFECTS-LOG.md` — DEFECT-021, 025, 026, 027, 028, 039, 040 |
| `rawcheck` implementation | `protocol/wire/rawcheck.py`, `js/wire/rawcheck.mjs`, `rust/adie-primitives/src/cbor/rawcheck.rs` |
| Cross-runtime differential | §D3.4 (three pairs, 134 executions) |

---

### D8.6 Bounded Fuzzing and Classification Behavior

#### D8.6.1 The 3A.6 fuzzing campaign

Phase 3A.6 introduced a differential fuzzing campaign that mutated a base corpus and ran every mutant through all three implementations.

| Property | Value |
|---|---|
| Number of mutations | **10,000** |
| Base corpus | ADIE certificates + wire vectors |
| Runtimes exercised | Rust, Python, JavaScript |
| Comparison axes | acceptance decision; rejection code |
| Run #1 result | 1/10k rejection-code mismatch (initially misreported as 0/10k) |
| DEFECT-039 fix | Applied to JavaScript `walkTag` |
| Run #2 result | **0/10k acceptance mismatches; 0/10k rejection-code mismatches** |
| Recording defect | DEFECT-040 (the run-#1 misreport is documented) |

#### D8.6.2 What this shows

For the tested mutations, no cross-runtime divergence in acceptance or rejection-code classification was observed on run #2. The single divergence on run #1 was diagnosed and corrected.

#### D8.6.3 What this does not show

- It does not show that no divergence exists outside the tested mutation corpus.
- It does not show bounded CPU or memory consumption — the campaign measured **classification**, not resource usage.
- It does not show resistance to a targeted adversary who knows the profile and crafts inputs specifically.
- It does not show DoS resistance.
- It does not show that the libraries themselves are robust under all inputs; only that the profile layer's acceptance/rejection decisions are consistent across runtimes for the tested mutants.

#### D8.6.4 Evidence

| Evidence | Source |
|---|---|
| Run #2 result | `CONTINUITY.md` §55; commit `3fbc921` |
| Run #1 correction | DEFECT-040 in `DEFECTS-LOG.md` |
| The fix | DEFECT-039 in `DEFECTS-LOG.md` |

**Reproduction.** The fuzzing campaign is not part of the routine test suite; its results are recorded in the continuity log and defect log. A re-run is outside the scope of this document.

---

### D8.7 What D8 Does Not Claim

- D8 does not claim that vOmega is secure.
- D8 does not claim that the eight threats in §D8.2 are fully mitigated. It lists the architecture's responses and the tests that exercise them.
- D8 does not claim that the list in §D8.3 is complete. Additional threats may exist outside the enumerated set.
- D8 does not claim that any library used is vulnerability-free or audited.
- D8 does not claim that the 10,000-mutation fuzz campaign is representative of any real-world input distribution. Its mutations are structured, not sampled from a population.
- D8 does not claim bounded resource behavior under adversarial input.
- D8 does not claim constant-time or side-channel resistance in any layer.
- D8 does not claim formal verification of any invariant.
- D8 does not claim production hardening. The document treats production deployment as out of scope (§E6.1).
- D8 does not claim that the DEFECT entries cited in §D8.5 constitute a complete list of library-default defects. They are the ones that were observed and closed during development.
- D8 does not claim that the O(N) integrity gate is safe under adversarial store sizes. The scaling behavior is documented (F-08) and not mitigated.
- D8 does not claim that the ADIE-owned compensating layers themselves are free of defects. They are subject to the same testing discipline as everything else in vOmega.

---

**End of D8.**

## D9. Defect History — All 44 DEFECTs

**Part II, Section D9.**
**Status:** Draft 03 — applying Commander's three precision corrections to Draft 01, plus the RISK-count correction identified during evidence verification.
**Scope:** the complete defect record from Phases 1 through 3D-R1: 46 top-level DEFECT headers (44 unique numbers), 3 library-evaluation entries, 3 GAP entries, and 4 RISK headers (3 unique numbers).
**Constraint:** D9 records defect history. It does not claim that the record is exhaustive of all defects that occurred during development; it records the defects that were logged.

---

### D9.1 Scope and Lineage

D9 documents the defect record that has accumulated across the vOmega work. It has a narrower purpose than a conventional "lessons learned" section. It documents:

1. **The numbering irregularities** — so a reader can reconcile the 46 DEFECT headers with the 44 unique DEFECT numbers, and the 4 RISK headers with the 3 unique RISK numbers.
2. **A categorical classification** — code, architecture, dependency, test, process, spec.
3. **The five architecture-critical defects** — the ones that changed the design, not just the code.
4. **The three library-evaluation entries** — CBOR-LIB-EVAL-001/002/003.
5. **The open GAPs and RISK entries** — separated from DEFECTs to avoid conflation.
6. **The full header index** — as an index, with pointers to `DEFECTS-LOG.md` for detail.

**What D9 is not.** D9 is not a complete reproduction of `DEFECTS-LOG.md`. It is an index and a classification. The full text of each defect — root cause, fix, lesson, commit references — is in `docs/vomega/DEFECTS-LOG.md` and is not duplicated here.

**Record inventory.** D9 references the following records in `DEFECTS-LOG.md`:

- **46** top-level `## DEFECT-` headers, corresponding to **44 unique DEFECT numbers**.
- **3** `CBOR-LIB-EVAL-` entries.
- **3** `GAP-` entries.
- **4** `RISK-` headers, corresponding to **3 unique RISK numbers** (2 archived, 1 active; RISK-3.1 appears twice — original + reclassification).

**Source of truth.** `docs/vomega/DEFECTS-LOG.md`.

**Evidence-reference commit.** `7683adb` (reproducibility baseline).

**Verification:**

```bash
cd ~/Desktop/EnterpriseGuard && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -cE "^## DEFECT-" && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -E "^## (DEFECT|CBOR-LIB|GAP|RISK)" | head -60
```

---

### D9.2 The Defect Record — Numbering Irregularities

The defect record in `DEFECTS-LOG.md` contains **46 top-level headers** matching `^## DEFECT-`. These correspond to **44 unique DEFECT numbers**. The difference is explained by three irregularities.

#### D9.2.1 Unassigned numbers

Two numbers in the sequence were never assigned:

| Number | Status |
|---|---|
| `DEFECT-005` | Never assigned. No header, no reference. |
| `DEFECT-030` | Never assigned. No header, no reference. |

This is not a defect; it is a documented gap in the numbering sequence. The numbers were reserved and then not used.

#### D9.2.2 A duplicated header

`DEFECT-017` appears **twice** in the log:

- The first entry (line 494) is the original defect: *"Rust adie-hybrid-verify did not check key_id before signature."*
- The second entry (line 554) is an **architectural classification** entry, recorded per Commander order on 2026-10-07. It re-examines the original defect in light of the RISK-3.1 reclassification.

The two entries share a number but serve different documentary purposes. Neither is a duplicate defect; the number is reused because the second entry is explicitly a re-classification of the first, not a new defect.

#### D9.2.3 A suffix variant

`DEFECT-029-WASM` is a **suffix variant** of `DEFECT-029`. It is not a separate number. It records a WASM-specific manifestation of the same underlying invariant (lossless integer boundary) that DEFECT-029 addressed for the JSON boundary.

#### D9.2.4 The counts, stated precisely

**DEFECT counts:**

| Metric | Value |
|---|---|
| Top-level `## DEFECT-` headers | 46 |
| Unique DEFECT numbers (base `NNN`) | 44 |
| Suffix variants (`NNN-XXX`) | 1 (`DEFECT-029-WASM`) |
| Duplicate headers | 1 (`DEFECT-017` architectural classification) |
| Unassigned numbers | 2 (`DEFECT-005`, `DEFECT-030`) |

**Formula:** 44 base numbers + 1 duplicate + 1 suffix = **46 headers**.

There are **44 unique base DEFECT numbers** and **45 unique DEFECT identifiers** when the `DEFECT-029-WASM` suffix variant is counted as a distinct identifier.

**RISK counts:**

| Metric | Value |
|---|---|
| Top-level `## RISK-` headers | 4 |
| Unique RISK numbers | 3 (`RISK-3.1`, `RISK-3.2`, `RISK-3.3`) |
| Duplicate headers | 1 (`RISK-3.1 RECLASSIFICATION`, Commander order 2026-10-07) |
| Active | 1 (`RISK-3.3`) |
| Archived | 2 (`RISK-3.1`, `RISK-3.2`) |

**Formula:** 3 unique RISK numbers + 1 duplicate header = **4 headers**.

---

### D9.3 Classification of Defects

Every logged DEFECT is classified under **one or more** of six categories, based on its dominant nature and recorded facets. The classification is preserved as recorded.

#### D9.3.1 The six categories

| Category | Meaning |
|---|---|
| **code** | A behavior bug in a specific code path. |
| **architecture** | A design correction that changes structural assumptions, not just code. |
| **dependency** | A library, tool, or external dependency behaves differently than assumed. |
| **test** | Test infrastructure, harness, or fixture defect. |
| **process** | Documentation, tooling, or workflow defect. |
| **spec** | Specification text is inaccurate or incomplete. |

A defect may carry more than one category label. For example, DEFECT-021 is classified as both *dependency* (the library's behavior differed from the assumption) and *architecture* (the correction introduced a new gate). The multi-label facet is intentional: it reflects the fact that a defect can occupy more than one plane of the system.

#### D9.3.2 Distribution (approximate)

| Category | Approximate count | Examples |
|---|---|---|
| code | ~15 | DEFECT-002, 004, 006, 011, 012, 018, 023, 026, 027, 028, 034, 035, 038, 039 |
| architecture | ~5 | DEFECT-021, 026, 027, 028, 036 |
| dependency | ~7 | DEFECT-010, 015, 016, 021, 025, 031, 032 |
| test | ~8 | DEFECT-001, 003, 014, 019, 022, 037, 041, 042 |
| process | ~6 | DEFECT-007, 008, 020, 024, 033, 040 |
| spec | ~2 | DEFECT-009, 013 |

The approximate counts in this table are **not disjoint**: a defect with two facets appears in two rows. The sum of the counts is greater than 44. The table is provided for orientation only; it is not an accounting total.

#### D9.3.3 The classification is not the log's schema

`DEFECTS-LOG.md` uses a **richer schema** for each entry, with fields including:

- `date`
- `commit_found`
- `commit_fixed`
- `suite`
- `test_id`
- `test_name`
- `category/classification facets` (the six categories above)
- `root_cause`
- `fix`
- `lesson`

D9.3's classification is a summarization of the `category/classification facets` field; it is not a substitute for the full record.

---

### D9.4 Architecture-Critical Defects

Five defects are marked as **architecture-critical**: they changed structural assumptions in the design, not just behavior in a specific code path. They are listed here with the change they triggered.

#### D9.4.1 DEFECT-021 — cbor2 silently interprets known semantic tags

**Category:** dependency, architecture.
**Discovery.** During the 3A.3 Python adapter work, a probe revealed that `cbor2` 6.1.5 by default interprets well-known CBOR tags (e.g., tag 0 → `datetime`, tag 1 → `datetime`) as native Python types. This means the codec conceals tag information rather than surfacing it.

**Architectural change.** The `rawcheck` gate was introduced as a **byte-level authority** that runs *before* the codec. `rawcheck` inspects the raw bytes and rejects major type 6 (tags) regardless of the codec's behavior. The codec's `tag_hook=raise` is retained only as defense-in-depth.

**Why architecture, not code.** The correction is not "patch the decoder." It is "introduce a byte-level gate that is authoritative for wire rules, and stop relying on the codec for those rules." The same gate protects all three implementations.

**Cross-reference.** §D1.6, §D8.5.

#### D9.4.2 DEFECT-026 — JS profile coercion of non-integral Number values

**Category:** dependency, architecture.
**Discovery.** During the 3A.4A JavaScript adapter work, a probe revealed that `cbor@9` accepted non-integral `Number` values (`1.5`) and passed them to the profile layer, where the initial profile did not reject them.

**Architectural change.** The JavaScript `profile.mjs` layer was extended to explicitly reject non-integral `Number` values before type classification. The check is at the profile layer, not the decoder, because the decoder's type model is not authoritative.

**Why architecture, not code.** The correction establishes that the profile layer — not the codec — is responsible for enforcing the DCP 2.1 type discipline. The codec is treated as a transport, not as a validator.

**Cross-reference.** §D8.5.2 (rejection-permissiveness sub-class).

#### D9.4.3 DEFECT-027 — rawcheck must reject duplicate keys at wire level

**Category:** architecture.
**Discovery.** Duplicate keys were being detected by the codec (when the codec was configured to reject them) rather than by the wire-level gate. This made the rejection behavior dependent on the codec's configuration and version.

**Architectural change.** `rawcheck` was extended to walk map structures at the byte level and reject duplicates before decoding. The codec's duplicate-rejection mode is retained as defense-in-depth, but the wire gate is now authoritative.

**Why architecture, not code.** It relocates the authority for a wire rule from a library configuration to the ADIE-owned gate. Library upgrades no longer silently change this behavior.

**Cross-reference.** §D8.4.4.

#### D9.4.4 DEFECT-028 — cbor@9 mixed Map/object output

**Category:** dependency, architecture.
**Discovery.** During the JavaScript work, the `cbor@9` decoder was found to return CBOR maps as JavaScript `Map` objects in some cases and as plain objects in others, depending on options and input shape.

**Architectural change.** The JavaScript decoder normalizes map output to a single representation. The profile layer accepts only that representation; any other map-like shape is rejected.

**Why architecture, not code.** The correction establishes a **canonical in-memory representation** for CBOR maps on the JavaScript side — parallel to the Python `AdieValue` class hierarchy and the Rust `AdieValue` enum. Without this, semantic decode parity across runtimes is not well-defined.

**Cross-reference.** §D3.6, §D8.5.2 (runtime type normalization sub-class).

#### D9.4.5 DEFECT-036 — Cross-runtime rejection-code divergence on nested duplicate keys

**Category:** architecture.
**Discovery.** During the 3A.6 fuzz campaign, a mutant containing a nested duplicate-key structure produced different rejection codes across Rust, Python, and JavaScript. The divergence was at the **classification priority** level: which of two applicable rejection codes should be returned.

**Architectural change.** A **classification priority** was defined for rejection codes and enforced consistently across all three implementations. The priority is documented in `WIRE-FORMAT-0.2.md` §9 and is exercised by the differential suites.

**Why architecture, not code.** The correction establishes a *priority order* where none existed. Without it, the three implementations could each choose "reasonable" but different codes for the same malformed input, breaking rejection-code parity.

**Cross-reference.** §D3.7.4 (classification priority).

---

### D9.5 Library-Evaluation Entries

Three entries in `DEFECTS-LOG.md` are **not DEFECTs** in the strict sense. They are **library-evaluation records** — documented comparisons of CBOR libraries with a recorded selection rationale.

#### D9.5.1 CBOR-LIB-EVAL-001 — ciborium 0.2.2 (Rust)

Selected for the Rust reference implementation. Rationale: mature codec, `Value` model available, Apache-2.0 license, MSRV 1.58. The log records the probe results on the library's default behavior (see §D8.4.3).

#### D9.5.2 CBOR-LIB-EVAL-002 — cbor2 6.1.5 (Python)

Selected for the Python adapter. Rationale: pinned version, provides both encode and decode, exposes strict-mode flags (`allow_indefinite`, `allow_duplicate_keys`, `max_depth`, `tag_hook`). The log records the same probe pattern.

#### D9.5.3 CBOR-LIB-EVAL-003 — cbor 9.0.2 (JavaScript)

Selected for the JavaScript adapter. Rationale: last major line with the classic helper API (`encode`, `encodeCanonical`, `decodeFirstSync`). The 10.x line rewrote the API to low-level push/pull primitives. The CommonJS-vs-ESM interop issue is recorded as DEFECT-025.

**Note on the number of entries.** There are exactly **three** CBOR-LIB-EVAL entries. They are separate from DEFECT numbering and are not counted in the 44/46 figures.

---

### D9.6 Open GAPs

Three GAP entries are recorded. GAPs are documented limitations that are **not** defects — the behavior is understood and accepted, or the gap is reserved for future work.

#### D9.6.1 GAP-8 — Rust ML-DSA sigGen not covered by ACVP KAT

**Status:** Open.
**Nature.** The ACVP KAT vectors used by the project cover ML-DSA-65 key generation and verification, but not the deterministic signature-generation path in Rust. The Rust signing path is exercised by project tests, but not against external NIST vectors.

**Documented as:** GAP, not a defect. The signing path works; its coverage by external vectors is incomplete.

#### D9.6.2 GAP-9 — ML-DSA-65 key_id uses raw pk bytes, not SPKI DER

**Status:** Open.
**Nature.** The ML-DSA-65 `key_id` in a hybrid certificate is derived from the raw public-key bytes, not from an SPKI-DER encoding. This is a documented design choice, not a defect.

**Documented as:** GAP, not a defect. The choice is consistent across phases; it is recorded so that a future profile decision (e.g., a switch to SPKI-DER) is visible as a decision rather than as a silent change.

#### D9.6.3 GAP-3.4B-01 — wasm-bindgen nodejs CWD-relative wasm path

**Status:** Documented by design.
**Nature.** The `wasm-bindgen`-generated Node.js bindings load the `.wasm` file relative to the current working directory. This is the default behavior of `wasm-bindgen` for the `nodejs` target and is not modified.

**Documented as:** GAP by design. Callers must invoke the WASM module from a working directory where the `.wasm` file is reachable.

---

### D9.7 RISK Entries

RISK entries record tracked risks. There are **4 RISK headers** in `DEFECTS-LOG.md`, corresponding to **3 unique RISK numbers**. One header is a reclassification entry (RISK-3.1).

#### D9.7.1 RISK-3.1 — sad-rsa fork tracks unstable rsa 0.10.x API line

**Status:** Archived.
**History.** RISK-3.1 was originally logged at line 363 with the status *"not applicable"*. On 2026-10-07, per Commander order, a **reclassification entry** was added at line 527 with the new status:

> BOUNDED EXPOSURE / NOT USED FOR PRIVATE-KEY OPERATIONS IN CURRENT VERIFIER PATH.

The reclassification was triggered by DEFECT-015 (`sad-rsa` 0.10.2 build failure) which caused the project to fall back to `rsa` 0.9.6. The two headers (original + reclassification) share the RISK-3.1 number. This is the same documentary pattern as DEFECT-017 (§D9.2.2).

#### D9.7.2 RISK-3.2 — sad-rsa dependency surface (~46 crates)

**Status:** Archived.
**History.** RISK-3.2 was logged at line 386. It was resolved together with RISK-3.1 when the `rsa` 0.9.6 fallback became permanent.

#### D9.7.3 RISK-3.3 — Build environment is space-constrained

**Status:** **ACTIVE.**
**History.** RISK-3.3 was logged at line 699 in Phase 3A.2. The observation: development disk is 38 GB with 36 GB used at peak, leaving ~450 MB free; one `cargo build --release` required ~240 MB.

The risk is monitored by recording disk state before and after each material block of work. As of the evidence-reference commit, disk usage is at 86% of the home partition.

**Cross-reference.** §E7.1, and any section that reports disk state.

---

### D9.8 The Full Header Index

The following is the complete index of the `## DEFECT-`, `## CBOR-LIB-EVAL-`, and `## GAP-` headers in `DEFECTS-LOG.md`. RISK entries are indexed separately in §D9.7. Each entry is a one-line summary taken from the header itself. Detail (root cause, fix, lesson, commits) is in `DEFECTS-LOG.md`.

#### D9.8.1 DEFECT headers (46 total, including 017 duplicate and 029-WASM suffix)

| Header | Summary |
|---|---|
| DEFECT-001 | M19 was a duplicate of M06 |
| DEFECT-002 | A25: EQ did not enforce type check |
| DEFECT-003 | Block B test 4 over-specified code |
| DEFECT-004 | JS verify.mjs: ClaimRoot field mismatch + message format |
| DEFECT-006 | Rust verifier binding error codes use hyphens |
| DEFECT-007 | Premature GAP-5 commitment based on partial information |
| DEFECT-008 | Repeated GAP-N before exhausting paths |
| DEFECT-009 | Placeholder contamination in spec §12.3 |
| DEFECT-010 | pqcrypto cannot participate in deterministic ML-DSA testing |
| DEFECT-011 | mldsa wrapper assumed ctx=b"" |
| DEFECT-012 | RustCrypto decode was stricter than FIPS 204.Verify semantics |
| DEFECT-013 | Spec claimed 13-byte domain tag; actual is 11 chars + NUL = 12 bytes |
| DEFECT-014 | Test count conflation across phases |
| DEFECT-015 | sad-rsa 0.10.2 fails to build; rsa 0.9.6 selected as fallback |
| DEFECT-016 | rsa 0.9.6 requires explicit sha2 feature |
| DEFECT-017 | Rust adie-hybrid-verify did not check key_id before signature |
| DEFECT-017 | ARCHITECTURAL CLASSIFICATION (Commander order, 2026-10-07) |
| DEFECT-018 | ciborium::Value is `#[non_exhaustive]` |
| DEFECT-019 | Test byte count error in rawcheck::valid_nested |
| DEFECT-020 | account.py summary anchor mismatch |
| DEFECT-021 | cbor2 silently interprets known semantic tags |
| DEFECT-022 | Test harness ROOT path off by one |
| DEFECT-023 | cbor2 raises CBORDecodeError for duplicate keys |
| DEFECT-024 | Hand-written JSON vector file had invalid syntax |
| DEFECT-025 | CommonJS interop: named exports not visible in ESM |
| DEFECT-026 | JS profile coercion of non-integral Number values |
| DEFECT-027 | rawcheck must reject duplicate keys at wire level |
| DEFECT-028 | cbor@9 mixed Map/object output for maps |
| DEFECT-029 | JSON Number precision boundary at u64 range |
| DEFECT-029-WASM | Lossless Integer Boundary Invariant (WASM ABI) |
| DEFECT-031 | getrandom wasm32 backend requires explicit opt-in |
| DEFECT-032 | wasm-bindgen nodejs output under ESM parent |
| DEFECT-033 | Build artifacts and toolchain binaries tracked |
| DEFECT-034 | jcs::canonical_bytes returns Result, not Vec |
| DEFECT-035 | CborError::Malformed is a struct variant, not tuple |
| DEFECT-036 | Cross-runtime rejection-code divergence on nested duplicate keys |
| DEFECT-037 | Patch application silently failed to insert helper |
| DEFECT-038 | Python rawcheck missing inner duplicate-key detection |
| DEFECT-039 | JS walkTag skipped shortest-form check on tag number |
| DEFECT-040 | Commit message claimed 0/10k mismatch while 1/10k existed |
| DEFECT-041 | pytest --collect-only breaks on test_bplus_e2e.py |
| DEFECT-042 | Test harness time-semantics error in H13 |
| DEFECT-043 | Missing governed initial ACTIVE state for trust resolver |
| DEFECT-044 | E2E did not perform cryptographic verification (FINDING-3D-01) |
| DEFECT-045 | E2E emitted a plain dict instead of real ExecutionManifest (FINDING-3D-02) |
| DEFECT-046 | E2E bypassed TrustStatusStore (FINDING-3D-03) |

#### D9.8.2 CBOR-LIB-EVAL headers (3 total)

| Header | Summary |
|---|---|
| CBOR-LIB-EVAL-001 | ciborium 0.2.2 selected for 3A.2 |
| CBOR-LIB-EVAL-002 | cbor2 6.1.5 selected for Python adapter (3A.3) |
| CBOR-LIB-EVAL-003 | cbor 9.0.2 selected for JavaScript adapter (3A.4A) |

#### D9.8.3 GAP headers (3 total)

| Header | Summary |
|---|---|
| GAP-8 | Rust ML-DSA sigGen not covered by ACVP KAT |
| GAP-9 | ML-DSA-65 key_id uses raw pk bytes, not SPKI DER |
| GAP-3.4B-01 | wasm-bindgen nodejs CWD-relative wasm path |

---

### D9.9 Evidence Summary

#### D9.9.1 Source

The single source for defect detail is `docs/vomega/DEFECTS-LOG.md`. D9 does not reproduce that file; it indexes and classifies.

#### D9.9.2 Reproduction

```bash
cd ~/Desktop/EnterpriseGuard && \
echo "═══ Total DEFECT headers ═══" && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -cE "^## DEFECT-" && \
echo "═══ Unique DEFECT numbers (base) ═══" && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -oE "^## DEFECT-[0-9]{3}" | sort -u | wc -l && \
echo "═══ Suffix variants ═══" && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -cE "^## DEFECT-[0-9]{3}-[A-Z]" && \
echo "═══ CBOR-LIB-EVAL headers ═══" && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -cE "^## CBOR-LIB-EVAL-" && \
echo "═══ GAP headers ═══" && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -cE "^## GAP-" && \
echo "═══ RISK headers ═══" && \
git show 7683adb:docs/vomega/DEFECTS-LOG.md | grep -cE "^## RISK-"
```

**Expected:**

```
═══ Total DEFECT headers ═══
46
═══ Unique DEFECT numbers (base) ═══
44
═══ Suffix variants ═══
1
═══ CBOR-LIB-EVAL headers ═══
3
═══ GAP headers ═══
3
═══ RISK headers ═══
4
```

#### D9.9.3 Commit reference

The full defect record as of the evidence-reference commit `7683adb` is what D9 indexes. Later commits may add defect entries; D9 reflects the state at that commit.

---

### D9.10 What D9 Does Not Claim

- D9 does not claim that the defect record is exhaustive of every defect that occurred during development. It records the defects that were logged.
- D9 does not claim that all defects were caught by tests. Some were caught by code review, by probing, or by adversarial review.
- D9 does not claim that the classification in §D9.3 is unique. A defect may fit multiple categories; the classification reflects the dominant nature and recorded facets.
- D9 does not claim that all open GAPs will be closed. GAP-8, GAP-9, and GAP-3.4B-01 are documented as understood limitations.
- D9 does not reproduce the full text of any defect. The full record is in `DEFECTS-LOG.md`; D9 is an index.
- D9 does not claim that the five architecture-critical defects in §D9.4 are the only defects with architectural consequences. They are the five explicitly classified as architecture-critical in the log.
- D9 does not claim that the RISK-3.3 status will not change. It is ACTIVE at the evidence-reference commit.
- D9 does not claim that RISK entries and DEFECT entries are interchangeable. They record different classes of observation: a DEFECT is a defect that was found and fixed; a RISK is a tracked concern that may or may not materialize.
- D9 does not claim that RISK-3.1 is a single header. It appears twice (original + reclassification), following the same documentary pattern as DEFECT-017. The duplication is documented in §D9.7.1.

---

**End of D9.**

## D10. Positioning Against Adjacent Technologies

**Part II, Section D10.**
**Scope:** a positioning analysis of vOmega relative to six adjacent technologies — JWT/JWS, COSE, CMS, plain CBOR, SCITT, Sigstore — based on **documented architectural properties**, not on quality or security claims.
**Constraint:** D10 does not claim that vOmega is "better than," "more secure than," or "a replacement for" any of the technologies discussed. It documents where vOmega's composition overlaps with each, and where it differs. Comparison is on architecture and scope, not on absolute merit.

---

### D10.1 Scope and Method

#### D10.1.1 What "positioning" means here

D10 uses the word *positioning* in a narrow, technical sense. It does not mean:

- vOmega is superior to any other technology.
- vOmega replaces any other technology.
- Any other technology is inadequate for its purpose.

It means:

- For each of six adjacent technologies, D10 records **what that technology provides** (a documented capability, not an opinion).
- It records **where vOmega overlaps** with that technology (if at all).
- It records **where vOmega differs** (the specific architectural property that distinguishes the two).
- It records **what vOmega borrows** from that technology (if any).

The comparison criterion is **architectural scope**, not security, performance, or quality.

#### D10.1.2 Why architectural scope is the criterion

vOmega is a composition of existing primitives (deterministic CBOR, JCS, cryptographic signatures, structured authority models) under stricter invariants. Many of the adjacent technologies also compose primitives under constraints. Comparing them on "security" would require a threat model that is specific to each technology's deployment context — a comparison that D10 cannot make without claiming to be a security audit of those technologies, which it is not.

Comparing them on **architectural scope** — what each defines, what each does not define, and where the two definitions overlap — is a factual exercise. That is what D10 does.

#### D10.1.3 The six adjacent technologies

| Technology | Category |
|---|---|
| **JWT / JWS** (RFC 7515, RFC 7519) | JSON-based signed tokens |
| **COSE** (RFC 9052, RFC 9964) | CBOR-based signing and encryption structures |
| **CMS / PKCS#7** (RFC 5652) | ASN.1-based cryptographic messaging |
| **Plain CBOR** (RFC 8949) | Binary data encoding |
| **SCITT** (Supply Chain Integrity, Transparency, and Trust) | IETF standards defining Signed Statements, Transparency Services, Verifiable Data Structures, and Receipts for trustworthy and transparent digital supply chains (RFC 9943, RFC 9942). |
| **Sigstore** | Signing infrastructure combining OIDC-bound short-lived certificates, a transparency/auditability service, and a signing client, for software artifacts. |

Each is documented here as it is defined by its own specification or, in the case of Sigstore, by its own project documentation. D10 does not attempt to characterize any of these technologies beyond what their own definitions state.

#### D10.1.4 Evidence base

D10 is primarily an architectural analysis. Where a specific vOmega property is cited, it points to a section of this document or to `docs/vomega/CONTINUITY.md` or `docs/vomega/DEFECTS-LOG.md`. Where a specific property of an adjacent technology is cited, it points to the corresponding RFC or project documentation by identifier.

**Evidence-reference commit.** `7683adb` (reproducibility baseline).

---

### D10.2 JWT / JWS

#### D10.2.1 What JWT / JWS provides

JWS (RFC 7515) defines a JSON-based structure for signing arbitrary byte payloads. In the JWS Compact Serialization, the signing input is computed from the base64url-encoded **protected header** and the base64url-encoded payload. In the JWS JSON Serialization, multiple signatures may be present, and unprotected headers do not participate in the signing input. JWT (RFC 7519) defines a set of registered claims (`iss`, `sub`, `exp`, `nbf`, `aud`, `iat`, `jti`) that can be carried in a JWS payload for token use cases.

#### D10.2.2 Where vOmega overlaps

- **Signing a semantic artifact.** Both vOmega and JWS bind a signature to a payload that is delivered alongside the signature. In both cases, the signature is computed over a byte sequence derived from the payload and its metadata.
- **Claim-based identity.** Both carry a set of named fields that constitute the artifact's semantic content.

#### D10.2.3 Where vOmega differs

| Property | JWS | vOmega (DCP 2.1 / B+) |
|---|---|---|
| Signing input framework | JOSE signing input (`BASE64URL(protected_header) ‖ "." ‖ BASE64URL(payload)`) in the Compact Serialization | `ADIE-SIG-V2\0` ‖ JCS(certificate_without_signatures) |
| Payload serialization | JSON, with base64url encoding for transport | Semantic certificate canonicalized by JCS (RFC 8785) |
| Deterministic encoding requirement | Not specified for JSON payloads | Required (JCS) |
| Signing-input dependence | The **protected header** participates in the signing input; the full serialized container is not, by itself, a single signed byte sequence. | The signing input does not include any wire container bytes; the CBOR envelope does not participate. |

The relevant difference is that in JWS, the **protected header** contributes to the signing input, whereas in vOmega the envelope (the wire container) contributes no bytes to the signing input. The JWS signing input is not "the container"; it is the concatenation of a specific subset (protected header and payload), by the rules of the serialization. vOmega's signing input is a similarly specific subset — the semantic certificate — with the envelope excluded by design. This is the Model B+ decision documented in §D2.2 and §D7.5.

#### D10.2.4 What vOmega borrows

No structural element. The vOmega certificate is not a JWS object, and the vOmega hybrid signature scheme is not a JOSE algorithm. The two are parallel designs addressing overlapping problems.

#### D10.2.5 What D10 does not claim

D10 does not claim that vOmega is "more secure" than JWS. JWS is a widely deployed, thoroughly reviewed standard. The two designs occupy different architectural points: JWS is a general-purpose signed-token format; vOmega is a decision-artifact format with explicit governance and trust layers. A deployment could use JWS for token delivery while using vOmega for the semantic decision artifact; the two are not in direct competition.

---

### D10.3 COSE

#### D10.3.1 What COSE provides

COSE (RFC 9052) defines CBOR-based structures for signing, encryption, and key representation. `COSE_Sign` and `COSE_Sign1` define signing structures in which the bytes to be signed are computed by the framework according to a defined `Sig_structure`; that structure incorporates context strings, protected attributes, and the payload. RFC 9964 (published May 2026) registers ML-DSA algorithm identifiers for COSE, including ML-DSA-65 (identifier `-49`), and defines the AKP key type for COSE.

#### D10.3.2 Where vOmega overlaps

- **CBOR as the transport encoding.** Both use CBOR as the binary representation.
- **ML-DSA-65 as a signature algorithm.** vOmega's hybrid profile includes ML-DSA-65 as one of the two required algorithms; COSE has a registered identifier for ML-DSA-65 (RFC 9964).
- **Algorithm identifier reuse.** vOmega uses the IANA COSE algorithm identifiers `-257` (RS256) and `-49` (ML-DSA-65). This reuse is documented in Amendment-1 §A2.4.

#### D10.3.3 Where vOmega differs

| Property | COSE | vOmega (Model B+) |
|---|---|---|
| Signing input | `Sig_structure` defined by the framework, incorporating context, protected attributes, and payload | `ADIE-SIG-V2\0` ‖ JCS(certificate_without_signatures) |
| Wire container participation | The signature covers the COSE `Sig_structure`, which references signing metadata and the payload | The signature covers only the semantic certificate; no envelope bytes participate |
| Signing object | `COSE_Sign` / `COSE_Sign1` | ADIE-native hybrid certificate (not a COSE object) |

This is the Model B+ architectural decision (Amendment-1 §A2, DECISION-0.3). The decision is documented in §D2.2 and the preservation argument is documented in §D7.5.

#### D10.3.4 What vOmega borrows

- **`COSE_Key` for ML-DSA-65 key representation.** The ML-DSA-65 public key is represented using the `COSE_Key` structure per RFC 9964 (AKP key type). This is a **key representation**, not a signing structure.
- **Algorithm identifiers.** `-257` (RS256) and `-49` (ML-DSA-65) are reused as IANA-registered values.

Both borrowings are documented in Amendment-1 §A2.4.

#### D10.3.5 What D10 does not claim

D10 does not claim that vOmega is "more COSE-compliant" than a COSE implementation, or that COSE is "inadequate." Amendment-1 §A2.3 explicitly states that vOmega does not claim compliance with any COSE signing profile or any composite-signature standard. The two designs address different problems: COSE is a general-purpose CBOR signing framework; vOmega is an application-level decision artifact with a stable cryptographic identity independent of transport.

A future COSE-native profile is reserved (Amendment-1 §A6) with a distinct domain tag; vOmega does not implement it.

---

### D10.4 CMS / PKCS#7

#### D10.4.1 What CMS provides

CMS (RFC 5652, superseding PKCS#7) defines ASN.1-based structures for signing, encryption, and enveloping data. `SignedData` and its variants are widely used in email (S/MIME), code signing, and document signing contexts. CMS permits the use of BER as a base encoding; when signed attributes are present, RFC 5652 requires those attributes to be DER-encoded.

#### D10.4.2 Where vOmega overlaps

- **Signing a semantic artifact.** Both bind a signature to a payload delivered alongside the signature.
- **Multi-signature support.** Both CMS `SignedData` and vOmega's `signatures[]` array can carry multiple signatures over the same payload.

#### D10.4.3 Where vOmega differs

| Property | CMS | vOmega |
|---|---|---|
| Wire encoding | ASN.1-based encoding; CMS permits BER encoding, while signed attributes are required to be DER-encoded when present. | Deterministic CBOR (DCP 2.1) |
| Canonicalization for signing | Defined per signed-attribute rules (RFC 5652 §5.4) | JCS (RFC 8785) |
| Deterministic encoding | Context-dependent; DER is required for signed attributes, while CMS as a whole is not equivalent to a universally DER-only container. | Deterministic by construction (DCP 2.1 + JCS) |
| Semantic model | Generic signed attributes | ADIE-specific decision certificate with 13 named fields |
| Governance layer | Not defined | Dual-axis decision model (§D4) |
| Trust model | Signer/key identification with optional certificate carriage; trust establishment is deployment-dependent | Authority-based assertion model (§D5) |

#### D10.4.4 What vOmega borrows

No structural element. vOmega does not use ASN.1, does not carry X.509 certificates, and does not reuse CMS signed-attribute rules. The two are parallel designs in different encoding families.

#### D10.4.5 What D10 does not claim

D10 does not claim that vOmega is "lighter" or "better" than CMS. CMS is a mature, standard-integrated system widely deployed in email and document-signing contexts. vOmega is not a CMS replacement; it addresses a decision-artifact use case where a JSON-based canonicalization (JCS) and a governance model are the primary requirements.

---

### D10.5 Plain CBOR (RFC 8949)

#### D10.5.1 What plain CBOR provides

RFC 8949 defines a binary data encoding with a defined set of major types and additional information fields. It permits multiple encodings for the same semantic value (shortest vs overlong integers, definite vs indefinite-length items, optional tag use). RFC 8949 §4.2 defines deterministic encoding requirements that protocols may adopt or further restrict.

#### D10.5.2 Where vOmega overlaps

- **CBOR as the transport family.** The B+ envelope is a CBOR map.
- **Rejection categories.** Most of the 14 `E_WIRE_*` codes classify violations of either RFC 8949 rules or DCP 2.1's stricter restrictions on top of them.

#### D10.5.3 Where vOmega differs

| Property | Plain CBOR (RFC 8949) | vOmega (DCP 2.1) |
|---|---|---|
| Encoding latitude | Permits overlong integers, indefinite items, floats, tags | Excludes all of these |
| Map key discipline | Any major type as key | Unsigned integer keys only |
| Map key ordering | Not required | Numeric ascending |
| Tag use | Permitted | Rejected (major type 6) |
| Depth limit | Not specified | 32 (bounded) |
| Rejection codes | Not applicable (no rejection model) | 14 typed `E_WIRE_*` codes |
| Authority for wire rules | Not defined | `rawcheck` (byte-level authority) |

DCP 2.1 is a **stricter profile** on top of RFC 8949, not a replacement. The relationship is documented in §D1 and §E2.2.1.

#### D10.5.4 What vOmega borrows

The entire byte-level syntax. DCP 2.1 uses the CBOR major-type/additional-information structure as defined by RFC 8949 and adds a stricter profile above it. RFC 8949 §4.2 (deterministic encoding) is the specific clause that DCP 2.1 restricts further.

#### D10.5.5 What D10 does not claim

D10 does not claim that RFC 8949 is "insufficient." The RFC explicitly permits protocols to define their own deterministic profiles. DCP 2.1 is one such profile.

---

### D10.6 SCITT

#### D10.6.1 What SCITT provides

SCITT (Supply Chain Integrity, Transparency, and Trust) is defined by IETF standards (RFC 9943 and RFC 9942) as a set of architectural elements for **trustworthy and transparent digital supply chains**. The architecture includes:

- **Signed Statements** — signed claims about supply-chain artifacts, carried as enveloped COSE structures (`COSE_Sign1`-based).
- **Transparency Services** — services that append statements to an **append-only log** and issue receipts.
- **Verifiable Data Structures (VDS)** — the data structures underlying a Transparency Service. SCITT supports multiple VDS constructions; specific implementations may use Merkle-style proofs, but SCITT does not require a single VDS construction.
- **Receipts** — proofs that a statement has been included in a Transparency Service's log.

RFC 9942 provides COSE receipt encodings, including Merkle-style proof encodings.

#### D10.6.2 Where vOmega overlaps

- **Signed claims.** Both define a signed artifact (a Signed Statement in SCITT; a certificate in vOmega).
- **Structured signing input.** Both define a specified signing structure that cryptographically binds the signed artifact to its metadata and payload. vOmega additionally fixes its own JCS/DCP 2.1 canonicalization rules; SCITT's Signed Statement is carried as an enveloped COSE structure whose signing input is defined by COSE.
- **Cryptographic binding.** Both bind a signature to a payload via a defined signing input.

#### D10.6.3 Where vOmega differs

| Property | SCITT | vOmega |
|---|---|---|
| Transparency Service | **Defined** (Append-only log / VDS; multiple VDS constructions supported) | **Not defined** |
| Receipt structure | **Defined** (proof of inclusion) | **Not defined** |
| Governance model | Not the primary focus | Dual-axis decision model (§D4) |
| Trust model | Issuer/signature + Transparency Service / Receipt model | Authority-based assertion model (§D5) |
| End-to-end path | Not the primary focus | Defined (§D6) |

The most consequential difference is that **SCITT defines a Transparency Service and receipts; vOmega does not.** vOmega's trust model is authority-based: a decision records the trust status of the authority that authorized it, and later changes to that authority do not overwrite the record. This is a different design point from a Transparency Service, which records statements in an append-only log/VDS and issues proofs of inclusion.

The two are not mutually exclusive. A deployment could sign its certificates under vOmega and publish their hashes to a SCITT Transparency Service for transparency; SCITT provides the transparency layer, vOmega provides the semantic artifact and its governance. This composition is **not implemented by vOmega** and is mentioned only as a design observation.

#### D10.6.4 What vOmega borrows

No structural element. vOmega does not implement a Transparency Service, does not produce inclusion receipts, and does not use SCITT's Signed Statement format.

#### D10.6.5 What D10 does not claim

D10 does not claim that SCITT is "redundant" or that vOmega "makes it unnecessary." SCITT addresses a distinct transparency requirement. vOmega addresses a decision-artifact and governance requirement. A deployment requiring both properties would use both. The composition is outside the current vOmega scope.

---

### D10.7 Sigstore

#### D10.7.1 What Sigstore provides

Sigstore is an open-source project providing signing infrastructure for software artifacts. Its components include:

- **Fulcio** — a certificate authority that issues short-lived certificates binding an ephemeral signing key to an OIDC identity.
- **Rekor** — a transparency/auditability service in which signing events are recorded.
- **Cosign** — a signing and verification client.
- **Timestamping authority** — a trusted timestamp service.

Sigstore's design point is keyless signing: an OIDC identity provider authenticates the signer, Fulcio issues a short-lived certificate, and the signing event is recorded in Rekor.

**Sigstore's Trust Root.** Sigstore's Trust Root distributes the trusted verification material for Sigstore services, including Fulcio and Rekor, through **TUF** (The Update Framework). OIDC providers supply the identity assertions consumed by Fulcio; they are not described here as components of the Sigstore Trust Root itself.

#### D10.7.2 Where vOmega overlaps

- **Signed artifacts.** Both produce signed artifacts.
- **Cryptographic binding.** Both bind a signature to an artifact.
- **Hash-based identification.** Both produce content hashes that can be used for identity purposes.

#### D10.7.3 Where vOmega differs

The comparison is on **two specific architectural properties**, not on overall system quality:

| Property | Sigstore | vOmega |
|---|---|---|
| Signing-key model | Short-lived certificate binding an ephemeral signing key to an OIDC identity; signing events are recorded in Rekor. | Authority-associated signing key material; key lifetime and rotation are not defined by the current vOmega scope. |
| Transparency / auditability service | **Defined** (Rekor) | **Not defined by vOmega** |
| Sigstore trust root | Fulcio/Rekor verification material distributed through TUF | Not defined (authorities provided as inputs; §E6.5, F-04/F-05) |
| Identity binding | OIDC identity | Authority identity (§D4.6) |
| Governance layer | Not the focus | Dual-axis decision model (§D4) |
| Trust-status history | Recorded in the transparency service | Explicit append-only assertion store (§D5) |

The distinguishing architectural property is that **Sigstore combines OIDC-bound short-lived signing certificates with a transparency/auditability service**, whereas vOmega does not define either a Fulcio-style CA or a Rekor-style transparency service.

#### D10.7.4 What vOmega borrows

No structural element. vOmega does not implement a Fulcio-style CA, does not implement a Rekor-style transparency service, does not use OIDC identity, and does not implement keyless signing.

#### D10.7.5 What D10 does not claim

D10 does not claim that vOmega is "more secure" or "simpler" than Sigstore. Sigstore is a widely adopted project with a distinct trust model suited to software supply chains. vOmega addresses a decision-artifact use case; Sigstore addresses software-artifact signing at scale. The two occupy different architectural points.

The specific comparison in §D10.7.3 is on **transparency / auditability service anchoring** and **signing-key model**, not on overall system merit.

---

### D10.8 Summary Table

The following table summarizes the architectural scope of each technology against vOmega's stated scope. It is a scope table, not a feature-quality table. Cells answer the question: *does this technology define this architectural property?*

| Property | JWT/JWS | COSE | CMS | Plain CBOR | SCITT | Sigstore | **vOmega** |
|---|---|---|---|---|---|---|---|
| Signed artifact | Yes | Yes | Yes | No (encoding only) | Yes | Yes | **Yes** |
| Deterministic byte encoding | No (JSON + base64url) | Yes (CBOR + Sig_structure) | Context-dependent (DER for signed attributes when present; BER permitted as base) | Optional (RFC 8949 §4.2) | Underlying payload may be structured; deterministic encoding is not SCITT's own construction | Not the focus | **Yes (DCP 2.1 + JCS)** |
| Signing input excludes the complete transport envelope | Depends on serialization; protected header participates in the signing input | No; `Sig_structure` incorporates signing metadata and payload | Depends on `SignedData` / `SignedAttributes` structure | N/A | Depends on the enveloping COSE structure | Depends on the signing format | **Yes** |
| Multi-signature over same payload | Yes (JWS JSON serialization) | Yes (`COSE_Sign`) | Yes (`SignedData`) | N/A | Not the focus | Not the focus | **Yes (`signatures[]`)** |
| Transparency / auditability service | No | No | No | No | **Yes (Transparency Service + VDS + Receipts)** | **Yes (Rekor)** | **No** |
| Governance model (lifecycle / authorization separation) | No | No | No | No | No | No | **Yes (§D4)** |
| Authority-based trust-status history | No | No | No | No | No (log-based) | No (log-based) | **Yes (§D5)** |
| End-to-end decision path | No | No | No | No | No | No | **Yes (§D6)** |
| External-execution boundary | Not defined | Not defined | Not defined | N/A | Not defined | Not defined | **Defined (§D6.2.9)** |

The following two scope boundaries are worth stating explicitly:

- vOmega does not define a transparency / auditability service. This is a scope choice; a deployment could compose vOmega with SCITT or Sigstore for that function.
- vOmega does not define a certificate authority or trust-bootstrap mechanism. Authorities are provided as inputs; their establishment is an external step (§E6.5, F-04/F-05).

---

### D10.9 What D10 Does Not Claim

- D10 does not claim that vOmega is more secure than any adjacent technology.
- D10 does not claim that vOmega replaces any adjacent technology.
- D10 does not claim that any adjacent technology is inadequate for its purpose.
- D10 does not claim that the summary table in §D10.8 is exhaustive of the architectural properties of the adjacent technologies. It lists the properties relevant to the vOmega scope.
- D10 does not claim that the scope rows in §D10.8 establish quality differences. A "Yes" in a cell means "this technology defines this property," not "this technology is better because of it."
- D10 does not claim that any composition between vOmega and an adjacent technology is implemented. Compositions such as vOmega + SCITT or vOmega + Sigstore are mentioned only as design observations, not as implemented features.
- D10 does not claim that the "No" entries in the vOmega column are deficiencies. They are scope boundaries; a deployment with the corresponding requirement would need to compose vOmega with a technology that provides it.
- D10 does not claim that adjacent technologies lack properties not listed in the table. Only the properties relevant to vOmega's scope are listed.
- D10 does not claim that the RFC identifiers used in this section represent the only relevant specifications of the technologies named. They are the specification references used by this document.
- D10 does not claim that vOmega defines key lifetime or rotation. Authority-associated signing key material is used, but the current vOmega scope does not define key lifetime, rotation, or revocation policy at the signing-key layer.

---

**End of D10.**

# End of Part II (D1–D10)

**D11–D12 and Part III (Appendices A–H) are not part of this recovery.**

---

# End of Recovered Document

**Status:** Recovered / Staged / Pending Commander Review
**Recovery source:** conversation transcript
**Evidence-reference commit:** `7683adb` (branch `vOmega`)
**Not yet performed:** Commander file review; single clean commit
