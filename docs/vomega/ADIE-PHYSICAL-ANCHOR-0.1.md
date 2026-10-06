# ADIE — Physical Anchor & Layer-2 Definitions

**Document:** ADIE-PHYSICAL-ANCHOR-0.1
**Status:** NON-NORMATIVE — North Star supplement
**Branch:** vOmega
**Date:** 2026-10-06
**Authority:** DECISIONS-0.2
**Applies to:** Target architecture, Phase 2 onwards

---

## §0. Standing

This document refines `ADIE-TERMINAL-ARCHITECTURE-0.1 §1` with
definitions of physical anchoring, hardware identity, TEE roles, and
temporal evidence.

It has NO normative authority over:
- META-CONTRACT-0.1
- ACL-0.1
- AUTHORING-0.1
- REGISTRY-0.1
- ERROR-REGISTRY-0.1
- Any existing test vector

Cross-references:
- [META-CONTRACT-0.1](./META-CONTRACT-0.1.md)
- [ADIE-TERMINAL-ARCHITECTURE-0.1](./ADIE-TERMINAL-ARCHITECTURE-0.1.md)
- [DECISIONS-0.2](./decisions/DECISIONS-0.2.md)

---

## §1. Layer-2 definition

ADIE Layer-2 is an **Integrity / Attestation Overlay**, not a blockchain.

```
Existing System (EnterpriseGuard, SIBB, CI/CD, runtime)
        │
        ▼
    ADIE Layer-2
        │
    ┌───┼────┐
    ▼   ▼    ▼
Identity Evidence Semantics
    │   │    │
    └───┼────┘
        ▼
    Claim / Proof
```

ADIE does not replace EnterpriseGuard or SIBB.
It adds an integrity/evidence plane above them.

---

## §2. Core invariant

```
No physical primitive creates truth.
```

Every physical component is classified as a source of **Evidence**, not
as a source of **Truth**.

| Component | Classification | Role |
|---|---|---|
| SRAM PUF | Research/Hardware Profile | Identity evidence |
| Ring Oscillator noise | Telemetry | Entropy/health evidence |
| Intel TDX | Production candidate | Confidential execution + attestation |
| ARM TrustZone | Production candidate | Secure/Normal-world separation |
| VDF | Proof-of-sequential-work | Sequential evidence, not absolute time |
| Kalman filter | Anomaly telemetry | Not a root of trust |
| SHE | Profile/Research | Not Core |
| Garbled Circuits | Private-computation profile | Alternative to iO |
| SMPC | Advanced profile | Multi-party computation |
| ZK | Proof profile | Verifiable computation |
| FHE | Advanced research | Encrypted computation |
| Self-Healing claims | Policy/Appraisal DAG | Not claim mutation |

---

## §3. Ontological Anchoring (redefined)

Rejected definition:
> "Computation is bound to physics; forgery requires violating
> thermodynamics." — **Not defensible scientifically.**

Accepted definition:
```
Ontological Anchoring =
Binding digital state to independently evidenced physical,
hardware, temporal, and environmental state.
```

The binding is:
```
Digital State
   ├── Cryptographic Evidence
   ├── Semantic Evidence
   ├── Hardware Evidence
   ├── Temporal Evidence
   ├── Runtime Evidence
   └── External Evidence
```

The claim is never "this is reality". The claim is
"this state was produced under these evidenced conditions".

---

## §4. Hardware identity — current state and target

Current `hardware_identity.py` in the repository computes:
```
SHA-256(MAC || UUID || platform info || machine-id)
```

This is a **SoftwareFingerprint**. It is not a PUF. It must not be
described as a physical anchor.

Upgrade path:
```
SoftwareIdentity → HardwareEvidence → HardwareAttestation → OptionalPhysicalAnchor
```

Not: `SoftwareIdentity → PUF` (skips evidence collection and attestation).

---

## §5. HardwareIdentityProvider interface

```python
class HardwareIdentityProvider:
    def collect(self) -> HardwareIdentityEvidence: ...
    def verify(self, evidence) -> VerificationResult: ...
```

Implementations (added incrementally):
```
LegacySoftwareIdentity   (current)
TPMIdentity
TDXIdentity
PUFIdentity
```

Existing integrations must not break. Adapters wrap; they do not replace.

---

## §6. HardwareEvidence ≠ HardwareTruth

```
HardwareEvidence ⇒ Measured State Claim
```

Not:
```
HardwareEvidence ⇒ Truth
```

Aligned with RATS model:
- Attester produces Evidence.
- Verifier appraises.
- Relying Party decides policy.

Attestation keys and appraisal policies are themselves part of security.

---

## §7. TDX as first production path

Intel TDX is designed to protect a Trust Domain from the host VMM:
memory confidentiality, integrity, and remote attestation.

```text
ADIE Workload
      │
      ▼
TDX Trust Domain
   ├── Measurement
   ├── Key sealing
   ├── Runtime evidence
   └── Attestation quote
```

```
TDX Attestation ≠ SemanticCorrectness
Attestation + SemanticClosure + Policy = usable evidence
```

---

## §8. TrustZone

TrustZone provides Secure World / Normal World separation on suitable
hardware. It is a SoC framework, not a universal guarantee.

