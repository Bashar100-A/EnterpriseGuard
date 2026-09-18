# DC-141: Dashboard Design (B3)

**Date:** 2026-09-18
**Owner:** Biss
**Status:** APPROVED
**Predecessor:** B2 (HTTP API, commit 07583b4)

## Context

Phase B task B3 (EXECUTION_PLAN Section 3):
> Dashboard — Single-page UI — Shows last 100 decisions + status

## Decision

Extend src/enterpriseguard/api/server.py with:

### Endpoint: GET /dashboard
Returns a single HTML page (inline, vanilla JS).
No auth on the HTML itself (static content).
The page prompts for X-ADIE-Key and then calls the JSON endpoint.

### Endpoint: GET /v1/decisions/recent?limit=N
Auth required (X-ADIE-Key).
Returns: {"decisions": [...], "count": N}
Reads from JSONL storage (today + previous days up to limit).
Limit: default 100, max 1000.
Records are returned in reverse-chronological order.

### HTML page contents
- Title: "ADIE Dashboard"
- Input: API key (stored in memory only, not localStorage)
- Button: Refresh
- Table: decision_id | target | action | authorized | created_at
- Footer: "showing N of M"

## Non-goals (v1)
- No CSS framework (plain CSS inline)
- No routing (single page)
- No auto-refresh
- No filtering / search
- No export

## Technology
- HTML + vanilla JS (EXECUTION_PLAN Section 5 locked)
- No new dependency
- Inline in server.py as _HTML_DASHBOARD constant

## Verification
tests/test_api_server.py extended:
10. GET /dashboard returns 200, HTML, contains "ADIE Dashboard"
11. GET /v1/decisions/recent without auth -> 401
12. GET /v1/decisions/recent with auth -> 200, {"decisions": [...], "count": N}
13. limit=N respects bounds (1..1000, default 100)
14. Reverse chronological order

## Rollback
Single commit.

**Approved by:** Biss (Owner)
**Effective:** 2026-09-18
