# Component: aaac_connector.py

**Path:** `tools/aaac_connector.py`
**Purpose:** Fetch Langfuse observations into unified AAAC events.
**Status:** Working prototype — Langfuse v2 API.

---

## What It Does
Loads `.env`, fetches recent observations, merges trace data,
normalizes events, skips duplicates, and appends to `ring_storage.jsonl`.

## Inputs
`.env`:
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_BASE_URL`

## Outputs
- `tools/ring_storage.jsonl` append-only events

## Key Functions
| Function | Purpose |
|----------|---------|
| `load_env()` | Read `.env` safely |
| `fetch_observations()` | Fetch Langfuse v2 observations |
| `fetch_trace()` | Fetch trace metadata |
| `normalize_observation()` | Convert to AAAC event |
| `load_existing_trace_ids()` | Deduplicate |
| `save_event_to_ring_storage()` | Atomic JSONL append |

## Security
- Sanitizes API keys/passwords/tokens in summaries.
- Uses env for secrets.
- No shell execution.

## Tests
Used indirectly by `aaac_cli.py`.

## Used By
`tools/aaac_cli.py`.

**End of Component Doc**
