# Component: paths_config.py

**Path:** `tools/paths_config.py`
**Purpose:** Centralized dynamic/static path configuration.
**Status:** Working — used by most tools.

---

## What It Does
Separates runtime data, logs, and static governance files.
Supports environment overrides without changing code.

## Inputs
Environment variables:
- `ENTERPRISEGUARD_DATA_DIR`
- `ENTERPRISEGUARD_LOG_DIR`
- `ENTERPRISEGUARD_STATIC_DIR`

## Outputs
Absolute `Path` constants for:
- `ACTIVITY_LOG_PATH`
- `ERROR_LOG_PATH`
- `INNOCENCE_CHAIN_PATH`
- `RELATIONAL_MEMORY_PATH`
- `DIMENSIONAL_STATE_PATH`
- `TRUSTED_BASELINE_PATH`
- `HARDWARE_IDENTITY_PATH`
- `GENESIS_BASELINE_PATH`
- `DECISIONS_LOG_PATH`

## Key Functions
| Function | Purpose |
|----------|---------|
| `ensure_dirs()` | Create data/log/static directories |
| `validate_paths()` | Check readability/writability |

## Security
- Static governance files remain in `tools/` by default.
- Dynamic files may move to `/var/lib/enterpriseguard`.
- No secrets are stored here.

## Tests
Used indirectly by all component tests.

## Used By
Most `tools/*.py` modules.

**End of Component Doc**
