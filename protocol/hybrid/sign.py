"""ADIE hybrid signing — RS256 + ML-DSA-65.

Per spec/HYBRID-CRYPTO-0.1.md §4–§7:
- Signatures array sorted by alg (canonical emission)
- TBS = DOMAIN_TAG || JCS(cert_without_signatures)
- key_id = sha256:hex(SHA-256(pubkey_encoding))
    RS256:      pubkey_encoding = SPKI DER
    ML-DSA-65:  pubkey_encoding = raw FIPS 204 pk bytes  (GAP-9)
- Signature value: base64:<standard base64 of raw sig bytes>
"""
import base64
import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from dilithium_py.ml_dsa import ML_DSA_65 as _DLP_MLDSA65

from protocol.hybrid.tbs import build_tbs


# ─── key_id computation ────────────────────────────────────────

def rs256_key_id_from_public_pem(pub_pem: bytes) -> str:
    pub = serialization.load_pem_public_key(pub_pem)
    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    return "sha256:" + hashlib.sha256(der).hexdigest()


def mldsa65_key_id_from_public_bytes(pub_raw: bytes) -> str:
    if len(pub_raw) != 1952:
        raise ValueError(f"ML-DSA-65 pubkey must be 1952 bytes, got {len(pub_raw)}")
    return "sha256:" + hashlib.sha256(pub_raw).hexdigest()


# ─── signature object builders ─────────────────────────────────

def _sig_object(alg: str, key_id: str, sig_bytes: bytes) -> dict:
    return {
        "alg": alg,
        "key_id": key_id,
        "value": "base64:" + base64.b64encode(sig_bytes).decode("ascii"),
    }


# ─── signing ───────────────────────────────────────────────────

def sign_rs256(pub_pem: bytes, priv_pem: bytes, tbs: bytes) -> dict:
    priv = serialization.load_pem_private_key(priv_pem, password=None)
    sig = priv.sign(tbs, padding.PKCS1v15(), hashes.SHA256())
    return _sig_object("RS256", rs256_key_id_from_public_pem(pub_pem), sig)


def sign_mldsa65(pub_raw: bytes, sk: bytes, tbs: bytes) -> dict:
    """ML-DSA-65 deterministic signature.
    Note: takes raw sk (4032 bytes), not seed — matches ACVP convention.
    For ADIE protocol, callers may derive (pk, sk) from a seed via key_derive.
    """
    if len(sk) != 4032:
        raise ValueError(f"ML-DSA-65 sk must be 4032 bytes, got {len(sk)}")
    sig = _DLP_MLDSA65.sign(sk, tbs, ctx=b"", deterministic=True)
    return _sig_object("ML-DSA-65", mldsa65_key_id_from_public_bytes(pub_raw), sig)


def sign_hybrid(
    cert_without_signatures: dict,
    rs256_pub_pem: bytes,
    rs256_priv_pem: bytes,
    mldsa65_pub_raw: bytes,
    mldsa65_sk: bytes,
) -> list[dict]:
    """Return the signatures array for a DCP 2.1 certificate.

    Order is sorted by alg for canonical emission (spec §4).
    """
    tbs = build_tbs(cert_without_signatures)
    sigs = [
        sign_mldsa65(mldsa65_pub_raw, mldsa65_sk, tbs),
        sign_rs256(rs256_pub_pem, rs256_priv_pem, tbs),
    ]
    sigs.sort(key=lambda s: s["alg"])
    return sigs


__all__ = [
    "rs256_key_id_from_public_pem",
    "mldsa65_key_id_from_public_bytes",
    "sign_rs256",
    "sign_mldsa65",
    "sign_hybrid",
]
