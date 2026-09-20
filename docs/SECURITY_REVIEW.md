# EnterpriseGuard Security Review

## Status

- **Task:** C3 - Security report
- **Review target:** OWASP Application Security Verification Standard (ASVS) Level 1
- **Review status:** Complete with material findings
- **ASVS Level 1 outcome:** Not demonstrated; remediation is required before claiming Level 1 alignment
- **Review date:** 2026-09-20

This report is an evidence-based review of the repository as inspected. It
does not authorize security remediation, production changes, a C2 architecture
change, or a change to the execution plan.

## Methodology and scope

The review reloaded the binding rules in `continuity/RULES.md` and the
authoritative task scope in `docs/EXECUTION_PLAN.md`. It inspected the
implemented API, SDK, dashboard, signing and verification paths, persistence,
authentication, input validation, output rendering, deployment files,
configuration, dependency declarations, error handling, and existing security
tests.

Protected directories were not inspected. No source code, tests, governance
records, execution-plan files, or deployment configuration were modified.
The review used repository evidence and a focused existing test run; it did
not perform an external penetration test or claim controls that require a
deployed environment.

## Findings

### F-01 - Reusable hardcoded deployment credentials and encryption key

- **Severity:** High
- **ASVS areas:** V2 Authentication, V6 Stored Cryptography, V14 Configuration
- **Evidence:**
  - `docker-compose.yml:9-11` contains `NEXTAUTH_SECRET: "mysecret"`,
    `SALT: "mysalt"`, and an all-zero `ENCRYPTION_KEY`.
  - `docker-compose.yml:17,29,39` contains literal ClickHouse and PostgreSQL
    credentials.
  - `docker-compose.yml:5,41` publishes service ports, increasing exposure of
    services using those credentials.
- **Impact:** Anyone with access to the repository or reachable deployment can
  reuse the credentials. The all-zero encryption key does not provide
  meaningful secrecy for protected data.
- **Recommendation:** Remove credentials and keys from version-controlled
  configuration, inject unique high-entropy values at deployment time through
  an approved secret-management path, rotate the exposed values, and avoid
  publishing database ports unless required and restricted.

### F-02 - Authenticated deployment uses plaintext HTTP

- **Severity:** High
- **ASVS areas:** V3 Session Management, V9 Communications
- **Evidence:**
  - `Dockerfile:18` starts `tools/sovereign_http_server.py` with
    `--host 0.0.0.0 --port 8443`.
  - `docker-compose.yml:50-51` publishes port `8443`.
  - `tools/sovereign_http_server.py:37-42` authenticates requests with the
    `X-ADIE-Key` header but does not configure TLS or enforce HTTPS.
  - `tools/sovereign_http_server.py:195-207` creates a standard
    `http.server.ThreadingHTTPServer`.
- **Impact:** The API key can be observed and replayed by a network observer or
  compromised intermediary when the service is exposed beyond a trusted local
  host.
- **Recommendation:** Terminate TLS in an approved boundary or use an
  HTTPS-capable server with certificate configuration. Bind the service to a
  private interface by default and rotate any key transmitted over plaintext.

### F-03 - Stored cross-site scripting in the dashboard

- **Severity:** Medium
- **ASVS areas:** V5 Validation, Sanitization and Encoding; V14 Configuration
- **Evidence:**
  - `src/enterpriseguard/api/server.py:96-103` constructs table rows with
    `tr.innerHTML`.
  - `src/enterpriseguard/api/server.py:98-101` concatenates
    `target_resource_id`, `action`, and `created_at` into that HTML.
  - `src/enterpriseguard/api/server.py:231` accepts the decision target from
    the request-derived contract.
  - `src/enterpriseguard/api/server.py:294-311` validates size and
    authentication but does not provide output encoding for dashboard HTML.
- **Impact:** An authenticated caller can store markup in a decision field.
  When an operator opens the dashboard, the stored value can be interpreted as
  HTML and script-capable markup.
- **Recommendation:** Create cells with DOM `textContent` and set only trusted
  CSS class names through a fixed allowlist. Add a regression test using a
  markup payload and deploy a restrictive Content-Security-Policy.

## Verified controls

### Owner-approved security operations policy

The security-event logging implementation uses a fixed schema with only these
event types:

