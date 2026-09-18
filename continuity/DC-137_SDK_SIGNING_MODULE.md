# DC-137: SDK Signing Module — Independent Design (v2)

**Date:** 2026-09-18
**Owner:** Biss
**Status:** APPROVED
**Predecessor:** B1.8 audit (PASS, 2026-09-18)
**Supersedes:** DC-137 v1 (rejected after critical review)

## Context

B1.8 audit found that tools.signing_backend is referenced by:
- tools/innocence_chain.py:49 (runtime import)
- scripts/benchmarks/benchmark_signing.py (legacy)
- scripts/legacy_patches/*.py (legacy; found via grep, not part of B1.8
  scope because B1.8 explicitly excluded this path)

B1.8 also confirmed:
- tools/__init__.py does not exist (tools/ is not a Python package)
- pyproject.toml packages only enterpriseguard.* from src/

A first design (v1) proposed extracting tools/signing_backend.py to
src/enterpriseguard/signing/. This design was rejected after critical
review identified 4 blocking issues:

- C1: Path(__file__).parent.parent changes meaning after move.
- C2: tools/innocence_chain.py would fail direct execution.
- C3: root/enterpriseguard vs src/enterpriseguard namespace merge.
- C4: the compatibility shim would fail in the very case it exists for.

## Decision

Do NOT extract tools/signing_backend.py.

Instead, build a fresh, minimal signing module inside the SDK:

  src/enterpriseguard/signing/
      __init__.py    (public API re-exports)
      backend.py     (implementation)

## Public API (v1)

Two functions, both keyword-only for future extensibility:

    def sign_bytes(
        data: str,
        *,
        backend: str = "rsa_local",
        key_dir: Path | None = None,
    ) -> str: ...

    def verify_signature_hex(
        data: str,
        signature_hex: str,
        *,
        backend: str = "rsa_local",
        key_dir: Path | None = None,
    ) -> bool: ...

`key_dir` defaults to `Path.home() / ".enterpriseguard" / "keys"`. It is
exposed explicitly so tests and containerized deployments can supply a
different directory without monkeypatching.

## Backends (v1)

- `rsa_local`:   RSA-2048, SHA-256, PKCS1v15
- `ecdsa_local`: ECDSA P-256, SHA-256

Key paths, relative to `key_dir`:
- RSA private:    private_key.pem
- RSA public:     public_key.pem
- ECDSA private:  ecdsa/private_key.pem
- ECDSA public:   ecdsa/public_key.pem

## Error Handling

- `sign_bytes` raises `SigningKeyNotFoundError` (subclass of RuntimeError)
  if the private key file is missing.
- `sign_bytes` raises `SigningKeyInvalidError` (subclass of RuntimeError)
  if the private key file exists but cannot be loaded.
- `sign_bytes` raises `ValueError` for an unknown `backend`.
- `verify_signature_hex` returns False (never raises) on:
  - missing public key
  - malformed public key
  - malformed hex signature
  - signature that fails verification
- `verify_signature_hex` raises `ValueError` only for an unknown `backend`.

## Non-goals (v1)

- No genesis signing (tools/-internal concern only).
- No KMS/TPM/Azure (deferred to v2).
- No mock mode (test-only; use key_dir with test keys).
- SDK does NOT read AAAC_SIGNING_BACKEND. This environment variable has
  no effect on SDK behavior. The separation between tools/ (CLI-oriented,
  env-var driven) and SDK (library-oriented, parameter driven) is
  intentional and must remain.

## Rationale for non-extraction

tools/signing_backend.py and the new SDK module have:
- Different import paths.
- Different audiences (CLI operator vs SDK developer).
- Different constraints (tools/ needs genesis keys; SDK does not).
- Different lifecycles (repo layout vs version).

This is layering, not duplication. The 4 critical issues above all stem
from attempting to reuse a tools/ module inside the SDK. Building fresh
eliminates them by construction.

## Consequences

- ~60-80 lines of overlapping crypto logic between tools/ and SDK.
  Accepted as the cost of clean separation.
- tools/ untouched -> zero regression risk.
- tools/innocence_chain.py unchanged.
- pyproject.toml: add the new package to the explicit include list.
- VERSION bump: 0.2.0 -> 0.3.0 (public API addition; SemVer MINOR).

## Pre-execution check

Before adding the package, verify setuptools resolves it correctly:

    python3 -c "from setuptools import find_packages; \
      print('enterpriseguard.signing' in find_packages(where='src', \
      include=['enterpriseguard.signing','enterpriseguard.signing.*'], \
      exclude=['enterpriseguard.adie','enterpriseguard.adie.*',\
      'enterpriseguard.intelligence','enterpriseguard.intelligence.*']))"

Expected: True

## pyproject.toml change

Under [tool.setuptools.packages.find] include, add (alphabetical order
near the other enterpriseguard entries):

    "enterpriseguard.signing",
    "enterpriseguard.signing.*",

The exclude list is unchanged; the new patterns do not overlap with it.

## Verification

New test file: tests/test_sdk_signing.py

Required scenarios:
1. RSA round-trip: sign_bytes(data, key_dir=tmp) -> hex; verify returns True.
2. ECDSA round-trip: same with backend="ecdsa_local".
3. Tampered data: verify(data + "x", sig) returns False (no exception).
4. Tampered signature: verify(data, corrupted_hex) returns False.
5. Missing key: sign_bytes raises SigningKeyNotFoundError.
6. Unknown backend: sign_bytes raises ValueError.
7. Explicit key_dir isolation: tests never touch ~/.enterpriseguard/.

Isolated install test (manual, one-time):

    pip install -e .
    python -c "from enterpriseguard.signing import sign_bytes, verify_signature_hex; print('OK')"

tools/ regression (must remain unchanged):

    python3 tools/open_verifier.py

## Timeline

- B1.9a (this decision): create src/enterpriseguard/signing/ with
  __init__.py + backend.py; add pyproject include; bump VERSION.
- B1.9b: add tests/test_sdk_signing.py; run all seven scenarios.
- B1.10: expose signing at the SDK top level
  (from enterpriseguard import sign_bytes).

## Rollback

Single commit. Revert with `git revert <commit>`.

## References

- B1.8 audit (this session)
- docs/EXECUTION_PLAN.md Section 13 (Key Management)
- docs/EXECUTION_PLAN.md Section 5 (cryptography allowed)
- continuity/DC-136_PHASE_B_INITIATION.md
- Critical review of DC-137 v1 (2026-09-18)

**Approved by:** Biss (Owner)
**Effective:** 2026-09-18
