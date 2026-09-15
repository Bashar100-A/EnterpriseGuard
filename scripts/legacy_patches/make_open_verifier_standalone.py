import sys, shutil, tempfile, os
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True
ROOT = Path('.')

def backup_file(path):
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    b = path.with_name(f"{path.name}.bak_{ts}")
    shutil.copy2(path, b)
    return b

def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

file = ROOT / 'tools' / 'open_verifier.py'
backup_file(file)

standalone_code = '''#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2026 EnterpriseGuard ADIE Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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


def load_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def verify_signature(data: str, signature_hex: str, public_key: Path) -> bool:
    if not signature_hex or not public_key.exists():
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
            ["openssl", "dgst", "-sha256", "-verify", str(public_key),
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
                      realtime_hash, chain_id, agent_events_hash):
    combined = f"{prev_hash}{identity_key}{integrity_status}{snapshot}{realtime_hash}{chain_id}{agent_events_hash}".encode()
    return hashlib.sha256(combined).hexdigest()


def verify_chain():
    identity = load_json(IDENTITY_PATH)
    if not identity or "identity_key" not in identity:
        return False, "identity_key missing"
    identity_key = identity["identity_key"]

    payload = load_json(CHAIN_PATH)
    if not payload:
        return False, "chain missing"
    rings = payload.get("rings")
    if not isinstance(rings, list) or not rings:
        return False, "no rings"

    first = rings[0]
    chain_id = first.get("chain_id")
    genesis_sig = first.get("genesis_signature")
    if not chain_id or not genesis_sig:
        return False, "genesis missing"
    if not verify_signature(chain_id, genesis_sig, GENESIS_PUBLIC_KEY_PATH):
        return False, "genesis signature invalid"

    prev_hash = GENESIS_PREV_HASH
    for i, ring in enumerate(rings):
        if i == 0:
            if ring.get("prev_ring_hash") != GENESIS_PREV_HASH:
                return False, f"ring 0 prev hash wrong"
        else:
            if ring.get("prev_ring_hash") != prev_hash:
                return False, f"linkage fail at ring {i}"

        if ring.get("chain_id") != chain_id:
            return False, f"chain_id mismatch at ring {i}"

        r_prev = ring.get("prev_ring_hash")
        r_status = ring.get("integrity_status")
        r_snapshot = ring.get("relational_memory_snapshot")
        r_realtime_hash = ring.get("realtime_events_hash", "none")
        r_agent_hash = ring.get("agent_events_hash", "none")
        r_signature = ring.get("signature")
        ring_hash = ring.get("ring_hash")

        if not all([r_prev, r_status, r_snapshot, r_realtime_hash, r_agent_hash, ring_hash]):
            return False, f"missing field at ring {i}"

        expected_hash = compute_ring_hash(r_prev, identity_key, r_status, r_snapshot,
                                          r_realtime_hash, chain_id, r_agent_hash)
        if ring_hash != expected_hash:
            return False, f"hash mismatch at ring {i}"

        if r_signature:
            if not verify_signature(ring_hash, r_signature, PUBLIC_KEY_PATH):
                return False, f"signature invalid at ring {i}"
        else:
            if os.environ.get("ALLOW_UNSIGNED") != "1":
                return False, f"unsigned ring {i}"

        prev_hash = ring_hash

    return True, "VALID"


if __name__ == "__main__":
    valid, reason = verify_chain()
    print(f"{'VALID' if valid else 'INVALID'}: {reason}")
    sys.exit(0 if valid else 1)
'''

atomic_write(file, standalone_code)
print("Successfully created standalone open_verifier.py")
