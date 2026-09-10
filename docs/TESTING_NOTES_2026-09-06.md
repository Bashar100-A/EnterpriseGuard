# Testing Notes — 2026-09-06

## Scenario 1-6: Basic flow
- Result: PASS (except first send had DNS error, retried successfully)
- Notes: /events and /agents work.

## Scenario 7-9: Multiple traces and HTTP
- Result: PASS (8 observations fetched and saved)
- Notes: /events?limit=10 shows 10 events, all with agent-123.

## Scenario 10: Event without trace_id
- Result: PASS
- Notes: Event accepted and displayed without `trace_id`; system did not crash.

## Scenario 11: Event without agent_id
- Result: PASS
- Notes: Event accepted and displayed without `agent_id`; `/agents` still shows only `agent-123` because it extracts agents from events that have `agent_id`.

## Scenario 12: Integrity check
- Result: PASS
- Notes: No monitored files modified.

## Scenario 13: Last ring
- Result: PASS
- Notes: `agent_events_hash` changed after generating a new ring. New hash: `5a6469ae223a258a456314b4b6022dd6a88141db708c4d366fa9ab7faa20dc6c`.


## Phase 2: Duplicate avoidance, RFC3161, dashboard
- Duplicate trace_id test: PASS (all 8 existing traces skipped on second run).
- RFC3161 token: partial (field present but returns "Bad request format or system error").
- Dashboard: endpoint created; pending browser test.
- Integrity check: PASS.
- Chain verify: VERIFIED_OK.


## Phase 2 Later Fixes (2026-09-06 evening)
- RFC3161 timestamp: fixed, now returns valid DER token from Certum.
- Dashboard: accessible via /dashboard without auth (temporary).
- Open verifier: created and tested `VALID: chain is authentic`.
- Integrity check: PASS.

## Compliance Docs
- Created AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md and AAAC_LEGAL_USE_CASE.md (draft).
