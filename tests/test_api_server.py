"""Tests for src/enterpriseguard/api/server.py (B2).

Scenarios per DC-140:
1. GET /v1/health returns 200, no auth
2. POST /v1/decisions without key -> 401
3. POST /v1/decisions with wrong key -> 401
4. POST /v1/decisions with correct key -> 200, signed decision
5. Response from /v1/decisions posted to /v1/verify -> valid=true
6. Tampered signature -> verify returns valid=false
7. Malformed JSON -> 400
8. Missing target field -> 400
9. JSONL file created, has 2 lines, mode 0600
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from enterpriseguard.api import create_server


COMPOSE_FILE = Path(__file__).resolve().parent.parent / "docker-compose.yml"


def test_compose_requires_deployment_secrets():
    compose = COMPOSE_FILE.read_text(encoding="utf-8")

    required_variables = (
        "NEXTAUTH_SECRET",
        "SALT",
        "ENCRYPTION_KEY",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_PASSWORD",
    )
    for variable in required_variables:
        assert f"${{{variable}:?" in compose


def test_compose_contains_no_previous_f01_literals():
    compose = COMPOSE_FILE.read_text(encoding="utf-8")

    for insecure_value in (
        "mysecret",
        "mysalt",
        "0000000000000000000000000000000000000000000000000000000000000000",
        'CLICKHOUSE_PASSWORD: "clickhouse"',
        "POSTGRES_PASSWORD: postgres",
    ):
        assert insecure_value not in compose


def test_authentication_failure_logs_no_api_key(running_server, caplog):
    caplog.set_level(logging.WARNING, logger="enterpriseguard.security")
    status, _ = _post(
        f"{running_server['base_url']}/v1/decisions",
        {"target": "host-01", "intent": "isolate"},
        api_key="sensitive-test-api-key",
    )
    assert status == 401
    assert "security_event=authentication_failure" in caplog.text
    assert "sensitive-test-api-key" not in caplog.text
    assert "X-ADIE-Key" not in caplog.text


def test_missing_api_key_logs_configuration_name_only(monkeypatch, caplog):
    import enterpriseguard.api.server as server_mod

    caplog.set_level(logging.WARNING, logger="enterpriseguard.security")
    monkeypatch.delenv("AAAC_API_KEY", raising=False)
    assert server_mod._get_api_key() is None
    server_mod._security_event(
        "configuration_error",
        request_id="request-1",
        setting="AAAC_API_KEY",
    )
    assert "security_event=configuration_error" in caplog.text
    assert 'setting="AAAC_API_KEY"' in caplog.text
    assert "secret" not in caplog.text.lower()
    assert "request_id=\"request-1\"" in caplog.text


def test_security_event_schema_escapes_paths_and_rejects_unsupported_data(caplog):
    import enterpriseguard.api.server as server_mod

    caplog.set_level(logging.WARNING, logger="enterpriseguard.security")
    server_mod._security_event(
        "authentication_failure",
        path="/v1/\nforged=event",
        request_id="request-2",
    )
    assert "forged=event" in caplog.text
    assert "\\n" in caplog.text
    assert "\nforged=event" not in caplog.text

    with pytest.raises(ValueError, match="unsupported security event"):
        server_mod._security_event("audit_event", request_id="request-3")
    with pytest.raises(ValueError, match="unsupported fields"):
        server_mod._security_event(
            "request_failure",
            method="POST",
            path="/v1/decisions",
            request_id="request-4",
            payload='{"secret":"value"}',
        )


# ───────────────────── fixtures ─────────────────────

def _make_rsa_keypair(base: Path) -> Path:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_dir = base / "keys"
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / "private_key.pem").write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    (key_dir / "public_key.pem").write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return key_dir


@pytest.fixture
def api_env(tmp_path, monkeypatch):
    key_dir = _make_rsa_keypair(tmp_path)
    data_dir = tmp_path / "data"
    api_key = "test-api-key-12345"

    monkeypatch.setenv("AAAC_API_KEY", api_key)
    monkeypatch.setenv("AAAC_API_DATA_DIR", str(data_dir))
    monkeypatch.setenv("AAAC_KEY_DIR", str(key_dir))
    monkeypatch.setenv("AAAC_SIGNING_BACKEND", "rsa_local")

    import enterpriseguard.api.server as server_mod
    server_mod._CLIENT = None
    server_mod._CLIENT_ERROR = None

    return {
        "key_dir": key_dir,
        "data_dir": data_dir,
        "api_key": api_key,
    }


@pytest.fixture
def running_server(api_env):
    server = create_server("127.0.0.1", 0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "api_key": api_env["api_key"],
        "data_dir": api_env["data_dir"],
    }

    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


# ───────────────────── helpers ─────────────────────

def _post(url, payload, api_key=None):
    headers = {"Content-Type": "application/json"}
    if api_key is not None:
        headers["X-ADIE-Key"] = api_key
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def _get(url):
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


# ─────────── 1. health ───────────

def test_health_no_auth(running_server):
    status, body = _get(f"{running_server['base_url']}/v1/health")
    assert status == 200
    assert body["status"] == "ok"
    assert body["version"] == "0.5.0"


# ─────────── 2. no key ───────────

def test_decisions_no_key_returns_401(running_server):
    status, body = _post(
        f"{running_server['base_url']}/v1/decisions",
        {"target": "h", "intent": "isolate"},
        api_key=None,
    )
    assert status == 401
    assert body["error"] == "unauthorized"


# ─────────── 3. wrong key ───────────

def test_decisions_wrong_key_returns_401(running_server):
    status, _ = _post(
        f"{running_server['base_url']}/v1/decisions",
        {"target": "h", "intent": "isolate"},
        api_key="wrong",
    )
    assert status == 401


# ─────────── 4. valid decision ───────────

def test_decisions_valid_key_returns_200(running_server):
    status, body = _post(
        f"{running_server['base_url']}/v1/decisions",
        {"target": "host-01", "intent": "isolate"},
        api_key=running_server["api_key"],
    )
    assert status == 200
    assert "contract" in body
    assert "signature_hex" in body
    assert body["contract"]["authorized"] is True


# ─────────── 5. verify round-trip ───────────

def test_decision_then_verify_roundtrip(running_server):
    base = running_server["base_url"]
    key = running_server["api_key"]

    status, signed = _post(
        f"{base}/v1/decisions",
        {"target": "host-01", "intent": "isolate"},
        api_key=key,
    )
    assert status == 200

    status, result = _post(f"{base}/v1/verify", signed, api_key=key)
    assert status == 200
    assert result["valid"] is True


# ─────────── 6. tampered ───────────

def test_verify_tampered_returns_false(running_server):
    base = running_server["base_url"]
    key = running_server["api_key"]

    _, signed = _post(
        f"{base}/v1/decisions",
        {"target": "host-01", "intent": "isolate"},
        api_key=key,
    )
    sig = signed["signature_hex"]
    signed["signature_hex"] = ("0" if sig[0] != "0" else "1") + sig[1:]

    status, result = _post(f"{base}/v1/verify", signed, api_key=key)
    assert status == 200
    assert result["valid"] is False


# ─────────── 7. malformed ───────────

def test_malformed_json_returns_400(running_server):
    base = running_server["base_url"]
    req = urllib.request.Request(
        f"{base}/v1/decisions",
        data=b"{not json",
        headers={
            "Content-Type": "application/json",
            "X-ADIE-Key": running_server["api_key"],
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            pytest.fail("expected 400")
    except urllib.error.HTTPError as e:
        assert e.code == 400


# ─────────── 8. missing field ───────────

def test_missing_target_returns_400(running_server):
    status, _ = _post(
        f"{running_server['base_url']}/v1/decisions",
        {"intent": "isolate"},
        api_key=running_server["api_key"],
    )
    assert status == 400


# ─────────── 9. JSONL file ───────────

def test_jsonl_file_created(running_server):
    base = running_server["base_url"]
    key = running_server["api_key"]
    data_dir = running_server["data_dir"]

    _post(f"{base}/v1/decisions", {"target": "h1", "intent": "isolate"}, api_key=key)
    _post(f"{base}/v1/decisions", {"target": "h2", "intent": "isolate"}, api_key=key)

    files = list(data_dir.glob("decisions-*.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "contract" in obj

    mode = files[0].stat().st_mode & 0o777
    assert mode == 0o600, f"expected 0600, got {oct(mode)}"
