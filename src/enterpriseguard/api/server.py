#!/usr/bin/env python3
"""HTTP API for EnterpriseGuard decisions.

Endpoints (v1):
    GET  /v1/health     public, no auth
    POST /v1/decisions  auth required, JSONL append with fsync
    POST /v1/verify     auth required, no side effects

Framework: http.server stdlib (DC-140).
Auth: X-ADIE-Key header; expected value from AAAC_API_KEY env var.
Storage: JSONL append at AAAC_API_DATA_DIR (default ~/.enterpriseguard/api/).
Files: 0600 for records, 0700 for directories (fail-closed).
Backend: 'rsa_local' | 'ecdsa_local' from enterpriseguard.signing.
Requires Python 3.11+ (datetime.fromisoformat Z-suffix support).
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import secrets
import sys
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.dont_write_bytecode = True

from enterpriseguard.decision.contracts import (
    DecisionAction,
    DecisionContract,
    DecisionStatus,
    DecisionValidationError,
)
from enterpriseguard.sdk import Client, SDKError, SignedDecision


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8443
API_VERSION = "0.5.0"
MAX_BODY_BYTES = 256 * 1024
_SECURITY_LOGGER = logging.getLogger("enterpriseguard.security")
_SECURITY_EVENT_FIELDS = {
    "authentication_failure": frozenset({"path", "request_id"}),
    "authorization_failure": frozenset({"path", "request_id"}),
    "configuration_error": frozenset({"setting", "request_id"}),
    "request_failure": frozenset({"method", "path", "request_id"}),
}
_SENSITIVE_LOG_FIELD_NAMES = frozenset(
    {
        "api_key",
        "authorization",
        "credential",
        "key",
        "password",
        "payload",
        "private_key",
        "request_body",
        "response_body",
        "secret",
        "token",
    }
)

_HTML_DASHBOARD = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>ADIE Dashboard</title>
<style nonce="{{CSP_NONCE}}">
body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#1a1a2e}
h1{color:#0f3460;border-bottom:3px solid #0f3460;padding-bottom:.5rem}
.bar{display:flex;gap:.5rem;margin:1rem 0;flex-wrap:wrap}
input{padding:.6rem;border:1px solid #ccc;border-radius:4px;font-family:monospace;font-size:.9rem;flex:1;min-width:200px}
button{background:#0f3460;color:#fff;border:0;padding:.6rem 1.2rem;border-radius:4px;cursor:pointer;font-size:.95rem}
button:hover{background:#16213e}
table{width:100%;border-collapse:collapse;font-size:.85rem;margin-top:1rem}
th{background:#0f3460;color:#fff;padding:.5rem;text-align:left}
td{padding:.4rem .5rem;border-bottom:1px solid #eee}
tr:hover{background:#f5f5f5}
.authorized-yes{color:#2e7d32;font-weight:bold}
.authorized-no{color:#c62828;font-weight:bold}
.footer{margin-top:1rem;color:#666;font-size:.85rem}
.error{color:#c62828;font-weight:bold}
.hidden{display:none}
</style></head><body>
<h1>ADIE Dashboard</h1>
<div class="bar">
  <input id="key" type="password" placeholder="X-ADIE-Key (kept in memory only)">
  <button id="refresh" type="button">Refresh</button>
</div>
<div id="status" class="footer">Enter API key and click Refresh.</div>
<table id="table" class="hidden">
  <thead><tr>
    <th>Decision ID</th><th>Target</th><th>Action</th>
    <th>Authorized</th><th>Created (UTC)</th>
  </tr></thead>
  <tbody id="rows"></tbody>
</table>
<div id="footer" class="footer"></div>
  <script nonce="{{CSP_NONCE}}">
async function load() {
  const key = document.getElementById('key').value;
  const status = document.getElementById('status');
  const table = document.getElementById('table');
  const rows = document.getElementById('rows');
  const footer = document.getElementById('footer');
  if (!key) { status.textContent = 'API key required.'; status.className='footer error'; return; }
  status.textContent = 'Loading...'; status.className = 'footer';
  try {
    const r = await fetch('/v1/decisions/recent?limit=100', {headers:{'X-ADIE-Key': key}});
    if (!r.ok) { status.textContent = 'Error: HTTP ' + r.status; status.className='footer error'; return; }
    const data = await r.json();
    rows.replaceChildren();
    for (const d of data.decisions) {
      const c = d.contract || {};
      const tr = document.createElement('tr');
      const addCell = (value, code = false) => {
        const cell = document.createElement('td');
        const content = code ? document.createElement('code') : cell;
        content.textContent = value;
        if (code) cell.appendChild(content);
        tr.appendChild(cell);
      };
      addCell((c.decision_id || '?').slice(0,20) + '...', true);
      addCell(c.target_resource_id || '');
      addCell(c.action || '');
      const authorized = document.createElement('td');
      authorized.className = c.authorized ? 'authorized-yes' : 'authorized-no';
      authorized.textContent = c.authorized ? 'YES' : 'NO';
      tr.appendChild(authorized);
      addCell(c.created_at || '', true);
      rows.appendChild(tr);
    }
    table.classList.remove('hidden');
    footer.textContent = 'Showing ' + data.count + ' recent decisions.';
    status.textContent = 'OK';
  } catch (e) {
    status.textContent = 'Error: ' + e.message; status.className='footer error';
  }
}
document.getElementById('refresh').addEventListener('click', load);
</script>
</body></html>"""


