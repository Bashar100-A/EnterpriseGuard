#!/usr/bin/env python3
"""ADIE Independent Verifier — POC (P-STEP-02). Standalone. Offline. Zero-trust."""
import sys, json, hashlib, re
from pathlib import Path

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.exceptions import InvalidSignature
    import jcs as jcs_lib
except ImportError as e:
    print(f"ERROR: missing dependency: {e}", file=sys.stderr)
    sys.exit(2)

E001 = "E001_SIGNATURE_INVALID"
E002 = "E002_HASH_MISMATCH"
E003 = "E003_SCHEMA_VIOLATION"
E004 = "E004_JCS_MISMATCH"
E005 = "E005_ALG_UNSUPPORTED"
E006 = "E006_TIMESTAMP_INVALID"
E007 = "E007_VERSION_MISMATCH"
E008 = "E008_REPLAY_OR_EXPIRED"
E009 = "E009_UNICODE_INVALID"
E010 = "E010_JSON_DUPLICATE_KEY"

PROTO_NAME = "ADIE"
PROTO_VERSION = "1.0"
SIG_ALGS = {"RSA-2048-PKCS1v15-SHA256"}
FP_ALGS = {"RFC6962-SHA256"}
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

def fail(code, d=None):
    print(f"INVALID: {code}" + (f" ({d})" if d else ""))
    sys.exit(1)

def ok():
    print("VALID")
    sys.exit(0)

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

def dedup(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise ValueError(f"duplicate key: {k}")
        seen.add(k)
    return dict(pairs)

def main():
    if len(sys.argv) != 3:
        print("Usage: verify.py <cert.json> <pubkey.pem>", file=sys.stderr)
        sys.exit(2)

    cert_path, key_path = sys.argv[1], sys.argv[2]

    # Read as RAW BYTES (no text-mode newline translation).
    # This is required for OS-agnostic behavior: Windows text mode
    # translates CRLF<->LF, which can alter the parsed content.
    try:
        raw_bytes = Path(cert_path).read_bytes()
    except Exception as e:
        fail(E003, f"read: {e}")

    # Strip UTF-8 BOM if present (some Windows tools add it).
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raw_bytes = raw_bytes[3:]

    # Decode as strict UTF-8. No newline translation.
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        fail(E009, f"utf-8 decode at byte {e.start}")

    # Sanity check: report CRLF presence but do not reject
    # (JSON treats CR/LF/CRLF identically as whitespace).
    # This is informational only.
    if b"\r\n" in raw_bytes:
        pass  # accepted; JCS is immune to structural whitespace

    try:
        cert = json.loads(raw, object_pairs_hook=dedup)
    except ValueError as e:
        if "duplicate key" in str(e):
            fail(E010, str(e))
        fail(E003, f"json: {e}")

    for s in walk_strings(cert):
        if not unicode_ok(s):
            fail(E009)

    for f in ("protocol", "decision_contract", "integrity", "issuer", "issued_at", "signature"):
        if f not in cert:
            fail(E003, f"missing: {f}")

    proto = cert["protocol"]
    if proto.get("name") != PROTO_NAME:
        fail(E007, f"name={proto.get('name')}")
    if proto.get("version") != PROTO_VERSION:
        fail(E007, f"version={proto.get('version')}")

    sig = cert["signature"]
    if sig.get("algorithm") not in SIG_ALGS:
        fail(E005, f"alg={sig.get('algorithm')}")

    integ = cert["integrity"]
    if integ.get("algorithm") not in FP_ALGS:
        fail(E005, f"fp_alg={integ.get('algorithm')}")

    issued_at = cert["issued_at"]
    if not isinstance(issued_at, str) or not TS_RE.match(issued_at):
        fail(E006, f"issued_at={issued_at}")

    contract = cert["decision_contract"]
    try:
        canonical = jcs_lib.canonicalize(contract)
    except Exception as e:
        fail(E004, f"jcs: {e}")

    recomputed_hash = "sha256:" + sha256_hex(canonical)
    if recomputed_hash != integ.get("decision_contract_content_hash"):
        fail(E002, "content_hash")

    ev = integ.get("referenced_event_hashes", [])
    evd = integ.get("referenced_evidence_hashes", [])
    leaves = []
    for h in list(ev) + list(evd):
        if not isinstance(h, str) or not h.startswith("sha256:") or len(h) != 71:
            fail(E003, f"bad hash: {h}")
        try:
            leaves.append(bytes.fromhex(h[7:]))
        except ValueError:
            fail(E003, f"bad hex: {h}")
    leaves.append(bytes.fromhex(recomputed_hash[7:]))
    root = merkle_root(leaves)
    recomputed_fp = "sha256:" + sha256_hex(b"ADIE:EMISSION:v1:" + root)
    if recomputed_fp != integ.get("emission_fingerprint"):
        fail(E002, "fingerprint")

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
        fail(E001, f"load key: {e}")

    sv = sig["value"]
    if sv.startswith("hex:"):
        sv = sv[4:]
    try:
        sb = bytes.fromhex(sv)
    except ValueError:
        fail(E001, "bad sig hex")

    try:
        pub.verify(sb, payload, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        fail(E001, "signature does not verify")
    except Exception as e:
        fail(E001, str(e))

    ok()

if __name__ == "__main__":
    main()
