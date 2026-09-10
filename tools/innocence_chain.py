#!/usr/bin/env python3
"""
EnterpriseGuard Innocence Chain — Renewed Innocence Component (with Digital Signatures)

Generates a continuous chain of proof rings. Each ring contains:
- ring_hash: sha256(prev_ring_hash + identity_key + integrity_status + snapshot + realtime_events_hash + chain_id)
- relational_memory_snapshot: last event_id from relational memory
- integrity_status: result of integrity_monitor --check (must be PASS or FAIL)
- realtime_events_hash: SHA256 of the last line in realtime_events.jsonl (or "none" if no events)
- signature: RSA-2048 digital signature of ring_hash (using private key)
- chain_id: UUID identifying the chain (only first ring has genesis_signature)

The chain is time-independent and bound to the hardware identity.
Output: tools/innocence_chain.json (chmod 444)
Modifying any old ring breaks all subsequent rings.

Governed by DC-050, DC-052, DC-055, and DC-068.
"""

from __future__ import annotations

import sys

# Mandatory: prevent bytecode generation
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import (
    HARDWARE_IDENTITY_PATH,
    RELATIONAL_MEMORY_PATH,
    INNOCENCE_CHAIN_PATH,
    REALTIME_EVENTS_PATH,
    ACTIVITY_LOG_PATH,
)

from tools.signing_backend import sign_bytes, verify_signature_hex, sign_genesis_chain_id_hex, verify_genesis_signature_hex

IDENTITY_PATH = HARDWARE_IDENTITY_PATH
RELATIONAL_PATH = RELATIONAL_MEMORY_PATH
CHAIN_PATH = INNOCENCE_CHAIN_PATH
REALTIME_EVENTS_PATH = REALTIME_EVENTS_PATH

# Paths for signing keys (outside project, in user's home directory)
PRIVATE_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "private_key.pem"
PUBLIC_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "public_key.pem"
GENESIS_PUBLIC_KEY_PATH = ROOT / "tools" / "genesis_public_key.pem"
GENESIS_PRIVATE_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "genesis_private_key.pem"
SYSTEM_PUBLIC_KEY_PATH = Path("/etc/enterpriseguard/public_key.pem")
SYSTEM_GENESIS_PUBLIC_KEY_PATH = Path("/etc/enterpriseguard/genesis_public_key.pem")
GENESIS_PREV_HASH = "genesis"


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 with Z suffix."""
    from tools.time_utils import utc_now
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json_file(path: Path) -> dict:
    """Read and return JSON content from a file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_identity_key() -> str:
    """Read identity_key from hardware_identity.json."""
    data = read_json_file(IDENTITY_PATH)
    key = data.get("identity_key")
    if not key or not isinstance(key, str):
        raise ValueError("hardware_identity.json missing identity_key")
    return key


def get_last_relational_node_id() -> str:
    """Return last event_id from relational_memory.json, or 'none' if empty or missing."""
    if not RELATIONAL_PATH.exists():
        return "none"
    data = read_json_file(RELATIONAL_PATH)
    nodes = data.get("nodes", []) if isinstance(data, dict) else data
    if not nodes:
        return "none"
    last_node = nodes[-1]
    if isinstance(last_node, dict):
        event_id = last_node.get("event_id")
        return event_id if event_id else "none"
    return "none"


