"""ADIE vΩ — DCP 2.0 verifier pipeline (Phase 1)."""
import base64
import json

from .domain_hash import H_A
from .jcs import strict_load, canonical_bytes, CanonicalError
from .claim_root import compute_claim_root, claim_root_hex
from .binding import verify_binding, BindingError

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


REQUIRED_FIELDS = [
    "dcp_version", "claim_id", "issuer", "subject", "binding",
    "request", "context", "policy", "model", "data", "runtime",
    "output", "temporal", "evidence", "authoring",
    "proofs", "claim_root", "signature",
]

FIELD_NAMES = ["issuer", "subject", "request", "context", "policy",
               "model", "data", "runtime", "output", "binding",
               "temporal", "evidence", "authoring"]


class VerifyError(Exception):
    def __init__(self, code, msg=""):
        self.code = code
        super().__init__(f"{code}: {msg}")


def _fail(code, msg=""):
    raise VerifyError(code, msg)


def verify_dcp20(raw: bytes, public_key_pem: bytes,
                 expectation: dict | None = None) -> dict:
    # 1. decode + canonicalize
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _fail("E_PARSE", "not valid UTF-8")
    try:
        obj = strict_load(text)
    except CanonicalError as e:
        _fail("E_CANONICAL", str(e)[:80])

    # 2. schema
    if not isinstance(obj, dict):
        _fail("E_SCHEMA", "top-level must be object")
    for f in REQUIRED_FIELDS:
        if f not in obj:
            _fail("E_SCHEMA", f"missing {f}")
    if obj.get("dcp_version") != "2.0":
        _fail("E_VERSION", f"dcp_version must be 2.0, got {obj.get('dcp_version')!r}")

    # 3. claim root (must equal what's declared)
    fields = {k: obj.get(k) for k in FIELD_NAMES}
    recomputed_root = "sha256:" + compute_claim_root(fields).hex()
    declared_root = obj.get("claim_root")
    if recomputed_root != declared_root:
        _fail("E_CLAIM_ROOT_MISMATCH",
              f"declared {str(declared_root)[:24]}, recomputed {recomputed_root[:24]}")

    # 4. binding
    try:
        verify_binding(obj["binding"], obj["request"], expectation)
    except BindingError as e:
        _fail(e.code, str(e)[:80])

    # 5. signature (RS256, over canonical_bytes(signed_payload))
    signed_payload = {k: obj[k] for k in obj if k != "signature"}
    canonical = canonical_bytes(signed_payload)
    sig_obj = obj["signature"]
    if not isinstance(sig_obj, dict):
        _fail("E_SIGNATURE", "signature must be object")
    if sig_obj.get("alg") != "RS256":
        _fail("E_SIGNATURE", f"unsupported alg {sig_obj.get('alg')!r}")
    sig_b64 = sig_obj.get("value", "")
    if not isinstance(sig_b64, str) or not sig_b64.startswith("base64:"):
        _fail("E_SIGNATURE", "value must be base64:...")
    try:
        sig = base64.b64decode(sig_b64[7:], validate=True)
    except Exception as e:
        _fail("E_SIGNATURE", str(e)[:60])
    try:
        pub = serialization.load_pem_public_key(public_key_pem)
        pub.verify(sig, canonical, padding.PKCS1v15(), hashes.SHA256())
    except Exception as e:
        _fail("E_SIGNATURE", str(e)[:80])

    # 6. assure vector (Phase 1 — minimal)
    return {
        "integrity": "PASS",
        "binding": "PASS",
        "claim_root": "PASS",
        "signature": "PASS",
        "claim_id": obj["claim_id"],
    }


def issue_dcp20(claim_fields: dict, private_key_pem: bytes,
                claim_id: str) -> bytes:
    """Minimal issuer for Phase 1 test vectors."""
    from cryptography.hazmat.primitives import serialization as ser
    key = ser.load_pem_private_key(private_key_pem, password=None)
    obj = {
        "dcp_version": "2.0",
        "claim_id": claim_id,
        "issuer": claim_fields.get("issuer"),
        "subject": claim_fields.get("subject"),
        "binding": claim_fields.get("binding"),
        "request": claim_fields.get("request"),
        "context": claim_fields.get("context"),
        "policy": claim_fields.get("policy"),
        "model": claim_fields.get("model"),
        "data": claim_fields.get("data"),
        "runtime": claim_fields.get("runtime"),
        "output": claim_fields.get("output"),
        "temporal": claim_fields.get("temporal"),
        "evidence": claim_fields.get("evidence"),
        "authoring": claim_fields.get("authoring"),
        "proofs": [],
    }
    # compute claim_root over the 13 named fields
    fields = {k: obj.get(k) for k in FIELD_NAMES}
    obj["claim_root"] = "sha256:" + compute_claim_root(fields).hex()

    # signature
    payload = canonical_bytes(obj)
    sig = key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    obj["signature"] = {
        "alg": "RS256",
        "value": "base64:" + base64.b64encode(sig).decode(),
    }
    return json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
