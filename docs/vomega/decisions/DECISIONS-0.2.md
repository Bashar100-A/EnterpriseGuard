# ADIE vΩ — Decision Record 0.2

**Date:** 2026-10-06
**Authority:** Project Lead
**Status:** Binding
**Extends:** DECISIONS-0.1

---

## Preamble

This record formalizes the incorporation of the Physical Anchor
supplement as a NON-NORMATIVE North Star document, and clarifies
several primitive classifications.

---

## Decision 1 — Physical Anchor document

**Choice:** Accept `ADIE-PHYSICAL-ANCHOR-0.1.md` as NON-NORMATIVE
North Star supplement.

**Constraints:**
- Does not modify META-CONTRACT-0.1
- Does not modify ACL-0.1
- Does not modify AUTHORING-0.1
- Does not modify REGISTRY-0.1
- Does not modify ERROR-REGISTRY-0.1
- Does not modify any existing test vector

---

## Decision 2 — Primitive classifications

| Primitive | Classification |
|---|---|
| PUF | Physical Identity Evidence (not "impossible to clone") |
| VDF | Sequential Work Evidence (not "absolute time") |
| TEE (TDX/TrustZone) | Hardware Execution Evidence (not trust root) |
| Kalman filter | AnomalyScore (not CryptographicTruth) |
| iO | Research Profile (not Core) |
| GC | Private Function Evaluation (Phase 5 entry) |
| SMPC | Multi-party computation profile |
| FHE | Encrypted computation profile |
| ZK | Proof profile |
| SIBB | Continuity / Evidence Substrate |

---

## Decision 3 — hardware_identity.py clarification

Current implementation computes SHA-256 over MAC/UUID/platform/machine-id.
This is a **SoftwareFingerprint**, NOT a PUF.

The upgrade path is:
```
SoftwareIdentity → HardwareEvidence → HardwareAttestation → OptionalPhysicalAnchor
```

Do NOT describe the current implementation as a physical anchor in any
document, commit message, or external communication.

---

## Decision 4 — Layer-2 definition

ADIE Layer-2 = Integrity/Attestation Overlay.
It is NOT a blockchain, NOT a state channel, NOT a consensus layer.

---

## Decision 5 — Order of physical primitives

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

No physical primitive enters Core before semantic + meta + evidence
layers are stable.

---

## Decision 6 — TDX as first production path

TDX precedes PUF/VDF/GC/SMPC/FHE in implementation order.

Rationale: TDX has mature documentation (Intel, 2026) and produces
attestation quotes that map directly to RATS-style evidence.
PUF requires hardware boards and enrollment infrastructure;
its evaluation methodology is still in draft revisions (ISO/IEC 20897).

---

## Decision 7 — Ontological Anchoring redefined

Rejected:
> Binding to physics prevents forgery by thermodynamic law.

Accepted:
```
Ontological Anchoring =
Binding digital state to independently evidenced physical,
hardware, temporal, and environmental state.
```

No claim that digital evidence becomes reality.

---

## Decision 8 — Assurance Vector expansion

Physical dimensions may be added to the Assurance Vector in Phase 2:
```
hardware, puf, tee, entropy_health, vdf, thermal_anomaly
```
Each with values `PASS | FAIL | UNKNOWN | STALE | DEGRADED | CONFLICT`.

---

## Decision 9 — VDF + PUF relationship

```
PUF + VDF = Identity-Bound Sequential Evidence
```

Not:
```
PUF + VDF = AbsoluteTime
```

---

## Decision 10 — Future Key correction

Not:
```
new_key = random()
```

But:
```
EpochKey = KDF(RootSecret, Epoch, PolicyDigest)
```

Derived only inside the trusted environment. Compromise → epoch
transition + new key ceremony.

---

## Prohibitions effective immediately

1. Describing `hardware_identity.py` as a PUF.
2. Using PUF/VDF/SMPC/FHE in Core before evidence layers are stable.
3. Claiming "absolute time" from entropy sources.
4. Claiming "impossible to clone" for any PUF.
5. Using "TEE = root of truth" in any document.
6. Presenting Kalman output as cryptographic truth.
7. Running `auto_repair()` after total compromise.

---

**End of DECISIONS-0.2**
