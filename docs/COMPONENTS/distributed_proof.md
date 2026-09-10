# Component: distributed_proof.py

**Path:** `tools/distributed_proof.py`
**Purpose:** Participatory proof - no single witness can prove the system.
**Status:** Working (9/9 tests passed)

---

## What It Does

Splits a proof digest into 3 shards (local, external, physical).
All 3 shards must be present to reconstruct the proof.
Prevents single-authority trust.

## Inputs

- identity_key (from hardware_identity.json)
- genesis_hash (from genesis_baseline.json)
- last_relational_node (from relational_memory.json)

## Outputs

- tools/proof_shard_local.json (chmod 0600)
- tools/proof_shard_external.json (private Git or local encrypted fallback)
- tools/proof_shard_physical.json (chmod 0400)

## Key Functions

| Function | Purpose |
|----------|---------|
| generate_proof_digest() | sha256(identity + genesis + last_node + utc) |
| split_digest() | Split into 3 equal shards |
| reconstruct_digest() | Combine shards to recover digest |

## Security

- Missing any shard -> reconstruction fails
- External shard must never be public
- Physical shard: chmod 0400 (owner read only)

## Tests

- tests/test_distributed_proof.py (9 tests, passing)

## Used By

- innocence_chain.py (optional anchoring)

**End of Component Doc**
