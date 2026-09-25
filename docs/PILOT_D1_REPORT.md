# EnterpriseGuard — Phase D1 Pilot Report

## 1. Pilot Overview & Partner Identity

- **Partner Name:** TBD — owner assignment pending
- **Pilot Start Date:** 2026-09-25
- **Pilot Status:** Not yet started
- **Target Decision Volume:** ≥ 1,000 valid decisions
- **Primary Use Case:** Immutable audit trails and decision verification

## 2. Architectural Baseline Compliance

- **Storage Tier:** SQLite 3 with WAL mode where the approved Phase C query tier is used:
  - `journal_mode = WAL`
  - `synchronous = NORMAL`
  - `busy_timeout = 5000`
  - `wal_autocheckpoint = 1000`
- **Integrity Model:** Append-oriented persistence with cryptographic integrity / chain-continuity verification and signature verification where applicable.
- **Infrastructure Restriction:** No unauthorized infrastructure changes are permitted during D1.
- **Architecture Status:** No PostgreSQL, ClickHouse, Redis, Kubernetes, or other new infrastructure may be introduced during D1 without explicit authorization and evidence-based scale justification.

> SQLite/WAL provides the approved storage behavior for the current tier; it is not itself treated as proof of physical WORM immutability.

## 3. Execution & Decision Ingestion Metrics

- **Total Decisions Recorded:** 0
- **Valid Verifiable Decisions:** 0
- **Observed Latency (p50 / p95 / p99):** Pending
- **Throughput:** Pending
- **Error Rate:** Pending
- **Verification Success Rate:** Pending

## 4. Integrity & Tamper Drill Results

- [ ] **Test A — Valid Record:** Pending
- [ ] **Test B — Modified Payload:** Pending
- [ ] **Test C — Broken Hash Linkage:** Pending
- [ ] **Test D — Invalid Signature:** Pending

All tamper testing must be performed against a controlled test copy or disposable dataset and must not modify authoritative production evidence.

## 5. Security & Verification Evidence

- **Authentication:** Pending validation against the deployed D1 configuration.
- **Authorization:** Pending validation.
- **Request Size Limits:** Pending confirmation from the currently deployed implementation.
- **Filesystem Permissions:** Pending validation of actual deployed files/directories.
- **Transport Security:** Pending validation if any interface is exposed beyond localhost.
- **Credential Handling:** Pending validation.
- **Verification Path:** Pending end-to-end partner verification test.

## 6. Findings & Operational Friction

- **Developer Friction:** No data collected yet.
- **Operator Feedback:** Pending partner onboarding.
- **Integration Friction:** Pending.
- **Open Defects / Limitations:** Baseline validation pending.
- **Known Constraints:** D1 remains within the currently authorized architecture and does not authorize infrastructure expansion.

## 7. Pilot Evidence

The following evidence must be collected during D1:

- Partner onboarding record
- Environment identifier
- SDK / application version
- Decision count
- Performance measurements
- Integrity verification results
- Tamper-drill results
- Security validation results
- Verification results
- Operational incidents
- Partner feedback
- Known limitations

## 8. D1 Exit Criteria

D1 is eligible for completion only when:

- [ ] ≥ 1,000 valid decisions are recorded
- [ ] Valid decisions are successfully verifiable
- [ ] Tamper detection is demonstrated
- [ ] Invalid signatures are rejected
- [ ] Performance measurements are captured
- [ ] Security validation is captured
- [ ] Partner feedback is recorded
- [ ] Evidence package is complete
- [ ] Project Owner / Governance review is complete

## 9. Recommendation for D2

- **Status:** Pending
- **Condition:** D1 exit criteria must be satisfied and the evidence must be reviewed by the Project Owner / Governance authority before proceeding to D2 — Case Study.
