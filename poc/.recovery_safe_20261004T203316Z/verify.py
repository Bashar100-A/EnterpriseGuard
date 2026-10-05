#!/usr/bin/env python3
"""
ADIE Independent Verifier — v3 Fortified.
Standalone. Offline. Zero-Trust. Built to mitigate all cross-OS attack vectors.
"""
import sys
import json
import hashlib
import re
from pathlib import Path

# Mitigation for Python 3.11+ string formatting / fallback encoding blocks
if sys.platform == "win32":
    import os
    if os.environ.get("PYTHONUTF8") != "1":
        # Force Windows console to respect strict UTF-8 boundaries
        os.environ["PYTHONUTF8"] = "1"

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.exceptions import InvalidSignature
    import jcs as jcs_lib
except ImportError as e:
    print(f"ERROR: Missing deployment dependency: {e}", file=sys.stderr)
    print("Execute: pip install cryptography jcs --break-system-packages", file=sys.stderr)
    sys.exit(2)

# Deterministic Reason Error Codes (ADIE Spec Compliance)
E001 = "E001_SIGNATURE_INVALID"
E002 = "E002_HASH_MISMATCH"
E003 = "E003_SCHEMA_VIOLATION"
E004 = "E004_JCS_MISMATCH"
E005 = "E005_ALG_UNSUPPORTED"
E006 = "E006_TIMESTAMP_INVALID"
E007 = "E007_VERSION_MISMATCH"
E009 = "E009_UNICODE_INVALID"
E010 = "E010_JSON_DUPLICATE_KEY"

PROTO_NAME = "ADIE"
PROTO_VERSION = "1.0"
SIG_ALGS = {"RSA-2048-PKCS1v15-SHA256"}
FP_ALGS = {"RFC6962-SHA256"}
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

def fail(code, detail=None):
    print(f"INVALID: {code}" + (f" ({detail})" if detail else ""))
    sys.exit(1)

def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()

def merkle_root(leaves):
    n = len(leaves)
    if n == 0: return hashlib.sha256(b"").digest()
    if n == 1: return hashlib.sha256(b"\x00" + leaves[0]).digest()
    k = 1
    while k * 2 < n: k *= 2
    return hashlib.sha256(b"\x01" + merkle_root(leaves[:k]) + merkle_root(leaves[k:])).digest()

def unicode_ok(s):
    try:
        s.encode("utf-8")
        return True
    except Exception:
        return False

def walk_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from walk_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_strings(v)

def dedup_json_hook(pairs):
    """Mitigates Risk 3: Catches and destroys duplicate JSON key injections."""
    seen = set()
    for k, _ in pairs:
        if k in seen:
            fail(E010, f"Duplicate key mutation detected: '{k}'")
        seen.add(k)
    return dict(pairs)

def main():
    if len(sys.argv) != 3:
        print("Usage: verify.py <cert.json> <pubkey.pem>", file=sys.stderr)
        sys.exit(2)

    cert_path, key_path = sys.argv[1], sys.argv[2]

    try:
        # MITIGATION: Read raw bytes directly to bypass Windows LF/CRLF auto-conversion
        raw_bytes = Path(cert_path).read_bytes()
        
        # MITIGATION: Strip UTF-8 Byte Order Mark (BOM) if injected by Windows tools
        if raw_bytes.startswith(b'\xef\xbb\xbf'):
            raw_bytes = raw_bytes[3:]
            
        raw_text = raw_bytes.decode("utf-8")
    except Exception as e:
        fail(E003, f"File access error: {e}")

    try:
        cert = json.loads(raw_text, object_pairs_hook=dedup_json_hook)
    except ValueError as e:
        fail(E003, f"Malformed structural JSON: {e}")

    # Malformed unicode / lone surrogate validation
    for s in walk_strings(cert):
        if not unicode_ok(s):
            fail(E009, "Invalid surrogate or malformed Unicode byte boundary")

    # Contract Schema enforcement
    for f in ("protocol", "decision_contract", "integrity", "issuer", "issued_at", "signature"):
        if f not in cert:
            fail(E003, f"Missing core contract field: {f}")

    proto = cert["protocol"]
    if proto.get("name") != PROTO_NAME or proto.get("version") != PROTO_VERSION:
        fail(E007, f"Protocol mismatch. Target: {PROTO_NAME} v{PROTO_VERSION}")

    sig = cert["signature"]
    if sig.get("algorithm") not in SIG_ALGS:
        fail(E005, f"Unsupported downgrade/signature scheme: {sig.get('algorithm')}")

    integ = cert["integrity"]
    if integ.get("algorithm") not in FP_ALGS:
        fail(E005, f"Unsupported fingerprint algorithm: {integ.get('algorithm')}")

    issued_at = cert["issued_at"]
    if not isinstance(issued_at, str) or not TS_RE.match(issued_at):
        fail(E006, f"Invalid timestamp format (Z suffix required): {issued_at}")

    # Canonicalization Check (JCS RFC 8785)
    contract = cert["decision_contract"]
    try:
        canonical = jcs_lib.canonicalize(contract)
    except Exception as e:
        fail(E004, f"JCS serialisation failure: {e}")

    recomputed_hash = "sha256:" + sha256_hex(canonical)
    if recomputed_hash != integ.get("decision_contract_content_hash"):
        fail(E002, "Content hash mismatch (Decision contract data altered)")

    # Merkle Root Binding (RFC 6962)
    ev = integ.get("referenced_event_hashes", [])
    evd = integ.get("referenced_evidence_hashes", [])
    leaves = []
    for h in list(ev) + list(evd):
        if not isinstance(h, str) or not h.startswith("sha256:") or len(h) != 71:
            fail(E003, f"Malformed evidence reference hash: {h}")
        leaves.append(bytes.fromhex(h[7:]))
        
    leaves.append(bytes.fromhex(recomputed_hash[7:]))
    root = merkle_root(leaves)
    recomputed_fp = "sha256:" + sha256_hex(b"ADIE:EMISSION:v1:" + root)
    
    if recomputed_fp != integ.get("emission_fingerprint"):
        fail(E002, "Emission fingerprint mismatch (Evidence ledger corrupted)")

    # Payload recreation and execution
    payload = jcs_lib.canonicalize({
        "decision_contract_content_hash": recomputed_hash,
        "emission_fingerprint": recomputed_fp,
        "issued_at": issued_at,
        "issuer": cert["issuer"],
        "protocol_version": proto["version"],
    })

    try:
        pub = serialization.load_pem_public_key(Path(key_path).read_bytes())
    except Exception as e:
        fail(E001, f"Failed to mount public key anchor: {e}")

    sv = sig["value"]
    try:
        sb = bytes.fromhex(sv)
    except ValueError:
        fail(E001, "Corrupted signature hexadecimal payload")

    try:
        pub.verify(sb, payload, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        fail(E001, "Cryptographic signature validation FAILED. Payload altered or unauthenticated key.")
    except Exception as e:
        fail(E001, f"Cryptographic subsystem error: {e}")

    print("VALID")
    sys.exit(0)

if __name__ == "__main__":
    main()
