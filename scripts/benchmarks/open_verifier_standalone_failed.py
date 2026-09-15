#!/usr/bin/env python3
"""
Standalone AAAC chain verifier.
MIT License.

This script verifies the innocence chain using only public data.
It requires:
  - innocence_chain.json
  - hardware_identity.json (for identity_key)
  - public_key.pem (RSA public key)
  - genesis_public_key.pem (Genesis RSA public key)
"""

import os
import sys
import json
import hashlib
import subprocess
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

CHAIN_PATH = ROOT / "tools" / "innocence_chain.json"
IDENTITY_PATH = ROOT / "tools" / "hardware_identity.json"
PUBLIC_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "public_key.pem"
GENESIS_PUBLIC_KEY_PATH = ROOT / "tools" / "genesis_public_key.pem"
GENESIS_PREV_HASH = "genesis"


def load_json(path: Path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _verify_signature(data: str, signature_hex: str, public_key_path: Path) -> bool:
    """Verify RSA SHA-256 signature using openssl."""
    if not signature_hex or not public_key_path.exists():
        return False
    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        f.write(data)
        data_file = f.name
    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".sig") as f:
        f.write(sig_bytes)
        sig_file = f.name
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(public_key_path),
             "-signature", sig_file, data_file],
            capture_output=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0 and b"Verified OK" in result.stdout
    except Exception:
        return False
    finally:
        Path(data_file).unlink(missing_ok=True)
        Path(sig_file).unlink(missing_ok=True)


def compute_ring_hash(prev_hash, identity_key, integrity_status, snapshot,
                      realtime_events_hash, chain_id, agent_events_hash):
    combined = f"{prev_hash}{identity_key}{integrity_status}{snapshot}{realtime_events_hash}{chain_id}{agent_events_hash}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify_chain():
    identity = load_json(IDENTITY_PATH)
    if not identity or "identity_key" not in identity:
        return False, "identity_key missing"
    identity_key = identity["identity_key"]

    chain = load_json(CHAIN_PATH)
    if not chain:
        return False, "chain missing"
    rings = chain.get("rings")
    if not isinstance(rings, list) or not rings:
        return False, "no rings"

    first_ring = rings[0]
    chain_id = first_ring.get("chain_id")
    genesis_signature = first_ring.get("genesis_signature")
    if not chain_id or not genesis_signature:
        return False, "genesis missing"

    # Verify genesis signature
    if not _verify_signature(chain_id, genesis_signature, GENESIS_PUBLIC_KEY_PATH):
        return False, "genesis signature invalid"

    prev_hash = GENESIS_PREV_HASH
    for i, ring in enumerate(rings):
        if i == 0:
            if ring.get("prev_ring_hash") != GENESIS_PREV_HASH:
                return False, f"ring 0 prev hash wrong"
        else:
            if ring.get("prev_ring_hash") != prev_hash:
                return False, f"linkage break at ring {i}"

        if ring.get("chain_id") != chain_id:
            return False, f"chain_id mismatch at ring {i}"

        required = ["prev_ring_hash", "integrity_status", "relational_memory_snapshot",
                    "realtime_events_hash", "agent_events_hash", "ring_hash", "signature"]
        for field in required:
            if field not in ring:
                return False, f"missing field {field} at ring {i}"

        expected_hash = compute_ring_hash(
            ring["prev_ring_hash"],
            identity_key,
            ring["integrity_status"],
            ring["relational_memory_snapshot"],
            ring.get("realtime_events_hash", "none"),
            ring["chain_id"],
            ring.get("agent_events_hash", "none"),
        )
        if ring["ring_hash"] != expected_hash:
            return False, f"hash mismatch at ring {i}"

        if ring.get("signature"):
            if not _verify_signature(ring["ring_hash"], ring["signature"], PUBLIC_KEY_PATH):
                return False, f"signature invalid at ring {i}"
        else:
            return False, f"unsigned ring {i}"

        prev_hash = ring["ring_hash"]

    return True, "VALID"


if __name__ == "__main__":
    valid, reason = verify_chain()
    if valid:
        print("VALID: chain is authentic")
        sys.exit(0)
    else:
        print(f"INVALID: {reason}")
        sys.exit(1)
