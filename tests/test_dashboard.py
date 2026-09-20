"""Tests for B3 Dashboard (dashboard + /v1/decisions/recent).

Scenarios per DC-141:
10. GET /dashboard returns 200 HTML, contains "ADIE Dashboard"
11. GET /v1/decisions/recent without auth -> 401
12. GET /v1/decisions/recent with auth -> 200, {"decisions": [...], "count": N}
13. limit bounds enforced (1..1000)
14. Reverse chronological order
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from enterpriseguard.api import create_server


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
    api_key = "test-api-key-dashboard"

    monkeypatch.setenv("AAAC_API_KEY", api_key)
    monkeypatch.setenv("AAAC_API_DATA_DIR", str(data_dir))
    monkeypatch.setenv("AAAC_KEY_DIR", str(key_dir))
    monkeypatch.setenv("AAAC_SIGNING_BACKEND", "rsa_local")

    import enterpriseguard.api.server as server_mod
    server_mod._CLIENT = None
    server_mod._CLIENT_ERROR = None

    return {"key_dir": key_dir, "data_dir": data_dir, "api_key": api_key}


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


def _get(url, api_key=None):
    headers = {}
    if api_key is not None:
        headers["X-ADIE-Key"] = api_key
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def _get_with_headers(url, api_key=None):
    headers = {}
    if api_key is not None:
        headers["X-ADIE-Key"] = api_key
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, resp.headers, resp.read().decode("utf-8")


def _post_json(url, payload, api_key=None):
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


# ─────────── 10. dashboard HTML ───────────

def test_dashboard_returns_html(running_server):
    status, headers, body = _get_with_headers(f"{running_server['base_url']}/dashboard")
    assert status == 200
    assert "ADIE Dashboard" in body
    assert "<html" in body.lower()
    assert "X-ADIE-Key" in body
    csp = headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "script-src 'nonce-" in csp
    assert "style-src 'nonce-" in csp
    assert "unsafe-inline" not in csp
    assert "unsafe-eval" not in csp
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_dashboard_uses_safe_dynamic_rendering(running_server):
    payloads = (
        "<script>alert(1)</script>",
        '"><img src=x onerror=alert(1)>',
    )
    for payload in payloads:
        status, _ = _post_json(
            f"{running_server['base_url']}/v1/decisions",
            {"target": payload, "intent": "isolate"},
            api_key=running_server["api_key"],
        )
        assert status == 200

    status, _, body = _get_with_headers(
        f"{running_server['base_url']}/dashboard"
    )
    assert status == 200
    assert "tr.innerHTML" not in body
    assert "rows.innerHTML" not in body
    assert "textContent" in body
    assert "replaceChildren" in body
    for payload in payloads:
        assert payload not in body


# ─────────── 11. recent without auth ───────────

def test_recent_no_auth_returns_401(running_server):
    status, _ = _get(f"{running_server['base_url']}/v1/decisions/recent")
    assert status == 401


# ─────────── 12. recent with auth ───────────

def test_recent_with_auth_returns_decisions(running_server):
    base = running_server["base_url"]
    key = running_server["api_key"]

    # Create 2 decisions
    _post_json(f"{base}/v1/decisions", {"target": "h1", "intent": "isolate"}, api_key=key)
    _post_json(f"{base}/v1/decisions", {"target": "h2", "intent": "isolate"}, api_key=key)

    status, raw = _get(f"{base}/v1/decisions/recent", api_key=key)
    assert status == 200
    data = json.loads(raw)
    assert data["count"] == 2
    assert len(data["decisions"]) == 2
    assert "contract" in data["decisions"][0]


# ─────────── 13. limit bounds ───────────

def test_recent_limit_bounds(running_server):
    base = running_server["base_url"]
    key = running_server["api_key"]

    # limit=0 -> 400
    status, _ = _get(f"{base}/v1/decisions/recent?limit=0", api_key=key)
    assert status == 400

    # limit=2000 -> 400
    status, _ = _get(f"{base}/v1/decisions/recent?limit=2000", api_key=key)
    assert status == 400

    # limit=50 -> 200
    status, _ = _get(f"{base}/v1/decisions/recent?limit=50", api_key=key)
    assert status == 200

    # limit not a number -> 400
    status, _ = _get(f"{base}/v1/decisions/recent?limit=abc", api_key=key)
    assert status == 400


# ─────────── 14. reverse chronological ───────────

def test_recent_reverse_chronological(running_server):
    base = running_server["base_url"]
    key = running_server["api_key"]

    # Create 3 decisions in order
    for target in ["first", "second", "third"]:
        _post_json(f"{base}/v1/decisions", {"target": target, "intent": "isolate"}, api_key=key)

    status, raw = _get(f"{base}/v1/decisions/recent", api_key=key)
    assert status == 200
    data = json.loads(raw)
    targets = [d["contract"]["target_resource_id"] for d in data["decisions"]]
    # Newest first
    assert targets == ["third", "second", "first"]
