# EnterpriseGuard Execution Plan

**Version:** 3.0
**Status:** AUTHORITATIVE AFTER DC-145 ADOPTION
**Governed by:** `continuity/RULES.md`
**Supersedes:** Version 2.4, preserved in Git history and the plan changelog
**Adoption condition:** This plan becomes authoritative only after DC-145 is recorded in the canonical decision log and index and this transition is recorded in `docs/PLAN_CHANGELOG.md`.

## 1. Product Definition and North Star

EnterpriseGuard provides independently verifiable trust infrastructure for consequential AI decisions. The north star is a portable, evidence-bound decision proof that remains verifiable outside the issuer's live runtime.

## 2. Current-State Baseline

- C1 demo: treated as complete by owner instruction; local recording evidence exists and the deliverable is treated as unlisted.
- C2 benchmarks: **BLOCKED**; the 100K/10-writer p99 target was not met; `docs/BENCHMARKS.md` does not exist.
- C3 security report: report complete; OWASP ASVS Level 1 **not demonstrated**; material findings remain.
- C4 design partners: **BLOCKED**; no real signed LOIs are evidenced.
- Existing SDK/API/dashboard and signing/verification behavior remain v2.4 compatibility surfaces.

The v2.4 Phase C gate is not silently erased. C2 and C4 remain blocked, and C3 remains a report with unresolved findings. They are converted into bounded prerequisite work below, not marked complete.

## 3. Governance and Authority

`continuity/RULES.md` is binding operational authority. This plan is the sole executable authority after DC-145 adoption. `docs/ROADMAP.md` and `docs/DECISION_TRUST_LAYER.md` are non-authoritative strategic/navigation documents. No future phase is activated by description alone.

## 4. Trust Model and Threat Boundaries

The issuer, signing keys, verifier, evidence store, policy, model/agent identity, timestamps, and delegation authorities are explicit trust boundaries. Independent verification must not require online EnterpriseGuard services or vendor-private state. Threats include tampering, key compromise, replay, equivocation, unauthorized delegation, disclosure, rollback, and availability loss.

## 5. Technology Classification and Anti-Scope

| Technology/capability | Classification |
|---|---|
| Python, SQLite/JSON, stdlib HTTP, vanilla JS, existing RSA/ECDSA | Executable when its phase prerequisites pass |
| Decision Certificate, offline verifier, identity, delegation, provenance, policy binding, model/agent provenance, trusted timestamping | Design and implementation phases below; not executable before their phase |
| Attestation, Merkle transparency, agent-to-agent trust, deterministic replay, formal verification, multi-party trust | Design/research until their phase gates pass |
| PQC, selective disclosure, ZKP, TEE, distributed evidence storage, open protocol ecosystem | Future/non-executable until their specific phase is reached and separately gated |
| PostgreSQL, Rust, gRPC, ZKP libraries, new databases, and unapproved dependencies | Forbidden unless a later explicit plan amendment changes this classification |

No technology is executable merely because it is named in this plan.

## 6. Phase 0 Security Foundation

**Executable first.** Define threat model, security ownership, secret handling, TLS boundary, dependency review, vulnerability remediation, logging, incident response, and security acceptance evidence. Phase 0 must produce a security baseline and remediation closure/acceptance for the C3 findings. No later phase starts until its binary gate passes.

## 7. Phase 1 Decision Certificate

Define and implement a versioned portable certificate binding E1-E8 from DC-143. Specify canonicalization, schema, required fields, signature algorithms, verification failures, compatibility, and negative tests. No deterministic replay, ZKP, or selective disclosure is implied.

## 8. Phase 2 Independent Verifier

Build an offline verifier for the Phase 1 certificate. It must verify without issuer availability and provide binary valid/invalid outcomes for tampering, wrong key, malformed certificate, unsupported version, and missing bindings.

## 9. Phase 3 Identity

Define issuer, verifier, agent, organization, and key identities; lifecycle, rotation, revocation, and identity-binding evidence. Acceptance requires negative tests for substitution, expiry, and revoked identity.

## 10. Phase 4 Delegation and Authority

Define scoped, time-bounded, auditable delegation and authority chains. Acceptance requires valid-chain and unauthorized-delegation rejection tests.

## 11. Phase 5 Decision Provenance DAG

Define canonical provenance nodes, edges, hashes, ordering, completeness, and cycle handling. Acceptance requires independent reconstruction and tamper rejection.

## 12. Phase 6 Policy Binding

Bind policy identity and version to certificates and verifier output. Acceptance requires policy substitution, missing-policy, and version-mismatch failures.