```text
ADIE-TEE
├── TDX Adapter
└── TrustZone Adapter
```

Interface:
```python
class TeeProvider:
    def measure(self) -> Measurement: ...
    def attest(self, nonce) -> AttestationEvidence: ...
    def seal(self, secret, policy) -> SealedBlob: ...
```

---

## §9. PUF — correct scope

PUF is suitable as **physical identity evidence**. It is not
"impossible to clone". Per ISO/IEC 20897 (still in draft revisions
in 2026), PUFs require enrollment, error correction, and fuzzy
extraction. The raw PUF response is not used as the final key.

```text
PUFResponse → ErrorCorrection → FuzzyExtractor → DeviceSecret
DeviceSecret → HardwareIdentityCommitment
```

A PUF mismatch produces `HARDWARE=FAIL`.
It does NOT automatically produce `INTEGRITY=FAIL`.

---

## §10. VDF — correct scope

VDF proves sequential work under a security model. It is not a
universal physical clock.

```text
VDF(x, T) → (y, π)
```

ADIE binds VDF seed to device identity:
```
x = H(PUFCommit || Counter || Nonce)
```

```
PUF + VDF = Identity-Bound Sequential Evidence
```

Not:
```
PUF + VDF = AbsoluteTime
```

---

## §11. Kalman filter — anomaly, not truth

Physical measurements (L3 cache latency, CPU timing, thermal response)
feed a `TelemetryState`. Kalman produces `AnomalyScore`. It does not
produce cryptographic truth.

Anomaly threshold crossing sets `hardware_health = DEGRADED`.
It does NOT set `HACKED = TRUE`.

---

## §12. Temporal Engine

```text
TemporalEngine
├── Wall Clock
├── Monotonic Counter
├── Secure Counter
├── Boot Epoch
├── Entropy Health
├── VDF Evidence
└── External Time Evidence
```

Produces:
```
T_i = (wall, mono, secure, boot, entropy, vdf, external, uncertainty)
T_R = H(T_i)
```

Offline guarantees: `Counter_{i+1} > Counter_i` (rollback detection).
It does NOT prove `wall = UTC_reality`.

---

## §13. Cryptographic stasis

Operational states:
```
NORMAL → DEGRADED → QUARANTINED → DEAD
```

In QUARANTINED:
- new issuance: blocked
- new key export: blocked
- new authority: blocked
- high-risk appraisal: blocked

In DEAD:
- issuance: OFF
- new keys: OFF
- remote updates: OFF
- historical reads: ON
- forensics: ON
- recovery: REQUIRED

No `auto_repair()`. Recovery from total compromise requires a new
key ceremony.

---

## §14. Future Key correction

Not:
```
"if compromise suspected, encrypt under the future key"
```

But:
```
EpochKey = KDF(RootSecret, Epoch, PolicyDigest)
```

derived only inside the trusted environment.

Compromise → epoch transition + new key ceremony.

---

## §15. GC before iO

For Phase 5 (private computation), the order is:
```
GC → SMPC → FHE
```

Not:
```
iO → FHE → everything
```

Garbled Circuits for two-party/private-function evaluation.
SMPC for multi-party trust.
FHE for genuinely encrypted computation at scale.
iO stays outside Core.

---

## §16. ZK ladder (unchanged from vΩ.3)

```
ZK-0  Digest equality
ZK-1  Set membership
ZK-2  Range
ZK-3  Policy execution
ZK-4  Private feature evaluation
ZK-5  Private model execution
```

Each level is independent.

---

## §17. Self-healing semantics (reaffirmed)

Rejected:
```
Claim_t → mutate itself
```

Accepted:
```
C_0 + P_t + E_t → A_t
```

Immutable claim, dynamic appraisal graph.

---

## §18. SIBB integration

SIBB already provides: hardware identity, genesis, relational memory,
distributed proof, innocence chain. ADIE does not rebuild these.

```python
class SibbAdapter:
    def append_event(self, event) -> SibbReceipt: ...
    def read_event(self, event_id) -> Event: ...
    def current_root(self) -> Digest: ...
    def verify_root(self, root) -> VerificationResult: ...
```

```
SIBB = Continuity / Evidence Substrate
ADIE = Semantic Decision Integrity
```

---

## §19. Physical evidence vector (Assurance Vector expansion)

```json
{
  "hardware": "PASS",
  "puf": "PASS",
  "tee": "PASS",
  "entropy_health": "PASS",
  "vdf": "PASS",
  "thermal_anomaly": "DEGRADED"
}
```

Shows why Assurance Vector beats Boolean.

---

## §20. Priority order (unchanged)

```
1.  META
2.  ACL
3.  Authoring
4.  ADIE/SIBB Adapter
5.  TDX
6.  Temporal Evidence
7.  PUF Profile
8.  VDF
9.  GC/SMPC
10. ZK
11. FHE
12. Recursive Continuity
```

No PUF/VDF/SMPC/FHE in Core before semantic + meta + evidence layers
are stable.

---

## §21. Final invariant

```
No physical primitive creates truth.
```

All physical layers produce **Evidence**, subject to independent
appraisal. This closes the document.

---

**End of ADIE-PHYSICAL-ANCHOR-0.1**
