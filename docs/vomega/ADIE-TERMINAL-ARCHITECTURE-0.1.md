# ADIE — Terminal Architecture (North Star)

**Document:** ADIE-TERMINAL-ARCHITECTURE-0.1
**Status:** NON-NORMATIVE — North Star only
**Date:** 2026-10-06
**Authority:** DECISIONS-0.1
**Applies to:** Phase 2 through Phase 6 (design reference)

---

## §0. Standing

This document describes the **target** architecture ADIE-vΩ aims toward.
It has no normative authority over the current implementation.

```
This document:
  - describes future layers
  - does NOT cancel any invariant in META-CONTRACT-0.1
  - does NOT redefine any error code in ERROR-REGISTRY-0.1
  - does NOT fix wire format (deferred to Phase 2)
  - does NOT authorize ZK/FHE/TEE/IVC/iO in the current verifier
```

Cross-references:

- [META-CONTRACT-0.1](./META-CONTRACT-0.1.md) — normative
- [ERROR-REGISTRY-0.1](./ERROR-REGISTRY-0.1.md) — normative (index)
- [DECISIONS-0.1](./decisions/DECISIONS-0.1.md) — binding decisions

---

## §1. Cryptographic & Physical Paradigm

**Status:** design reference — not normative for Phase 1
**Topics:**
- Conditional security theorem `Security(ADIE) | Assumptions A`
- "DO NOT CLAIM SUCCESS" on total compromise
- Semantic Authority Drift
- State tensor (M, G, L, C, P, X, E, Q, R)
- Domain-separated hash algebra (`ADIE/vOmega/physical/`)
- Proof-carrying semantic equivalence
- Physical entropy paradigm
- Thermodynamic non-theorem
- Multi-anchor temporal evidence
- Hybrid signature algebra (RS256 + ML-DSA-65)
- Blind computation paradigm (FHE + ZK + TEE)
- iO as research profile
- Recursive proof model
- Dead state and recovery
- Zero-leakage containment

Full content to be re-committed from session record. Until then, this
section is a **table of contents**.

---

## §2. Wire Format Topology

**Status:** NON-NORMATIVE — design only
**Implementation:** deferred to Phase 2 (`ADIE-WIRE-0.1`)

Topics (all non-normative):
- Protocol stack L0–L7
- Transport envelope (fixed binary framing)
- Section directory
- Canonical CBOR rules
- Claim map
- Binding wire object
- Purpose registry
- Evidence object
- Independence graph
- Proof envelope
- Signature envelope
- Manifest wire format
- Root set
- Governance event
- Registry entry
- Compatibility object
- Authoring closure
- Parameter encoding
- Model weight root
- Provenance binding
- Recursive state
- Transparency log
- Privacy object
- Usage receipt

Full content to be re-committed from session record.

---

## §3. Hyper-Adversarial Fail-Closed Matrix

**Status:** non-normative — the current normative suite remains
`tests/vomega/meta/run_all.py` (M01–M40) plus `tests/vomega/run_all.py`
(ATTACK-001..012).

Future attack families (see DECISIONS-0.1 §2):

| Family | Namespace |
|---|---|
| Meta-layer | META-M01..M40 (frozen) |
| Core | CORE-C01.. |
| Semantic | SEM-S01.. |
| Binding | BIND-B01.. |
| Temporal | TIME-T01.. |
| Evidence | EVID-E01.. |
| Privacy | PRIV-P01.. |
| FHE | FHE-F01.. |
| ZK | ZK-Z01.. |
| TEE | TEE-H01.. |
| Recursive | RECUR-R01.. |
| Transparency | LOG-L01.. |

Full content to be re-committed from session record.

---

## §4. Naming corrections

The phrase "actual planet-scale architecture" is replaced with
**Target Planet-Scale Architecture**. Rationale in DECISIONS-0.1.

---

## §5. Amendment

This document is **append-only** for §1–§3.
Any change:
- uses a new version (0.2, 0.3, …)
- is committed on `vOmega`
- does not modify META-CONTRACT-0.1, ACL, ERROR-REGISTRY, or frozen tests

---

**End of ADIE-TERMINAL-ARCHITECTURE-0.1 (stub)**
