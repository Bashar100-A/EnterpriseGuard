# Component: innocence_chain.py

**Path:** `tools/innocence_chain.py`
**Purpose:** Continuous proof - regenerates integrity evidence over time.
**Status:** Working (13/13 tests passed)

---

## What It Does

Generates a chain of proof rings. Each ring contains:
- ring_hash = sha256(prev_ring_hash + identity + integrity_status + snapshot)
- relational_memory_snapshot (last event_id)
- integrity_status (PASS/FAIL)
- realtime_events_hash
- agent_events_hash
- rfc3161_token (TSA timestamp)
- signature (RSA/ECDSA)
- chain_id (UUID, first ring only)

Modifying any old ring breaks all subsequent rings.

## Inputs

- identity_key (from hardware_identity.json)
- integrity_status (from integrity_monitor.py)
- relational_memory snapshot
- realtime_events_hash
- agent_events_hash

## Outputs

- tools/innocence_chain.json (chmod 0444)

## Key Functions

| Function | Purpose |
|----------|---------|
| generate_ring() | Create a new proof ring |
| verify_chain() | Verify entire chain integrity |
| load_chain() | Read chain from disk |
| save_chain() | Atomic save with 0444 |
| sign_ring_hash() | RSA/ECDSA sign ring hash |
| verify_ring_signature() | Verify ring signature |
| get_chain_status() | Return VALID/TAMPERED/CORRUPT/MISSING |

## Security

- File permissions: 0444 (read-only)
- Chain spoofing mitigated via RSA-2048/ECDSA signatures
- Hard fork mitigated via genesis_signature + chain_id
- RFC3161 timestamp anchored via TSA (Certum/FreeTSA/DFN)
- Optional blockchain anchoring (Sepolia testnet)

## Tests

- tests/test_innocence_chain.py (13 tests, passing)

## Used By

- sibb_innocence_integration.py

**End of Component Doc**
