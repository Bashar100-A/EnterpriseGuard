# DC-140: HTTP API Design (B2)

**Date:** 2026-09-18
**Owner:** Biss
**Status:** APPROVED
**Predecessor:** B1.11 (SDK Client, commit ec7203a)

## Context

Phase B task B2 (EXECUTION_PLAN Section 3):
> HTTP API — /v1/decisions, /v1/verify — Works with curl + TSA failover per Section 14

Investigation:
- tools/sovereign_http_server.py exists (215 lines, GET-only, X-ADIE-Key auth,
  state inspection: /health, /dimensions, /verify-chain, /agents, /events)
- It is a state-inspection tool, not a decision API.
- FastAPI is not installed.
- EXECUTION_PLAN Section 5 allows "FastAPI (or http.server stdlib)".

## Decision

Build a new HTTP API inside the canonical package:

    src/enterpriseguard/api/
        __init__.py    (re-exports)
        server.py      (implementation)

## Owner Decisions (2026-09-18)

- Q1: location = src/enterpriseguard/api/ (canonical)
- Q2: framework = http.server stdlib (no new dependency)
- Q3: auth = X-ADIE-Key header (consistent with sovereign_http_server)
- Q4: storage = JSONL append (Section 15 Tier 1)
- Q5: TSA = deferred to v2 (Section 14 complexity)
- Q6: endpoints v1 = /v1/health, /v1/decisions, /v1/verify

## Scope (v1)

### Endpoint: GET /v1/health
    Returns: {"status": "ok", "version": "0.5.0"}
    Auth: not required

### Endpoint: POST /v1/decisions
    Request JSON:
        {"target": "host-01", "intent": "isolate",
         "policy_id": "default", "parameters": {}}
    Response JSON:
        {"contract": {...}, "signature_hex": "...",
         "signed_at": "...", "backend": "rsa_local",
         "signed_payload_hash": "..."}
    Auth: X-ADIE-Key required
    Side effect: append record to decisions-YYYY-MM-DD.jsonl

### Endpoint: POST /v1/verify
    Request JSON:
        {"contract": {...}, "signature_hex": "...",
         "signed_at": "...", "backend": "rsa_local",
         "signed_payload_hash": "..."}
    Response JSON:
        {"valid": true|false}
    Auth: X-ADIE-Key required
    Side effect: none (read-only)

## Storage layout

    data/
      decisions-YYYY-MM-DD.jsonl    (append-only, one JSON per line)

Default data directory: ~/.enterpriseguard/api/ (configurable via env
AAAC_API_DATA_DIR). Tests use a tmp dir.

## Auth

Header: X-ADIE-Key: <token>
Expected token: env var AAAC_API_KEY.
If AAAC_API_KEY is unset:
  - /v1/health is public
  - other endpoints respond 503 (service unavailable, no key configured)
No password hashing in v1; constant-time comparison required.

## Non-goals (v1)

- No TSA / RFC3161 (deferred v2, Section 14)
- No HTTPS (localhost only in v1)
- No rate limiting (deferred to v2)
- No multi-tenant isolation
- No async / concurrency beyond ThreadingHTTPServer
- No storage rotation / archival
- No dashboard / UI (that is B3)

## Reuse

- Client from enterpriseguard.sdk (create_decision, sign, verify)
- http.server.ThreadingHTTPServer from stdlib
- JSON I/O from stdlib

## VERSION

0.4.0 -> 0.5.0 (SemVer MINOR for new public API surface)

## Verification plan

tests/test_api_server.py — scenarios:
1. GET /v1/health returns 200, no auth
2. POST /v1/decisions without key -> 401 (when key configured)
3. POST /v1/decisions with wrong key -> 401
4. POST /v1/decisions with correct key -> 200, signed decision JSON
5. Response from /v1/decisions can be POSTed to /v1/verify -> valid=true
6. Tampered signature -> verify returns valid=false
7. Malformed JSON -> 400
8. Missing required field -> 400
9. JSONL file is created and appended
10. Client behavior (SDK) can consume the API response

## Rollback

Single commit. git revert if needed.

## References

- EXECUTION_PLAN.md Section 3 (Phase B), Section 5 (stdlib allowed),
  Section 15 (storage Tier 1)
- DC-139 (SDK Client)
- tools/sovereign_http_server.py (pattern reference, not modified)

**Approved by:** Biss (Owner)
**Effective:** 2026-09-18