def _dashboard_html(nonce: str) -> str:
    """Render the dashboard with a request-specific CSP nonce."""
    return _HTML_DASHBOARD.replace("{{CSP_NONCE}}", nonce)


def _dashboard_csp(nonce: str) -> str:
    """Return the restrictive policy for the inline dashboard assets."""
    return (
        "default-src 'none'; "
        f"script-src 'nonce-{nonce}'; "
        f"style-src 'nonce-{nonce}'; "
        "connect-src 'self'; "
        "img-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "frame-ancestors 'none'"
    )


class APIError(Exception):
    """Base exception for API-layer errors."""


# ───────────────────── env helpers ─────────────────────

def _get_api_key() -> str | None:
    return os.environ.get("AAAC_API_KEY")


def _security_event(event: str, **fields: object) -> None:
    """Emit only the approved, escaped security-event schema."""
    allowed_fields = _SECURITY_EVENT_FIELDS.get(event)
    if allowed_fields is None:
        raise ValueError(f"unsupported security event: {event}")
    if set(fields) - allowed_fields:
        raise ValueError(f"unsupported fields for security event: {event}")
    if set(fields) & _SENSITIVE_LOG_FIELD_NAMES:
        raise ValueError("sensitive security-event fields are forbidden")
    details = " ".join(
        f"{key}={json.dumps(str(fields[key])[:256], ensure_ascii=True)}"
        for key in sorted(fields)
    )
    _SECURITY_LOGGER.warning(
        "security_event=%s%s",
        event,
        f" {details}" if details else "",
    )


def _get_data_dir() -> Path:
    override = os.environ.get("AAAC_API_DATA_DIR")
    if override:
        return Path(override)
    home = os.environ.get("HOME")
    if not home:
        raise RuntimeError("HOME not set; AAAC_API_DATA_DIR must be provided")
    return Path(home) / ".enterpriseguard" / "api"


def _today_jsonl(data_dir: Path) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return data_dir / f"decisions-{today}.jsonl"


