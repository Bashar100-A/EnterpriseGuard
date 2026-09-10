# Component: sibb_keys.py

**Path:** `tools/sibb_keys.py`
**Version:** 1.0.3
**Purpose:** Shamir Secret Sharing + AES-GCM for master key management.
**Status:** Working (29/29 tests passed)

---

## What It Does

Manages the master cryptographic key using Shamir Secret Sharing.
Splits master key into N shares (default 5), requiring K shares (default 3)
to reconstruct. Each share is encrypted at rest with AES-GCM.
HMAC-SHA256 protects integrity with an independent random key.

## Inputs

- master_password (>=12 chars)
- master_key (32 bytes) — generated internally
- N, K parameters (default 5, 3)

## Outputs

- tools/shares/<key_id>_<n>.share (chmod 0600)
- ~/.enterpriseguard/keys/sibb_hmac_key.bin (chmod 0600)

## Key Functions

| Function | Purpose |
|----------|---------|
| generate_master_key() | Generate 32-byte random key |
| split_master_key() | Split into N encrypted shares |
| reconstruct_key() | Reconstruct from K shares |
| verify_share() | Check share integrity |
| delete_share() | Secure delete |
| list_shares() | List all shares |
| get_status() | Return manager status |

## Shamir Implementation

- Prime: 2^256 - 189 (safe prime)
- Polynomial: degree K-1 with random coefficients
- Interpolation: Lagrange at x=0
- Shares: points (x, y) where x = 1..N

## Encryption

- Per-share random 16-byte salt
- File key derived via HKDF from password_key
- AES-GCM with random 12-byte nonce
- HMAC-SHA256 over full share structure

## Share File Structure

    {
      "key_id": "...",
      "share_id": "...",
      "master_salt": "<base64>",
      "salt": "<base64>",
      "nonce": "<base64>",
      "ciphertext": "<base64>",
      "n": 5,
      "k": 3
    }
    <newline>
    <base64 HMAC>

## Security

- Shares never stored in plaintext
- HMAC key independent from master key
- Lockout: 5 failed attempts -> 30s lockout
- Constant-time comparison for HMAC
- Secure deletion: overwrite with zeros

## Tests

- tests/test_sibb_keys.py (29 tests, passing)

## Used By

- sibb_cli.py (split-key, reconstruct-key commands)
- Potentially: sibb_storage.py (for HMAC key management)

**End of Component Doc**
