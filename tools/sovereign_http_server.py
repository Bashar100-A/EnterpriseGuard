import http.server
import ssl
import json
import argparse
import sys
import os

class SovereignHTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        auth_header = self.headers.get("X-ADIE-Key")
        if not auth_header:
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized: Missing X-ADIE-Key"}).encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "service": "sovereign_http_server"}).encode())

def run_server(host="127.0.0.1", port=8443, certfile=None, keyfile=None):
    server_address = (host, port)
    httpd = http.server.ThreadingHTTPServer(server_address, SovereignHTTPHandler)

    if certfile and keyfile and os.path.exists(certfile) and os.path.exists(keyfile):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
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
