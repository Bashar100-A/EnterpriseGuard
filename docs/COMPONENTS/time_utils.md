# Component: time_utils.py

**Path:** `tools/time_utils.py`
**Purpose:** Canonical UTC timestamp parsing and arithmetic.
**Status:** Working — used across governance tools.

---

## What It Does
Provides strict, timezone-aware timestamp handling.
Rejects naive timestamps and unsupported formats.

## Inputs
Timestamp strings in supported formats:
- `YYYY-MM-DDTHH:MM:SSZ`
- `YYYY-MM-DD HH:MM:SSZ`
- `YYYY-MM-DDTHH:MM:SS+00:00`
- `YYYY-MM-DD HH:MM:SS UTC`
- fallback ISO 8601

## Outputs
- `datetime` objects with UTC timezone
- `timedelta` for safe subtraction

## Key Functions
| Function | Purpose |
|----------|---------|
| `parse_utc_timestamp(s)` | Parse string into UTC datetime |
| `utc_now()` | Return current UTC datetime |
| `ensure_aware(dt)` | Normalize to aware UTC |
| `safe_subtract(a, b)` | Aware UTC subtraction |

## Security
- Prevents timezone confusion in audit logs.
- No wall-clock trust beyond parsing.

## Tests
Used by `time_drift.py`, `audit_chain.py`, and component tests.

## Used By
`audit_chain.py`, `alerts_monitor.py`, `time_drift.py`, and others.

**End of Component Doc**