def _append_decision(data_dir: Path, payload: dict[str, Any]) -> None:
    """Append one decision record with fsync for durability."""
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = _today_jsonl(data_dir)
    line = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, (line + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_recent_decisions(data_dir: Path, limit: int) -> list[dict[str, Any]]:
    """Read up to `limit` most recent decisions from JSONL files."""
    if limit <= 0:
        return []
    if not data_dir.exists():
        return []

    files = sorted(data_dir.glob("decisions-*.jsonl"), reverse=True)
    records: list[dict[str, Any]] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        # Reverse within the file: newest first.
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(records) >= limit:
                return records
    return records


# ───────────────────── client singleton ─────────────────────

_CLIENT: Client | None = None
_CLIENT_ERROR: str | None = None


def _get_client() -> Client:
    """Return a cached Client; store and re-raise init failure."""
    global _CLIENT, _CLIENT_ERROR
    if _CLIENT is not None:
        return _CLIENT
    if _CLIENT_ERROR is not None:
        raise SDKError(f"Client initialization previously failed: {_CLIENT_ERROR}")
    try:
        backend = os.environ.get("AAAC_SIGNING_BACKEND", "rsa_local")
        key_dir_env = os.environ.get("AAAC_KEY_DIR")
        key_dir = Path(key_dir_env) if key_dir_env else None
        _CLIENT = Client(backend=backend, key_dir=key_dir)
        return _CLIENT
    except Exception as exc:
        _CLIENT_ERROR = str(exc)
        print(f"FATAL: Client init failed: {exc}", file=sys.stderr)
        raise


# ───────────────────── reconstruction ─────────────────────

def _rebuild_signed_decision(payload: dict[str, Any]) -> SignedDecision:
    """Rebuild a SignedDecision from a to_dict() payload."""
    if not isinstance(payload, dict):
        raise APIError("payload must be a JSON object")
    if "contract" not in payload:
        raise APIError("missing 'contract' field")
    c = payload["contract"]
    if not isinstance(c, dict):
        raise APIError("'contract' must be a JSON object")

    try:
        contract = DecisionContract(
            decision_id=c["decision_id"],
            evaluation_id=c["evaluation_id"],
            policy_id=c["policy_id"],
            action=DecisionAction(c["action"]),
            status=DecisionStatus(c["status"]),
            authorized=bool(c["authorized"]),
            created_at=datetime.fromisoformat(c["created_at"]),
            expires_at=datetime.fromisoformat(c["expires_at"])
                if c.get("expires_at") else None,
            target_resource_id=c["target_resource_id"],
            parameters=c.get("parameters", {}),
            provenance_hash=c.get("provenance_hash", ""),
            executes_security_actions=False,
        )
    except DecisionValidationError as exc:
        raise APIError(f"invalid contract: {exc}") from exc
    except (KeyError, ValueError, TypeError) as exc:
        raise APIError(f"invalid contract: {exc}") from exc

    try:
        signed_at = datetime.fromisoformat(payload["signed_at"])
        return SignedDecision(
            contract=contract,
            signature_hex=str(payload["signature_hex"]),
            signed_at=signed_at,
            backend=str(payload["backend"]),
            signed_payload_hash=str(payload["signed_payload_hash"]),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise APIError(f"invalid signed decision: {exc}") from exc


# ───────────────────── request handler ─────────────────────

class _Handler(BaseHTTPRequestHandler):
    server_version = "ADIE-API"
    sys_version = ""

    # ---- response helpers ----

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass
    def _send_html(
        self,
        status: int,
        html: str,
        *,
        content_security_policy: str | None = None,
    ) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        if content_security_policy:
            self.send_header("Content-Security-Policy", content_security_policy)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _read_json_body(self) -> dict[str, Any]:
        raw_len = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_len)
        except ValueError:
            raise APIError("invalid Content-Length")
        if length <= 0:
            raise APIError("empty body")
        if length > MAX_BODY_BYTES:
            raise APIError("body too large")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise APIError(f"invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise APIError("payload must be a JSON object")
        return data

    def _check_auth(self) -> bool:
        expected = _get_api_key()
        if not expected:
            _security_event(
                "configuration_error",
                request_id=self._request_id(),
                setting="AAAC_API_KEY",
            )
            self._send_json(503, {"error": "api_key_not_configured"})
            return False
        provided = self.headers.get("X-ADIE-Key", "")
        if not secrets.compare_digest(provided, expected):
            _security_event(
                "authentication_failure",
                path=self._path(),
                request_id=self._request_id(),
            )
            self._send_json(401, {"error": "unauthorized"})
            return False
        return True

    def _path(self) -> str:
        return urlparse(self.path).path

    def _request_id(self) -> str:
        request_id = getattr(self, "_security_request_id", None)
        if request_id is None:
            request_id = uuid.uuid4().hex
            self._security_request_id = request_id
        return request_id

    # ---- routes ----

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._route_get()
        except Exception:
            _security_event(
                "request_failure",
                method="GET",
                path=self._path(),
                request_id=self._request_id(),
            )
            try:
                self._send_json(500, {"error": "internal"})
            except Exception:
                pass

    def _route_get(self) -> None:
        path = self._path()
        if path == "/v1/health":
            self._send_json(200, {"status": "ok", "version": API_VERSION})
            return
        if path == "/dashboard":
            nonce = base64.b64encode(secrets.token_bytes(32)).decode("ascii")
            self._send_html(
                200,
                _dashboard_html(nonce),
                content_security_policy=_dashboard_csp(nonce),
            )
            return
        if path == "/v1/decisions/recent":
            self._handle_recent()
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._route_post()
        except Exception:
            _security_event(
                "request_failure",
                method="POST",
                path=self._path(),
                request_id=self._request_id(),
            )
            try:
                self._send_json(500, {"error": "internal"})
            except Exception:
                pass

    def _route_post(self) -> None:
        path = self._path()
        if path == "/v1/decisions":
            self._handle_decisions()
            return
        if path == "/v1/verify":
            self._handle_verify()
            return
        self._send_json(404, {"error": "not_found"})

    def _handle_decisions(self) -> None:
        if not self._check_auth():
            return
        try:
            body = self._read_json_body()
        except APIError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        target = body.get("target")
        intent = body.get("intent")
        if not isinstance(target, str) or not target or len(target) > 512:
            self._send_json(400, {"error": "target must be a non-empty string (<=512)"})
            return
        if not isinstance(intent, str) or not intent or len(intent) > 128:
            self._send_json(400, {"error": "intent must be a non-empty string (<=128)"})
            return

        policy_id = body.get("policy_id", "default")
        if not isinstance(policy_id, str) or not policy_id or len(policy_id) > 128:
            self._send_json(400, {"error": "policy_id must be a non-empty string (<=128)"})
            return

        parameters = body.get("parameters")
        if parameters is not None and not isinstance(parameters, dict):
            self._send_json(400, {"error": "parameters must be a JSON object"})
            return

        try:
            signed = _get_client().decide(
                target=target,
                intent=intent,
                policy_id=policy_id,
                parameters=parameters,
            )
        except SDKError as exc:
            print(f"decision_failed: {exc}", file=sys.stderr)
            self._send_json(500, {"error": "decision_failed"})
            return
        except DecisionValidationError as exc:
            self._send_json(400, {"error": f"invalid_decision: {exc}"})
            return

        payload = signed.to_dict()
        try:
            _append_decision(_get_data_dir(), payload)
        except Exception as exc:
            print(f"storage_failed: {exc}", file=sys.stderr)
            self._send_json(500, {"error": "storage_failed"})
            return

        self._send_json(200, payload)

    def _handle_verify(self) -> None:
        if not self._check_auth():
            return
        try:
            body = self._read_json_body()
        except APIError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        try:
            signed = _rebuild_signed_decision(body)
        except APIError as exc:
            self._send_json(400, {"error": str(exc)})
            return

        try:
            valid = _get_client().verify(signed)
        except Exception as exc:
            print(f"verify_failed: {exc}", file=sys.stderr)
            self._send_json(500, {"error": "verify_failed"})
            return

        self._send_json(200, {"valid": bool(valid)})

    def _handle_recent(self) -> None:
        if not self._check_auth():
            return
        # Parse limit from query string (default 100, max 1000).
        parsed = urlparse(self.path)
        params = dict(
            pair.split("=", 1)
            for pair in parsed.query.split("&")
            if "=" in pair
        )
        try:
            limit = int(params.get("limit", "100"))
        except ValueError:
            self._send_json(400, {"error": "limit must be an integer"})
            return
        if limit < 1 or limit > 1000:
            self._send_json(400, {"error": "limit must be between 1 and 1000"})
            return

        try:
            records = _read_recent_decisions(_get_data_dir(), limit)
        except Exception as exc:
            print(f"read_recent_failed: {exc}", file=sys.stderr)
            self._send_json(500, {"error": "read_failed"})
            return

        self._send_json(200, {"decisions": records, "count": len(records)})

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        pass


# ───────────────────── server factory + CLI ─────────────────────

def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> ThreadingHTTPServer:
    """Create a ThreadingHTTPServer bound to (host, port)."""
    return ThreadingHTTPServer((host, port), _Handler)


def _preflight() -> int:
    """Return 0 if preflight passes, non-zero otherwise."""
    if not _get_api_key():
        print(
            "ERROR: AAAC_API_KEY is not set.\n"
            "Generate one with:\n"
            "  python3 -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
            "Then export it before starting the server.",
            file=sys.stderr,
        )
        return 2

    home = os.environ.get("HOME")
    if not home:
        print("ERROR: HOME not set; set AAAC_KEY_DIR or HOME", file=sys.stderr)
        return 2

    key_dir = Path(
        os.environ.get("AAAC_KEY_DIR", str(Path(home) / ".enterpriseguard" / "keys"))
    )
    backend = os.environ.get("AAAC_SIGNING_BACKEND", "rsa_local")
    if backend == "rsa_local" and not (key_dir / "private_key.pem").exists():
        print(
            f"ERROR: missing private key at {key_dir / 'private_key.pem'}.\n"
            "Run: python3 tools/hardware_identity.py --generate\n"
            "Or set AAAC_KEY_DIR to the correct location.",
            file=sys.stderr,
        )
        return 2

    # Verify Client can be constructed and keys load successfully.
    try:
        _get_client()
    except Exception as exc:
        print(f"ERROR: Client initialization failed: {exc}", file=sys.stderr)
        return 2
    return 0


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="EnterpriseGuard HTTP API (v1).",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    rc = _preflight()
    if rc != 0:
        return rc

    # File permissions: fail-closed. New files 0600, dirs 0700.
    os.umask(0o077)

    server = create_server(args.host, args.port)
    print(f"ADIE-API {API_VERSION} listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
