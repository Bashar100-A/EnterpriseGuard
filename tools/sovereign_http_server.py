#!/usr/bin/env python3
"""Minimal authenticated HTTP server for EnterpriseGuard state inspection."""

import argparse
import json
import sys
import http.server
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import (
    HARDWARE_IDENTITY_PATH,
    DIMENSIONAL_STATE_PATH,
    INNOCENCE_CHAIN_PATH,
)

# مسار ملف تخزين الأحداث (يمكن تغييره إذا أضفت المسار إلى paths_config)
RING_STORAGE_PATH = ROOT / "tools" / "ring_storage.jsonl"
RELATIONAL_MEMORY_PATH = ROOT / "tools" / "relational_memory.json"


class SovereignRequestHandler(http.server.BaseHTTPRequestHandler):
    """Authenticate and serve the supported read-only JSON endpoints."""

    server_version = "SovereignHTTP/1.0"

    def _send_json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _authenticated(self) -> bool:
        expected_key = load_identity_key()
        supplied_key = self.headers.get("X-ADIE-Key")
        if not expected_key or supplied_key != expected_key:
            self._send_json(401, {"error": "unauthorized"})
            return False
        return True

    def do_GET(self) -> None:
        if not self._authenticated():
            return

        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/dimensions":
            self._send_json(200, load_json(DIMENSIONAL_STATE_PATH, {}))
        elif self.path == "/verify-chain":
            valid, reason = verify_chain()
            self._send_json(200, {"valid": valid, "reason": reason})
        elif self.path == "/agents":
            self._send_json(200, load_agents())
        elif self.path.startswith("/events"):
            self._send_json(200, load_events(self.path))
        else:
            self._send_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args: object) -> None:
        return


def load_json(path: Path, default: object) -> object:
    """Load JSON from path, returning default when unavailable or invalid."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default


def load_identity_key() -> str | None:
    """Load the hardware identity key used to authenticate requests."""
    identity = load_json(HARDWARE_IDENTITY_PATH, {})
    if isinstance(identity, dict):
        key = identity.get("identity_key")
        if isinstance(key, str) and key:
            return key
    return None


def verify_chain() -> tuple[bool, str]:
    """Validate ring presence, status, hashes, and predecessor linkage."""
    payload = load_json(INNOCENCE_CHAIN_PATH, None)
    if not isinstance(payload, dict):
        return False, "invalid_json"

    rings = payload.get("rings")
    if not isinstance(rings, list) or not rings:
        return False, "no_rings"

    previous_hash = None
    for index, ring in enumerate(rings):
        if not isinstance(ring, dict):
            return False, f"invalid_ring_{index}"
        if ring.get("integrity_status") != "PASS":
            return False, f"integrity_fail_{index}"
        ring_hash = ring.get("ring_hash")
        if not ring_hash:
            return False, f"missing_hash_{index}"
        if index > 0 and ring.get("prev_ring_hash") != previous_hash:
            return False, f"linkage_fail_{index}"
        previous_hash = ring_hash
    return True, "ok"


def load_agents() -> dict:
    """
    Return summary of known agents from relational memory.
    Looks for agent_id, actor_id, or event_id (excluding EVT-*).
    """
    mem = load_json(RELATIONAL_MEMORY_PATH, None)
    if not isinstance(mem, dict):
        return {"agents": [], "node_count": 0, "note": "relational_memory unavailable"}

    agents = set()
    nodes = mem.get("nodes")
    if not isinstance(nodes, list):
        return {"agents": [], "node_count": 0, "note": "nodes field is not a list"}

    for node in nodes:
        if not isinstance(node, dict):
            continue
        # البحث عن أي حقل يحمل معرف الوكيل
        agent_id = node.get("agent_id") or node.get("actor_id") or node.get("event_id")
        if agent_id and isinstance(agent_id, str) and not agent_id.startswith("EVT-"):
            agents.add(agent_id)

    return {
        "agents": sorted(list(agents)),
        "node_count": len(nodes),
        "note": "Agents are inferred from relational memory nodes." if agents else "No agents found.",
    }


def load_events(path_query: str) -> dict:
    """
    Read events from ring_storage.jsonl, filtered by agent_id or actor_id.
    Supports query parameters: agent_id (or actor_id) and limit (max 500).
    Reads only the last 2000 lines for performance.
    """
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(path_query)
    params = parse_qs(parsed.query)
    actor_filter = params.get("agent_id", [None])[0] or params.get("actor_id", [None])[0]

    try:
        limit = int(params.get("limit", [50])[0])
        limit = max(1, min(limit, 500))  # فرض حد أقصى 500
    except ValueError:
        limit = 50

    events = []
    if not RING_STORAGE_PATH.exists():
        return {"count": 0, "events": [], "note": "ring_storage.jsonl not found"}

    # قراءة آخر 2000 سطر فقط لتجنب استهلاك الذاكرة
    try:
        with open(RING_STORAGE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[-2000:]
    except OSError:
        return {"count": 0, "events": [], "note": "error reading ring_storage"}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if actor_filter:
            # البحث عن agent_id أو actor_id في الحدث
            event_actor = event.get("agent_id") or event.get("actor_id")
            if event_actor != actor_filter:
                continue
        events.append(event)

    events = events[-limit:]
    return {"count": len(events), "events": events}


def create_server(host: str, port: int) -> http.server.ThreadingHTTPServer:
    """Create the threaded server using the supplied bind address."""
    return http.server.ThreadingHTTPServer((host, port), SovereignRequestHandler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8443)
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
