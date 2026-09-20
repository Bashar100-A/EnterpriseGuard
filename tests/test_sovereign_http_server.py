"""TLS boundary tests for the sovereign HTTP server."""

from __future__ import annotations

import json
import logging
import socket
import ssl
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from tools import sovereign_http_server


def _write_tls_material(base: Path) -> tuple[Path, Path]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]
    )
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    certfile = base / "server.crt"
    keyfile = base / "server.key"
    certfile.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    keyfile.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return certfile, keyfile


def _start_server(tmp_path: Path):
    certfile, keyfile = _write_tls_material(tmp_path)
    identity_file = tmp_path / "hardware_identity.json"
    identity_file.write_text(json.dumps({"identity_key": "test-key"}), encoding="utf-8")
    original_identity_path = sovereign_http_server.HARDWARE_IDENTITY_PATH
    sovereign_http_server.HARDWARE_IDENTITY_PATH = identity_file
    server = sovereign_http_server.create_server(
        "127.0.0.1",
        0,
        tls_certfile=str(certfile),
        tls_keyfile=str(keyfile),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    return server, thread, original_identity_path


def test_https_preserves_authentication_and_health(tmp_path):
    server, thread, original_identity_path = _start_server(tmp_path)
    try:
        port = server.server_address[1]
        context = ssl._create_unverified_context()
        request = urllib.request.Request(
            f"https://localhost:{port}/health",
            headers={"X-ADIE-Key": "test-key"},
        )
        with urllib.request.urlopen(request, context=context, timeout=5) as response:
            assert response.status == 200
            assert json.loads(response.read()) == {"status": "ok"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        sovereign_http_server.HARDWARE_IDENTITY_PATH = original_identity_path


def test_plaintext_request_is_rejected_by_tls_server(tmp_path):
    server, thread, original_identity_path = _start_server(tmp_path)
    try:
        port = server.server_address[1]
        with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
            connection.sendall(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
            connection.settimeout(2)
            response = connection.recv(128)
        assert not response.startswith(b"HTTP/")
    except (ConnectionResetError, BrokenPipeError, ssl.SSLError):
        pass
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        sovereign_http_server.HARDWARE_IDENTITY_PATH = original_identity_path


def test_tls_arguments_must_be_complete(tmp_path):
    certfile, _ = _write_tls_material(tmp_path)
    try:
        sovereign_http_server.create_server(
            "127.0.0.1",
            0,
            tls_certfile=str(certfile),
        )
    except ValueError as exc:
        assert "provided together" in str(exc)
    else:
        raise AssertionError("incomplete TLS configuration was accepted")


def test_production_container_requires_tls_secrets():
    repository_root = Path(__file__).resolve().parent.parent
    dockerfile = (repository_root / "Dockerfile").read_text(encoding="utf-8")
    compose = (repository_root / "docker-compose.yml").read_text(encoding="utf-8")

    assert "--tls-certfile" in dockerfile
    assert "--tls-keyfile" in dockerfile
    assert "aaac_tls_cert" in compose
    assert "aaac_tls_key" in compose
    assert "${AAAC_TLS_CERT_FILE:?" in compose
    assert "${AAAC_TLS_KEY_FILE:?" in compose


def test_sovereign_authentication_failure_logs_no_key(tmp_path, caplog):
    identity_file = tmp_path / "hardware_identity.json"
    identity_file.write_text(
        json.dumps({"identity_key": "sensitive-identity-key"}),
        encoding="utf-8",
    )
    original_identity_path = sovereign_http_server.HARDWARE_IDENTITY_PATH
    sovereign_http_server.HARDWARE_IDENTITY_PATH = identity_file
    caplog.set_level(
        logging.WARNING,
        logger="enterpriseguard.sovereign_security",
    )
    try:
        handler = sovereign_http_server.SovereignRequestHandler
        handler_instance = object.__new__(handler)
        handler_instance.headers = {"X-ADIE-Key": "wrong-identity-key"}
        handler_instance.path = "/health"
        handler_instance._send_json = lambda *_args: None
        assert handler_instance._authenticated() is False
        assert "security_event=authentication_failure" in caplog.text
        assert "sensitive-identity-key" not in caplog.text
        assert "request_id=" in caplog.text
    finally:
        sovereign_http_server.HARDWARE_IDENTITY_PATH = original_identity_path


def test_sovereign_security_event_schema_escapes_paths(caplog):
    caplog.set_level(
        logging.WARNING,
        logger="enterpriseguard.sovereign_security",
    )
    sovereign_http_server._security_event(
        "authentication_failure",
        path="/health\r\nforged=event",
        request_id="request-5",
    )
    assert "\\r\\n" in caplog.text
    assert "\r\nforged=event" not in caplog.text
