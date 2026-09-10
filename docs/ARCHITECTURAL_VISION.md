```markdown
# EnterpriseGuard ADIE — Architectural Vision

**Version:** 0.2.0  
**Date:** 2026-09-01  
**Status:** Authoritative Reference  
**Governed by:** DC-043

---

## 0. Preamble

EnterpriseGuard ADIE is not a collection of security tools.  
It is a **Sovereign Reference Core** — a self-verifying, self-evolving,
tamper-evident decision core that refuses to trust its own existence
without proof.

This document defines the philosophical foundation and the five
components that materialize that philosophy into executable Python
modules.

> **Note:** Technical details in this document (node counts, intervals,
> exact file names) are authoritative but modifiable during
> implementation. This document will be updated after each phase.

---

## 1. Sovereign Reference Core

The Sovereign Reference Core is the ultimate source of truth for
proving that ADIE:

- Was not created from nothing.
- Runs on the same hardware that generated its identity.
- Remembers its past without retaining every detail.
- Cannot be witnessed by a single authority alone.
- Constantly regenerates proof of its own integrity.

This is not a "feature". It is the definition of the product.

---

## 2. The Five Components

| # | Component | Purpose |
|---|-----------|---------|
| 1 | `hardware_identity.py` | Tissue Identity — prevents cloning |
| 2 | `genesis_seed.py` | Inherited Proof — proves origin |
| 3 | `relational_memory.py` | Associative Memory — forgets without denial |
| 4 | `distributed_proof.py` | Participatory Proof — no single witness |
| 5 | `innocence_chain.py` | Renewed Innocence — continuous proof |

Each component is standalone, but together they form a closed proof cycle.

---

## 3. Component Details

### 3.1 `hardware_identity.py`

Generates an `identity_key` from multiple hardware fingerprints:

- `uuid.getnode()`
- `platform.processor()`
- `platform.machine()`
- `os.cpu_count()`
- `systemd-machine-id` if available

The key is stored in `tools/hardware_identity.json` with `chmod 600`.

**Rule:** Changing any fingerprint changes the identity.  
Regeneration requires explicit owner authorization and is logged in
`DECISIONS_LOG.md`.

---

### 3.2 `genesis_seed.py`

Generates `genesis_hash` from:

`sha256(external_seed + identity_key + utc_now())`

Where:
- `external_seed` comes from `genesis_seed.txt`, Git HEAD, or manual CLI.
- `identity_key` is the hardware identity from `hardware_identity.py`.

This binds origin to hardware. Without the same hardware identity,
the genesis proof cannot be reproduced.

**Rule:** Same seed + same hardware gives same hash.  
Output is `tools/genesis_baseline.json` with `chmod 444`.

---

### 3.3 `relational_memory.py`

Stores associative nodes:

```
{
  "event_id": "...",
  "prev_event": "...",
  "next_event": "...",
  "cause": "...",
  "effect": "...",
  "timestamp": "..."
}
```

Memory lives in `tools/relational_memory.json` with `chmod 600`.

**Rule:** Events can be archived, but their relational nodes remain.
This is "forgetting without denial."

Rotation policy: max 1000 nodes, then oldest 500 are compressed to
`tools/relational_memory_archive.json.gz`.

---

### 3.4 `distributed_proof.py`

Generates proof by hashing:

`sha256(identity_key + genesis_hash + last_relational_node + utc_now())`

Then splits the digest into three shards:

- `tools/proof_shard_local.json` — `chmod 600`
- `tools/proof_shard_external.json` — stored in a **private** Git repository, or local encrypted fallback in air-gapped environments
- `tools/proof_shard_physical.json` — `chmod 400`

**Rule:** Missing any shard means proof reconstruction fails.  
The external shard must never be stored in a public repository or
transmitted unencrypted.

---

### 3.5 `innocence_chain.py`

Generates a ring every configurable interval (default 300 seconds).

Each ring contains:

- `ring_hash`
- `relational_memory_snapshot`
- `integrity_status`

Stored in `tools/innocence_chain.json` with `chmod 444`.

**Rule:** Modifying any old ring breaks all subsequent rings.

---

## 4. Proof Cycle

```
Hardware Identity
      ↓
Genesis Seed
      ↓
Relational Memory
      ↓
Distributed Proof
      ↓
Innocence Chain
      ↓
   (loop)
```

Every component feeds the next. No component can be forged alone.

---

## 5. Cross-Cutting Audit Layer

`audit_chain.py` is the transverse logging layer that records every
critical event in the proof cycle. It is not one of the five components,
but it binds them together.

Each component must write to `activity_log.json` via `append_activity`
after every successful operation.

---

## 6. Protection Invariants

- `adie/` and `intelligence/` are never read or modified.
- All writes are atomic (`tempfile.mkstemp` + `os.replace`).
- `PYTHONDONTWRITEBYTECODE=1` and `sys.dont_write_bytecode = True` are mandatory.
- Every new file is immediately added to baselines.
- Every governance action is logged in `DECISIONS_LOG.md` and `activity_log.json`.
- No automatic activation without owner approval.
- The external proof shard is private or encrypted, never public.

---

## 7. Conclusion

The Sovereign Reference Core is the highest expression of ADIE's
philosophy:

> **A system that does not trust its own existence is the only system
> that can be trusted by others.**

---

**End of Architectural Vision.**
```