def get_last_realtime_event_hash() -> str:
    """Return SHA256 of the last realtime event, or 'none' if no events exist."""
    if not REALTIME_EVENTS_PATH.exists():
        return "none"
    try:
        with open(REALTIME_EVENTS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return "none"
        last_line = lines[-1].strip()
        return hashlib.sha256(last_line.encode("utf-8")).hexdigest()
    except Exception:
        return "none"
def get_last_agent_events_hash() -> str:
    """Compute SHA-256 of the last line in ring_storage.jsonl, or 'none' if missing/empty."""
    try:
        agent_events_path = ROOT / "tools" / "ring_storage.jsonl"
        if not agent_events_path.exists():
            return "none"
        last_line = None
        with open(agent_events_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line
        if not last_line:
            return "none"
        return hashlib.sha256(last_line.encode('utf-8')).hexdigest()
    except Exception:
        return "none"



def get_rfc3161_timestamp(data: str):
    """Request RFC3161 timestamp from a pool of TSA providers, returning (token, provider)."""
    import subprocess
    import requests
    import base64
    from urllib.parse import urlparse

    # قراءة قائمة المزودين من متغير البيئة (مفصولة بفواصل) أو استخدام الافتراضية
    providers_str = os.environ.get("AAAC_TSA_URLS", "http://time.certum.pl,https://freetsa.org/tsr,https://zeitstempel.dfn.de")
    providers = [p.strip() for p in providers_str.split(",") if p.strip()]

    # توليد استعلام RFC3161 مرة واحدة
    try:
        query = subprocess.run(
            ["openssl", "ts", "-query", "-data", "-", "-sha256"],
            input=data.encode("utf-8"),
            capture_output=True,
            timeout=10,
            check=True,
        ).stdout
    except Exception as e:
        print(f"Failed to create TSA query: {e}", file=sys.stderr)
        return "", ""

    last_error = None
    for tsa_url in providers:
        try:
            headers = {"Content-Type": "application/timestamp-query"}
            resp = requests.post(tsa_url, data=query, headers=headers, timeout=15)
            if resp.status_code == 200:
                token_b64 = base64.b64encode(resp.content).decode("ascii")
                return token_b64, tsa_url
            else:
                last_error = f"status {resp.status_code}"
        except Exception as e:
            last_error = str(e)
            continue

    print(f"All TSA providers failed. Last error: {last_error}", file=sys.stderr)
    return "", ""


def run_integrity_check() -> str:
    """
    Run integrity_monitor --check and return either "PASS" or "FAIL".
    Raises RuntimeError if the result cannot be determined.
    """
    try:
        result = subprocess.run(
            ["python3", "-B", "tools/integrity_monitor.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        output = (result.stdout or "").strip()
        if not output:
            raise RuntimeError("integrity_monitor returned empty output")

        try:
            data = json.loads(output)
            if isinstance(data, dict):
                status = data.get("status")
                if status in {"PASS", "FAIL"}:
                    return status
                raise RuntimeError(f"Invalid status in JSON: {status}")
        except json.JSONDecodeError:
            upper = output.upper()
            if "PASS" in upper:
                return "PASS"
            if "FAIL" in upper:
                return "FAIL"
            raise RuntimeError(f"Unable to determine integrity status from output: {output[:200]}")

        raise RuntimeError("Integrity status missing from JSON output")

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("integrity_monitor timed out") from exc
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"integrity_monitor execution failed: {exc}") from exc

def _get_integrity_status() -> str:
    status = run_integrity_check()
    if status not in {"PASS", "FAIL"}:
        raise ValueError(f"Invalid integrity status: {status}")
    return status


def load_chain() -> List[Dict]:
    if not CHAIN_PATH.exists():
        return []
    try:
        data = json.loads(CHAIN_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rings = data.get("rings", [])
            if not isinstance(rings, list):
                raise RuntimeError("Chain file 'rings' field is not a list")
            return rings
        if isinstance(data, list):
            return data
        raise RuntimeError("Invalid chain file structure")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Chain file is corrupt: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to load chain: {exc}") from exc


def save_chain(rings: List[Dict]) -> None:
    payload = {
        "schema_version": "1.0",
        "rings": rings,
        "last_updated": utc_now_iso(),
    }
    CHAIN_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".innocence_chain.",
        suffix=".tmp",
        dir=str(CHAIN_PATH.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        os.chmod(tmp_path, 0o444)
        os.replace(tmp_path, CHAIN_PATH)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def sign_ring_hash(ring_hash: str) -> str:
    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":
        return hashlib.sha256(("mock:" + ring_hash).encode("utf-8")).hexdigest()
    if os.environ.get("AAAC_SIGNING_BACKEND") in ("aws_kms", "tpm"):
        return sign_bytes(ring_hash)
    if not PRIVATE_KEY_PATH.exists():
        raise RuntimeError("Private key not found; cannot sign ring.")
    with tempfile.TemporaryDirectory() as tmpdir:
        data_file = Path(tmpdir) / "data.bin"
        sig_file = Path(tmpdir) / "sig.bin"
        data_file.write_bytes(bytes.fromhex(ring_hash))
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(PRIVATE_KEY_PATH),
             "-out", str(sig_file), str(data_file)],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"OpenSSL signing failed: {result.stderr.decode().strip()}")
        return sig_file.read_bytes().hex()


def verify_ring_signature(ring_hash: str, signature_hex: str) -> bool:
    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":
        expected = hashlib.sha256(("mock:" + ring_hash).encode("utf-8")).hexdigest()
        return signature_hex == expected
    if os.environ.get("AAAC_SIGNING_BACKEND") in ("aws_kms", "tpm"):
        return verify_signature_hex(ring_hash, signature_hex)
    pub_key = PUBLIC_KEY_PATH
    if not pub_key.exists() and SYSTEM_PUBLIC_KEY_PATH.exists():
        pub_key = SYSTEM_PUBLIC_KEY_PATH
    if not pub_key.exists():
        raise RuntimeError("Public key not found; cannot verify signature.")

    try:
        signature = bytes.fromhex(signature_hex)
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.bin"
            sig_file = Path(tmpdir) / "sig.bin"
            data_file.write_bytes(bytes.fromhex(ring_hash))
            sig_file.write_bytes(signature)
            result = subprocess.run(
                ["openssl", "dgst", "-sha256", "-verify", str(pub_key),
                 "-signature", str(sig_file), str(data_file)],
                capture_output=True,
                timeout=10,
                check=False,
            )
            return result.returncode == 0 and b"Verified OK" in result.stdout
    except Exception:
        return False


def sign_genesis_chain_id(chain_id: str) -> str:
    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":
        return hashlib.sha256(("genesis-mock:" + chain_id).encode("utf-8")).hexdigest()
    if os.environ.get("AAAC_SIGNING_BACKEND") in ("aws_kms", "tpm"):
        return sign_genesis_chain_id_hex(chain_id)
    if not GENESIS_PRIVATE_KEY_PATH.exists():
        raise RuntimeError("Genesis private key not found")
    with tempfile.TemporaryDirectory() as tmpdir:
        data_file = Path(tmpdir) / "chain_id.bin"
        sig_file = Path(tmpdir) / "chain_id.sig"
        data_file.write_text(chain_id, encoding="utf-8")
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(GENESIS_PRIVATE_KEY_PATH),
             "-out", str(sig_file), str(data_file)],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Genesis signing failed: {result.stderr.decode().strip()}")
        return sig_file.read_bytes().hex()


def verify_genesis_signature(chain_id: str, signature_hex: str) -> bool:
    if os.environ.get("AAAC_SIGNING_BACKEND") == "mock":
        expected = hashlib.sha256(("genesis-mock:" + chain_id).encode("utf-8")).hexdigest()
        return signature_hex == expected
    if os.environ.get("AAAC_SIGNING_BACKEND") in ("aws_kms", "tpm"):
        return verify_genesis_signature_hex(chain_id, signature_hex)
    pub_key = GENESIS_PUBLIC_KEY_PATH
    if not pub_key.exists() and SYSTEM_GENESIS_PUBLIC_KEY_PATH.exists():
        pub_key = SYSTEM_GENESIS_PUBLIC_KEY_PATH
    if not pub_key.exists():
        return False  # Key missing, cannot verify
    try:
        signature = bytes.fromhex(signature_hex)
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "chain_id.bin"
            sig_file = Path(tmpdir) / "chain_id.sig"
            data_file.write_text(chain_id, encoding="utf-8")
            sig_file.write_bytes(signature)
            result = subprocess.run(
                ["openssl", "dgst", "-sha256", "-verify", str(pub_key),
                 "-signature", str(sig_file), str(data_file)],
                capture_output=True,
                timeout=10,
                check=False,
            )
            return result.returncode == 0 and b"Verified OK" in result.stdout
    except Exception:
        return False


def compute_ring_hash(prev_hash: str, identity_key: str,
                      integrity_status: str, snapshot: str,
                      realtime_events_hash: str = "none",
                      chain_id: str = "",
                      agent_events_hash: str = "none") -> str:
    """Compute ring hash with optional chain_id and agent events hash."""
    if not prev_hash:
        raise ValueError("prev_ring_hash cannot be empty")
    if not identity_key:
        raise ValueError("identity_key cannot be empty")
    if integrity_status not in {"PASS", "FAIL"}:
        raise ValueError("integrity_status must be PASS or FAIL")
    if not snapshot:
        raise ValueError("relational_memory_snapshot cannot be empty")
    if not realtime_events_hash:
        raise ValueError("realtime_events_hash cannot be empty")
    if chain_id is None:
        chain_id = ""
    if not agent_events_hash:
        raise ValueError("agent_events_hash cannot be empty")

    combined = f"{prev_hash}{identity_key}{integrity_status}{snapshot}{realtime_events_hash}{chain_id}{agent_events_hash}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()
def compute_ring_hash(prev_hash: str, identity_key: str,
                      integrity_status: str, snapshot: str,
                      realtime_events_hash: str = "none",
                      chain_id: str = "",
                      agent_events_hash: str = "none") -> str:
    """Compute ring hash with optional chain_id and agent events hash."""
    if not prev_hash:
        raise ValueError("prev_ring_hash cannot be empty")
    if not identity_key:
        raise ValueError("identity_key cannot be empty")
    if integrity_status not in {"PASS", "FAIL"}:
        raise ValueError("integrity_status must be PASS or FAIL")
    if not snapshot:
        raise ValueError("relational_memory_snapshot cannot be empty")
    if not realtime_events_hash:
        raise ValueError("realtime_events_hash cannot be empty")
    if chain_id is None:
        chain_id = ""
    if not agent_events_hash:
        raise ValueError("agent_events_hash cannot be empty")

    combined = f"{prev_hash}{identity_key}{integrity_status}{snapshot}{realtime_events_hash}{chain_id}{agent_events_hash}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()

def _verify_rings(rings: List[Dict], identity_key: str, allow_unsigned: bool = False) -> bool:
    if not rings:
        return False

    first_ring = rings[0]
    chain_id = first_ring.get("chain_id")
    genesis_signature = first_ring.get("genesis_signature")

    if not chain_id or not isinstance(chain_id, str):
        return False
    if not genesis_signature or not isinstance(genesis_signature, str):
        return False

    if not verify_genesis_signature(chain_id, genesis_signature):
        return False

    prev_hash = GENESIS_PREV_HASH
    for i, ring in enumerate(rings):
        if i == 0:
            if ring.get("prev_ring_hash") != GENESIS_PREV_HASH:
                return False
        else:
            if ring.get("prev_ring_hash") != rings[i - 1].get("ring_hash"):
                return False

        if ring.get("chain_id") != chain_id:
            return False

        ring_prev = ring.get("prev_ring_hash")
        ring_status = ring.get("integrity_status")
        ring_snapshot = ring.get("relational_memory_snapshot")
        ring_realtime_hash = ring.get("realtime_events_hash", "none")
        ring_agent_events_hash = ring.get("agent_events_hash", "none")
        ring_signature = ring.get("signature")

        if not isinstance(ring_prev, str) or not ring_prev:
            return False
        if ring_status not in {"PASS", "FAIL"}:
            return False
        if not isinstance(ring_snapshot, str) or not ring_snapshot:
            return False
        if not isinstance(ring_realtime_hash, str) or not ring_realtime_hash:
            return False
        if not isinstance(ring_agent_events_hash, str) or not ring_agent_events_hash:
            return False

        try:
            expected_hash = compute_ring_hash(
                ring_prev,
                identity_key,
                ring_status,
                ring_snapshot,
                ring_realtime_hash,
                chain_id,
                ring_agent_events_hash,
            )
        except ValueError:
            return False

        if ring.get("ring_hash") != expected_hash:
            return False

        if ring_signature:
            if not verify_ring_signature(ring.get("ring_hash"), ring_signature):
                return False
        else:
            if not allow_unsigned:
                return False

    return True


def verify_chain(allow_unsigned: bool = False) -> bool:
    if not CHAIN_PATH.exists():
        raise RuntimeError("Innocence chain not initialized (file missing)")

    identity_key = get_identity_key()
    rings = load_chain()
    if not rings:
        raise RuntimeError("Innocence chain is empty (no rings)")

    return _verify_rings(rings, identity_key, allow_unsigned)


def get_chain_status() -> str:
    if not CHAIN_PATH.exists():
        return "MISSING"

    try:
        rings = load_chain()
        if not rings:
            return "EMPTY"
        identity_key = get_identity_key()
        if _verify_rings(rings, identity_key, allow_unsigned=False):
            return "VALID"
        else:
            return "TAMPERED"
    except Exception:
        return "CORRUPT"




def verify_rfc3161_token(token_b64: str, data_hex: str = None) -> bool:
    """Verify RFC3161 token structure and optionally signature with TSA certificate."""
    import base64
    import subprocess
    import tempfile
    from pathlib import Path as _Path
    if not token_b64:
        return False
    token_file = None
    data_file = None
    try:
        token_bytes = base64.b64decode(token_b64)
        fd, token_file = tempfile.mkstemp(suffix='.tsr')
        with os.fdopen(fd, 'wb') as f:
            f.write(token_bytes)

        cmd = ["openssl", "ts", "-reply", "-in", token_file]
        # إذا توفرت شهادة CA خارجية، أضفها للتحقق من التوقيع
        ca_file = os.environ.get("AAAC_TSA_CAFILE")
        if ca_file and _Path(ca_file).exists():
            cmd += ["-CAfile", ca_file]
        # إذا مررنا data_hex (الهاش الأصلي)، يمكننا التحقق من تطابق الرسالة
        if data_hex:
            fd2, data_file = tempfile.mkstemp(suffix='.txt')
            with os.fdopen(fd2, 'wb') as f:
                f.write(bytes.fromhex(data_hex))
            cmd += ["-data", data_file]
        cmd += ["-text"]
        result = subprocess.run(cmd, capture_output=True, timeout=15, check=False)
        return result.returncode == 0
    except Exception:
        return False
    finally:
        if token_file and os.path.exists(token_file):
            os.unlink(token_file)
        if data_file and os.path.exists(data_file):
            os.unlink(data_file)

def generate_ring() -> dict:
    rings = load_chain()

    chain_id = None
    if rings:
        chain_id = rings[0].get("chain_id")
        if not chain_id:
            raise RuntimeError("Existing chain does not contain a valid chain_id (legacy chain unsupported)")
    else:
        # Check that Genesis public key exists before creating new chain
        if not GENESIS_PUBLIC_KEY_PATH.exists() and not SYSTEM_GENESIS_PUBLIC_KEY_PATH.exists():
            raise RuntimeError("Genesis public key not found; cannot create verifiable chain")
        chain_id = uuid.uuid4().hex

    if rings:
        identity_key_for_verify = get_identity_key()
        if not _verify_rings(rings, identity_key_for_verify, allow_unsigned=False):
            raise RuntimeError("Cannot generate new ring: existing chain is corrupted")

    identity_key = get_identity_key()
    snapshot = get_last_relational_node_id()
    integrity_status = _get_integrity_status()
    realtime_events_hash = get_last_realtime_event_hash()
    agent_events_hash = get_last_agent_events_hash()

    prev_hash = rings[-1].get("ring_hash") if rings else GENESIS_PREV_HASH
    rfc3161_token, tsa_provider = get_rfc3161_timestamp(agent_events_hash)
    tsa_verified = verify_rfc3161_token(rfc3161_token, agent_events_hash) if rfc3161_token else False
    ring_hash = compute_ring_hash(
        prev_hash, identity_key, integrity_status, snapshot,
        realtime_events_hash, chain_id, agent_events_hash
    )
    signature = sign_ring_hash(ring_hash)

    ring = {
        "ring_hash": ring_hash,
        "prev_ring_hash": prev_hash,
        "integrity_status": integrity_status,
        "relational_memory_snapshot": snapshot,
        "realtime_events_hash": realtime_events_hash,
        "agent_events_hash": agent_events_hash,
        "rfc3161_token": rfc3161_token,
        "tsa_provider": tsa_provider,
        "tsa_verified": tsa_verified,
        "signature": signature,
        "chain_id": chain_id,
        "created_at": utc_now_iso(),
    }

    if not rings:
        ring["genesis_signature"] = sign_genesis_chain_id(chain_id)

    rings.append(ring)
    save_chain(rings)
    log_ring_event(ring_hash)

    return ring


def log_ring_event(ring_hash: str) -> None:
    try:
        from tools.audit_chain import append_activity
        from tools.time_utils import utc_now

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "innocence_chain",
                "status": "success",
                "details": f"innocence_ring_generated hash={ring_hash[:16]}...",
            },
            ACTIVITY_LOG_PATH,
        )
    except Exception as exc:
        print(f"WARNING: failed to log ring event: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Innocence Chain")
    parser.add_argument("--generate", action="store_true", help="Generate a new ring")
    parser.add_argument("--verify", action="store_true", help="Verify existing chain")
    parser.add_argument("--status", action="store_true", help="Show chain status")
    parser.add_argument("--allow-unsigned", action="store_true",
                        help="Allow unsigned rings during verification (for legacy chains)")
    args = parser.parse_args()

    if args.generate:
        try:
            ring = generate_ring()
            print(json.dumps(ring, indent=2, sort_keys=True))
            return 0
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if args.verify:
        try:
            if verify_chain(allow_unsigned=args.allow_unsigned):
                print("VERIFIED_OK")
                return 0
            else:
                print("VERIFICATION_FAILED")
                return 1
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if args.status:
        status = get_chain_status()
        print(status)
        return 0

    parser.print_usage(sys.stderr)
    print("error: one of --generate, --verify, or --status is required", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
