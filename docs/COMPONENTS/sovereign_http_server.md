# Component: sovereign_http_server.py

**Path:** `tools/sovereign_http_server.py`
**Purpose:** HTTP server for SIBB storage, innocence chain, and dashboard.
**Status:** Working (used for demos and integrations)

---

## What It Does

Provides HTTP endpoints for:
- Health check
- Chain verification
- Compliance report
- Dashboard (HTML view)
- Agent listing
- Events listing

Uses Python standard library `http.server` — no external dependencies.

## Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| /health | GET | No | Server health |
| /verify-chain | GET | Yes | Verify innocence chain |
| /compliance-report | GET | Yes | Generate compliance report |
| /dashboard | GET | Configurable | HTML dashboard |
| /agents | GET | Yes | List agents (from ring storage) |
| /events | GET | Yes | List events (limit 500) |
| /dimensions | GET | Yes | Dimensional state |

## Authentication

- Header: `X-ADIE-Key: <key>`
- Key from environment (SOVEREIGN_HTTP_KEY)
- Returns 401 for invalid key
- /dashboard may be temporarily open (configurable)

## Inputs

- HTTP requests (GET)
- Query parameters: limit, since

## Outputs

- JSON responses (default)
- HTML for /dashboard
- Status codes: 200, 401, 404, 500

## Key Functions

| Function | Purpose |
|----------|---------|
| serve_health() | Health endpoint |
| serve_verify_chain() | Verify chain |
| serve_compliance_report() | Compliance report |
| serve_dashboard() | HTML dashboard |
| load_agents() | Read from ring_storage.jsonl |
| load_events() | Read recent events |
| check_auth() | Verify X-ADIE-Key |

## Security

- API key authentication (X-ADIE-Key header)
- Dashboard temporarily open for local testing (must be reverted)
- No file upload
- No shell execution
- Read-only operations (except chain generation via CLI)

## Dashboard Content

- Ring count
- Integrity status
- Verification result
- TSA info
- Agents list
- Recent events

## Performance

- /events: reads last 2000 lines for performance
- /agents: reads unique agent IDs from ring_storage.jsonl
- Limit cap: 500 events per request

## Tests

- Tested manually via curl
- No dedicated test file

## Used By

- Demo environment
- Langfuse/LangSmith integration
- Future: public API for customers

**End of Component Doc**
