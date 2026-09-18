# DC-138: Defer B1.10 Top-Level Export

**Date:** 2026-09-18
**Owner:** Biss
**Status:** APPROVED
**Related:** DC-137 (SDK signing module)

## Context

After B1.9a/B1.9b, B1.10 was defined as adding a top-level export:

    from enterpriseguard import sign_bytes

Investigation found:
- src/enterpriseguard/ does not contain __init__.py (namespace package)
- All subpackages contain __init__.py (regular packages inside a namespace)
- Root enterpriseguard/__init__.py exists (compatibility boundary, 587 bytes)
- Current working form: from enterpriseguard.signing import sign_bytes

## Decision

Do NOT add a top-level export at this time.

Reasons:
1. The SDK is usable today via from enterpriseguard.signing import ...
2. Top-level export is cosmetic; it does not unlock any new capability.
3. Adding src/enterpriseguard/__init__.py could interfere with the
   namespace merging between root and src trees (P0.9-C compatibility).
4. If a top-level export is added later, the natural place is the root
   enterpriseguard/__init__.py (already exists) — not a new src file.

## Consequences

- The public SDK import path is fixed as:
    from enterpriseguard.signing import sign_bytes, verify_signature_hex
- This is documented as the official import path in the SDK docs (Phase A A1 component doc).

## Deferred to B1.11

The real Phase B target is not import cosmetics but the SDK Client:
    client = Client()
    decision = client.create_decision(...)
    decision.sign()

This is B1.11 and beyond.

**Approved by:** Biss (Owner)
**Effective:** 2026-09-18