- `authentication_failure`
- `authorization_failure`
- `configuration_error`
- `request_failure`

Only fields appropriate to each event are accepted. Paths and metadata are
serialized with JSON escaping and bounded before logging, so control
characters cannot create additional log lines. Request IDs are generated
locally by the request handlers and are included in emitted events. Credentials,
API keys, authorization headers, tokens, private keys, passwords, secrets, and
request or response payloads are not accepted as security-event fields.

The approved operational policy assigns the security owner to the Project
Owner / Security Responsible Role, the incident owner to the Incident
Management Responsible Role, and residual-risk ownership to the Project Owner.
Escalation is `Incident Owner -> Security Owner -> Owner`.

Operational deployment must provide an authorized log destination and access
control, retention and rotation, evidence preservation, and monitoring/alerting
for repeated authentication failures and critical security events. The policy
does not define a numeric retention period or named access list; those values
remain owner/operator decisions and are not invented by this implementation.

The following controls were confirmed in the inspected implementation:

- API key comparison uses `secrets.compare_digest` in
  `src/enterpriseguard/api/server.py:311`.
- API request bodies are capped at 256 KiB and JSON object input is checked
  (`src/enterpriseguard/api/server.py:44,294-305`).
- Decision persistence uses append-only JSONL writes with `os.O_APPEND`,
  `os.fsync`, file mode `0600`, and directory mode `0700`
  (`src/enterpriseguard/api/server.py:142-151`).
- SDK signing and verification use the existing cryptographic backends and
  verify signed decision material; these behaviors are covered by the focused
  SDK tests.
- API JSON responses set `Cache-Control: no-store`; the API implementation
  also applies `X-Content-Type-Options: nosniff` where responses are emitted.
- The dashboard keeps the entered API key in browser memory rather than
  persisting it to local storage (`src/enterpriseguard/api/server.py:57-76`).

## Partial, missing, and not-applicable areas

### Partial or missing

- **Transport security:** Missing for the deployed authenticated
  `sovereign_http_server.py` path; no TLS or HTTPS enforcement was verified.
- **Secret management:** Missing in the Docker Compose deployment because
  reusable literal credentials and an all-zero key are committed.
- **Browser output encoding:** Missing for decision fields rendered with
  `innerHTML`.
- **Content Security Policy:** No effective CSP header or meta policy was
  verified for the dashboard.
- **Automated security scanning:** `bandit` is declared in `requirements.txt`
  but was unavailable in the execution environment, so no Bandit result is
  claimed.

### Not verified

- TLS configuration at an external reverse proxy or load balancer.
- Runtime secret injection supplied outside this repository.
- Host, container, firewall, network-segmentation, backup, and monitoring
  controls in a production deployment.
- Dependency vulnerability status from `pip-audit`; no audit command was
  claimed because the available environment did not provide the required
  security tooling and no packages were installed.

### Not applicable to this review

- PostgreSQL architecture changes and C2 benchmark remediation are outside C3.
- Phase E trust-layer implementation is inactive and outside the authoritative
  Phase C task scope.

## Tests and checks executed

Existing focused security-relevant tests were run without modifying the
repository:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
  tests/test_api_server.py \
  tests/test_sdk_client.py \
  tests/test_security_integration.py \
  tests/test_prompt_security_advanced.py
```

Result:

```text
25 passed in 32.59s
```

The existing tests passing does not negate the deployment and dashboard
findings above; the current suite does not demonstrate TLS deployment,
secret-rotation controls, or safe HTML rendering of attacker-controlled
decision fields.

The existing Bandit scan was attempted with:

```text
PYTHONDONTWRITEBYTECODE=1 bandit -r src tools -ll -x ./tests
```

Result:

```text
bandit: command not found
```

No package was installed to compensate.

## Conclusion

The repository demonstrates several useful application controls, including
constant-time API-key comparison, bounded request bodies, durable restricted
JSONL persistence, and signed decision verification. However, the three
material findings above prevent an evidence-based claim of OWASP ASVS Level 1
compliance for the repository's deployed surfaces.

This report completes the authorized C3 documentation task with findings.
Remediation requires separate implementation authorization and must not be
inferred as authorization to alter C2, activate Phase E, or change the
execution plan.
