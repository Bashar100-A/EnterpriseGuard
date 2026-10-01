import argparse
import http.server
import json
import logging
import os
import ssl
from pathlib import Path

HARDWARE_IDENTITY_PATH = Path("hardware_identity.json")
logger = logging.getLogger("enterpriseguard.sovereign_security")


def _security_event(event_type: str, path: str = "", request_id: str = "", **kwargs) -> None:
    escaped_path = path.replace("\r", "\\r").replace("\n", "\\n")
    msg = f"security_event={event_type} path={escaped_path} request_id={request_id}"
    for k, v in kwargs.items():
        msg += f" {k}={v}"
    logger.warning(msg)


def _get_expected_identity_key() -> str | None:
    if HARDWARE_IDENTITY_PATH.exists():
        try:
            data = json.loads(HARDWARE_IDENTITY_PATH.read_text(encoding="utf-8"))
            return data.get("identity_key")
        except Exception:
            return None
    return None


class SovereignRequestHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _authenticated(self) -> bool:
        headers = getattr(self, "headers", {}) or {}
        provided_key = headers.get("X-ADIE-Key")
        expected_key = _get_expected_identity_key()
        request_id = headers.get("X-Request-ID", "req-default")

        if provided_key and expected_key and provided_key == expected_key:
            return True

        _security_event(
            "authentication_failure",
            path=getattr(self, "path", ""),
            request_id=request_id,
        )
        return False

    def do_GET(self):
        if not self._authenticated():
            self._send_json(401, {"error": "Unauthorized: Missing or invalid X-ADIE-Key"})
            return

        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        self._send_json(404, {"error": "Not found"})


SovereignHTTPHandler = SovereignRequestHandler


def create_server(host="127.0.0.1", port=8443, tls_certfile=None, tls_keyfile=None):
    if bool(tls_certfile) != bool(tls_keyfile):
        raise ValueError("Both tls_certfile and tls_keyfile must be provided together.")

    server_address = (host, port)
    httpd = http.server.ThreadingHTTPServer(server_address, SovereignRequestHandler)

    if tls_certfile and tls_keyfile:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=tls_certfile, keyfile=tls_keyfile)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    return httpd


def run_server(host="127.0.0.1", port=8443, certfile=None, keyfile=None):
    httpd = create_server(host=host, port=port, tls_certfile=certfile, tls_keyfile=keyfile)

    if certfile and keyfile and os.path.exists(certfile) and os.path.exists(keyfile):
        print(f"Server starting with TLS/HTTPS on https://{host}:{port}")
    else:
        print(f"Server starting on http://{host}:{port} (Local/Internal Mode)")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sovereign HTTP/HTTPS Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8443, help="Port number")
    parser.add_argument("--cert", default=None, help="Path to TLS cert file")
    parser.add_argument("--key", default=None, help="Path to TLS key file")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, certfile=args.cert, keyfile=args.key)
