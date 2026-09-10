# Component: sibb_storage.py

**Path:** `tools/sibb_storage.py`
**Version:** 7.3
**Purpose:** Immutable WORM storage with AES-GCM encryption + HMAC.
**Status:** Working (21/21 tests passed)

---

## What It Does

Cross-platform WORM (Write Once, Read Many) storage engine.
Enforces immutability at the OS level (chattr +i on Linux,
chflags uchg on macOS, FILE_ATTRIBUTE_READONLY on Windows).
Supports optional AES-GCM encryption with per-file keys.

## Inputs

- file data (bytes)
- filename (string)
- optional metadata (dict)

## Outputs

- tools/sibb_store/<filename> (chmod 0444)
- tools/sibb_store/.worm_metadata.json (chmod 0600)
- tools/sibb_store/.worm_metadata.hmac (chmod 0600)
- tools/sibb_store/.worm_metadata.backup.json
- tools/sibb_store/.worm_metadata.hmac.backup

## Key Features

| Feature | Description |
|---------|-------------|
| WORM | Exclusive file creation, no overwrite |
| Encryption | AES-GCM (optional), per-file keys via HKDF |
| HMAC | Metadata integrity with independent key |
| Path Safety | resolve() + relative_to() + O_NOFOLLOW |
| Atomic Writes | tempfile + os.replace |
| Full I/O Loops | Handles partial reads/writes |
| Orphan Handling | Optional (opt-in) |

## Security

- File permissions: 0444 for data, 0600 for metadata
- Salt file: .worm_salt.bin (chmod 0600)
- HMAC key: outside storage (default ~/.enterpriseguard/keys/)
- No overwrite even by root (except with CAP_LINUX_IMMUTABLE)
- Constant-time comparison for HMAC
- Metadata refresh from disk before every operation

## Tests

- tests/test_sibb_storage.py (21 tests, passing)

## Used By

- sibb_distributed.py
- sibb_cli.py
- sibb_innocence_integration.py

**End of Component Doc (part 1/3)**
