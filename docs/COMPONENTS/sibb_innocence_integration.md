# Component: sibb_innocence_integration.py

**Path:** `tools/sibb_innocence_integration.py`
**Version:** 1.3
**Purpose:** Integrate SIBB storage with innocence chain rings.
**Status:** Working (15/15 tests passed)

---

## What It Does

Stores innocence chain rings in SIBB storage with:
- Chain continuity enforcement (prev_ring_hash)
- Signature verification (RSA-SHA256)
- Encryption support (AES-GCM via SIBB)
- WORM integration
- Audit logging

## Inputs

- ring_data (dict): ring with hash, signature, prev_ring_hash, chain_id
- ring_id (string): unique identifier
- config (dict): storage paths, public key, encryption settings
- password (optional): for encrypted storage

## Outputs

- tools/sibb_store/<ring_id>.ring
- Chain head state in ~/.enterpriseguard/state/chain_head.json
- Audit events in activity log

## Key Functions

| Function | Purpose |
|----------|---------|
| validate_ring_id() | Pattern check (alphanumeric, _, -) |
| verify_ring_signature() | RSA-SHA256 verification |
| compute_ring_hash() | SHA-256 of ring (excl. signature) |
| load_chain_head() | Read chain head state |
| save_chain_head() | Save with HMAC protection |
| get_storage_backend() | Return WORM or Distributed storage |
| store_ring() | Store a ring (with locks) |
| retrieve_ring() | Retrieve + verify |
| verify_stored_rings() | Full chain verification |

## Chain Continuity Rules

- First ring: prev_ring_hash must be None or "genesis"
- Subsequent rings: prev_ring_hash must equal current chain head
- chain_id must match across all rings
- Any violation -> store rejected

## Security

- Ring ID pattern: ^[A-Za-z0-9_-]{1,64}$
- MAX_RING_SIZE = 1 MB
- File lock around read-verify-write (prevents race)
- Chain head HMAC-protected (state_hmac_key.bin)
- Signature verified BEFORE storage
- Signature verified AFTER retrieval
- Hash mismatch -> reject

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| Invalid signature | Reject storage |
| Hash mismatch | Reject storage |
| Chain continuity break | Reject storage |
| Encryption failure | Reject storage |
| Ring size > 1MB | Reject storage |

## Tests

- tests/test_sibb_innocence_integration.py (15 tests, passing)

## Used By

- sibb_cli.py (indirectly)
- Future: HTTP API for ring storage

**End of Component Doc**
