# AAAC Prototype Notes — Langfuse Integration and Chain Extension

**Date:** 2026-09-06T15:25:00Z
**Status:** Working prototype (local testing)

## Goal
Create a proof layer that pulls agent traces from Langfuse, normalizes them, stores them temporarily, and includes their hash in the innocence chain.

## Steps Completed
1. Dropped self-hosted Langfuse V3 due to ClickHouse complexity; switched to Langfuse Cloud free tier (5k traces/month).
2. Created `tools/send_test_trace.py` using REST API to send a test observation.
3. Created `tools/aaac_connector.py` to fetch observations from Langfuse v2 API, merge trace metadata, and save normalized events to `tools/ring_storage.jsonl`.
4. Modified `tools/innocence_chain.py`:
   - Added `get_last_agent_events_hash()` to compute SHA-256 of last line in ring_storage.
   - Extended `compute_ring_hash` with `agent_events_hash` parameter.
   - Updated `_verify_rings` and `generate_ring` to include the new field.
5. Reset innocence chain (old chain was incompatible) and generated new genesis ring.
6. Verified chain: `VERIFIED_OK`.

## Known Issues
- ~~`integrity_status` shows `FAIL` because baselines not regenerated after code changes.~~ **Fixed on 2026-09-06T15:23:00Z: regenerated baselines, now shows `PASS`.**
- Langfuse API v1 trace endpoint is deprecated but still working until Nov 2026.
- API keys were exposed in chat during testing; should be rotated before any real use.

## Next Steps
- Regenerate trust/integrity baselines so integrity_status becomes PASS.
- Test end-to-end: send new trace → run connector → generate ring → verify chain.
- Add sensitive data filtering (already minimal in connector).
