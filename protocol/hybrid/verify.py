"""ADIE hybrid verification — RS256 + ML-DSA-65.

Per spec/HYBRID-CRYPTO-0.1.md §7–§8:
- Hybrid policy: AND (default) — every required alg must verify.
- Downgrade: if any required alg is missing → E_SIGNATURE_DOWNGRADE.
- Unknown alg → E_SIGNATURE_UNKNOWN_ALG.
- Duplicate alg → E_SIGNATURE_DUPLICATE_ALG.
- No silent fallback: if ML-DSA-65 is required and only RS256 present → reject.
- No silent upgrade: unknown alg → reject.
"""
import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from dilithium_py.ml_dsa import ML_DSA_65 as _DLP_MLDSA65

from protocol.hybrid.tbs import build_tbs
from protocol.hybrid.sign import (
    rs256_key_id_from_public_pem,
    mldsa65_key_id_from_public_bytes,
)


ALLOWED_ALGS = frozenset({"RS256", "ML-DSA-65"})


class HybridVerifyError(Exception):
    def __init__(self, code, msg=""):
        self.code = code
        super().__init__(f"{code}: {msg}")


# ─── individual verifiers ──────────────────────────────────────

def _rs256_verify(pub_pem: bytes, tbs: bytes, sig_bytes: bytes) -> bool:
    try:
        pub = serialization.load_pem_public_key(pub_pem)
        pub.verify(sig_bytes, tbs, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


def _mldsa65_verify(pub_raw: bytes, tbs: bytes, sig_bytes: bytes) -> bool:
    try:
        return _DLP_MLDSA65.verify(pub_raw, tbs, sig_bytes, ctx=b"")
    except Exception:
        return False


# ─── main verifier ─────────────────────────────────────────────

def verify_hybrid(
    cert_without_signatures: dict,
    signatures: list[dict],
    required_algs: list[str],
    rs256_pub_pem: bytes = None,
    mldsa65_pub_raw: bytes = None,
) -> dict:
    """Verify hybrid signatures on a DCP 2.1 certificate.

    Args:
        cert_without_signatures: cert dict with signatures/signature removed.
        signatures: list of {"alg", "key_id", "value"}.
        required_algs: algorithms that MUST appear (spec §7).
        rs256_pub_pem: PEM public key if RS256 is required.
        mldsa65_pub_raw: raw 1952B pk if ML-DSA-65 is required.

    Returns:
        {"status": "VALID" | "INVALID", "checks": {...}, "code": ...}

    Raises:
        HybridVerifyError on structural issues (unknown alg, duplicate, downgrade).
    """
    if not isinstance(signatures, list) or not signatures:
        raise HybridVerifyError("E_SIGNATURE_HYBRID_MISSING",
                                "signatures array is empty")

    # duplicate alg check
    algs_seen = [s.get("alg") for s in signatures]
    if len(algs_seen) != len(set(algs_seen)):
        raise HybridVerifyError("E_SIGNATURE_DUPLICATE_ALG",
                                f"algs: {algs_seen}")

    # unknown alg check
    for alg in algs_seen:
        if alg not in ALLOWED_ALGS:
            raise HybridVerifyError("E_SIGNATURE_UNKNOWN_ALG", f"alg: {alg!r}")

    # downgrade check
    for req in required_algs:
        if req not in algs_seen:
            raise HybridVerifyError(
                "E_SIGNATURE_DOWNGRADE",
                f"required {req!r} absent; present: {algs_seen}")

    # build lookup
    sig_by_alg = {s["alg"]: s for s in signatures}

    # TBS
    tbs = build_tbs(cert_without_signatures)

    checks = {}
    all_valid = True

    for alg in required_algs:
        s = sig_by_alg[alg]
        value = s.get("value", "")
        if not isinstance(value, str) or not value.startswith("base64:"):
            checks[alg] = "FAIL (bad base64 prefix)"
            all_valid = False
            continue
        try:
            sig_bytes = base64.b64decode(value[7:], validate=True)
        except Exception as e:
            checks[alg] = f"FAIL (bad base64: {str(e)[:40]})"
            all_valid = False
            continue

        if alg == "RS256":
            if rs256_pub_pem is None:
                raise HybridVerifyError("E_SIGNATURE_HYBRID_MISSING",
                                        "RS256 required but pub key not provided")
            expected_key_id = rs256_key_id_from_public_pem(rs256_pub_pem)
            if s.get("key_id") != expected_key_id:
                raise HybridVerifyError(
                    "E_SIGNATURE_KEY_MISMATCH",
                    f"RS256 key_id mismatch: cert={s.get('key_id')!r} vs key={expected_key_id!r}")
            ok = _rs256_verify(rs256_pub_pem, tbs, sig_bytes)
            checks[alg] = "PASS" if ok else "FAIL"
            all_valid = all_valid and ok

        elif alg == "ML-DSA-65":
            if mldsa65_pub_raw is None:
                raise HybridVerifyError("E_SIGNATURE_HYBRID_MISSING",
                                        "ML-DSA-65 required but pub key not provided")
            expected_key_id = mldsa65_key_id_from_public_bytes(mldsa65_pub_raw)
            if s.get("key_id") != expected_key_id:
                raise HybridVerifyError(
                    "E_SIGNATURE_KEY_MISMATCH",
                    f"ML-DSA-65 key_id mismatch: cert={s.get('key_id')!r} vs key={expected_key_id!r}")
            ok = _mldsa65_verify(mldsa65_pub_raw, tbs, sig_bytes)
            checks[alg] = "PASS" if ok else "FAIL"
            all_valid = all_valid and ok

    if not all_valid:
        raise HybridVerifyError("E_SIGNATURE_HYBRID_INVALID",
                                f"checks: {checks}")

    return {"status": "VALID", "checks": checks}


__all__ = ["verify_hybrid", "HybridVerifyError"]
