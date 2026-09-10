# Component: signing_backend.py

**Path:** `tools/signing_backend.py`
**Purpose:** Pluggable cryptographic signing backend.
**Status:** Working (used by innocence_chain.py)

---

## What It Does

Provides a unified signing interface with multiple backends,
controlled by the AAAC_SIGNING_BACKEND environment variable.

Supported backends:
- local (default): RSA-2048 or ECDSA P-256 via OpenSSL
- ecdsa_local: ECDSA P-256 (faster, smaller signatures)
- mock: SHA-256 based (tests only)
- aws_kms: AWS Key Management Service (dormant, needs credentials)
- azure_kv: Azure Key Vault (dormant, needs credentials)
- tpm: Trusted Platform Module (dormant, needs hardware)

## Inputs

- data (bytes or hex string)
- backend selection via env var

## Outputs

- signature (hex string)
- verification result (bool)

## Key Functions

| Function | Purpose |
|----------|---------|
| sign_bytes(data) | Sign bytes with active backend |
| verify_signature_hex(data, sig_hex) | Verify signature |
| sign_genesis_chain_id_hex(chain_id) | Sign genesis chain ID |
| verify_genesis_signature_hex(chain_id, sig_hex) | Verify genesis sig |

## Backend Selection

    AAAC_SIGNING_BACKEND=local       # default, RSA-2048
    AAAC_SIGNING_BACKEND=ecdsa_local # ECDSA P-256 (faster)
    AAAC_SIGNING_BACKEND=mock        # for tests only
    AAAC_SIGNING_BACKEND=aws_kms     # dormant
    AAAC_SIGNING_BACKEND=azure_kv    # dormant
    AAAC_SIGNING_BACKEND=tpm         # dormant

## Performance

From DC-118 benchmark:
- RSA-2048:   320.61 ms/sig
- ECDSA P-256:   0.67 ms/sig
- Improvement: 99.8%

## Key Management

- Private keys: ~/.enterpriseguard/keys/private_key.pem (0600)
- Public keys:  ~/.enterpriseguard/keys/public_key.pem (0644)
- Genesis keys: separate pair in same directory
- No keys in repository

## Security

- OpenSSL used for RSA (subprocess, no shell)
- cryptography library used for ECDSA
- Constant-time comparison for verification
- Environment variable only for backend selection
- No fallback to insecure algorithms

## Tests

- tools/test_signing_backend.py (mock + local modes)
- Used by test_innocence_chain.py (signing backend tests)

## Used By

- innocence_chain.py (primary signing engine)
- Potentially: any component needing signatures

**End of Component Doc**