## 13. Phase 7 Model and Agent Provenance

Bind model/rule identity, agent identity, configuration references, and provenance commitments. Acceptance requires mismatch and omission rejection.

## 14. Phase 8 Attestation

Design attestation boundaries and failure semantics. Production attestation is non-executable until a phase-specific decision authorizes the mechanism, threat model, privacy impact, and acceptance tests.

## 15. Phase 9 Merkle Transparency

Design transparency log, inclusion/consistency proofs, equivocation handling, retention, and verifier behavior. Implementation is gated and not implied by existing local anchoring.

## 16. Phase 10 Trusted Timestamping

Preserve the v2.4 non-blocking TSA failover semantics. Any extension must define token canonicalization, provider identity, failure states, retries, and negative verification tests.

## 17. Phase 11 Post-Quantum Cryptography

**Future/non-executable.** No PQC implementation, dependency, migration, or algorithm claim is authorized until all prior gates pass and a dedicated amendment authorizes scope and interoperability.

## 18. Phase 12 Privacy and Selective Disclosure

**Future/non-executable.** Define privacy threat model and design only after certificate and verifier gates pass. No selective-disclosure implementation is authorized here.

## 19. Phase 13 Zero-Knowledge Proofs

**Future/non-executable.** ZKP remains prohibited until a dedicated governance decision, technology approval, soundness model, and acceptance gate are adopted.

## 20. Phase 14 Agent-to-Agent Trust

Design authenticated agent exchange, identity, delegation, replay, failure, and audit semantics. No protocol implementation precedes Phase 3 and Phase 4 acceptance.

## 21. Phase 15 Deterministic Replay

Define replay versus reconstruction, required inputs, nondeterminism, version pinning, and bounded claims. No deterministic replay promise is made before a binary reproducibility gate passes.

## 22. Phase 16 Formal Verification

Research/design only until the target properties, formalism, trusted toolchain, proof artifacts, and review gate are approved.

## 23. Phase 17 Multi-Party Trust

Define quorum, authority composition, failure, equivocation, revocation, and recovery. Implementation requires accepted identity and delegation foundations.

## 24. Phase 18 Distributed Evidence and Scale

Future/non-executable. Preserve current SQLite/JSON compatibility until a separately gated scale decision. PostgreSQL or distributed storage is not authorized by this plan alone.

## 25. Phase 19 Developer Ecosystem

After verifier stability, define SDK/API versioning, documentation, conformance fixtures, integration compatibility, and support boundaries. Existing v2.4 contracts must remain compatible or be explicitly versioned.

## 26. Phase 20 Open Protocol and Ecosystem

Future/non-executable until certificate, verifier, identity, provenance, security, and interoperability gates pass. Define governance, versioning, conformance, and compatibility before implementation.

## 27. Interoperability

Every executable trust artifact must define canonical serialization, version negotiation, algorithm identifiers, unknown-field behavior, failure semantics, and conformance vectors. Existing v2.4 SDK/API behavior is preserved or versioned before change.

## 28. Migration and Backward Compatibility

Existing signed decisions, JSONL records, API endpoints, SDK behavior, keys, and dashboards remain readable or receive an explicit migration/versioning plan. No destructive migration is authorized. Legacy verification behavior must remain testable.

## 29. Security Gates

Each executable phase requires threat-model review, secret/key review, negative tests, dependency review, logging and failure semantics, and an owner-accepted security result. No phase may claim security compliance from documentation alone.

## 30. Acceptance Gates

Every phase has a binary gate with raw evidence: deliverables exist, required tests pass, negative tests pass, compatibility is demonstrated, and security review findings are closed or explicitly owner-accepted. Phase 0 additionally requires a completed security baseline and disposition of all C3 findings.

## 31. Execution Order and Dependencies

Order is Phase 0, then Phases 1-20. A later phase cannot authorize earlier work retroactively or authorize work belonging to a later phase. Phase C v2.4 blockers remain prerequisites: C2 requires a passing benchmark deliverable, C3 requires security findings to be dispositioned for the relevant gate, and C4 requires three real signed LOIs. No Phase D or trust-infrastructure production claim bypasses these gates.

## 32. Change Control

Any scope, technology, acceptance, phase-order, or authority change requires owner-authored plan replacement, an incremented version, a unique governance decision in the canonical log and index, and a `docs/PLAN_CHANGELOG.md` entry. All agents must reload the adopted plan. This v3.0 plan does not authorize implementation of future/non-executable technologies by implication.
