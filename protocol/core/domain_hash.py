"""ADIE vΩ — domain-separated hashing (Phase 1, normative)."""
import hashlib
import struct

DOMAIN_PREFIX = b"ADIE/vOmega/2/"


def H_A(t: str, x: bytes) -> bytes:
    """H_A(t,x) = SHA256("ADIE/vOmega/2/" || u16(|t|) || t || x)

    Normative: never reuse a digest across domains even if bytes match.
    """
    if not isinstance(t, str):
        raise TypeError("t must be str")
    if not isinstance(x, (bytes, bytearray)):
        raise TypeError("x must be bytes")
    tb = t.encode("utf-8")
    if len(tb) > 0xFFFF:
        raise ValueError("domain tag too long")
    return hashlib.sha256(
        DOMAIN_PREFIX + struct.pack(">H", len(tb)) + tb + bytes(x)
    ).digest()


# Fixed field registry (1.5 in blueprint)
FIELD_REGISTRY = [
    (1,  "issuer"),
    (2,  "subject"),
    (3,  "request"),
    (4,  "context"),
    (5,  "policy"),
    (6,  "model"),
    (7,  "data"),
    (8,  "runtime"),
    (9,  "output"),
    (10, "binding"),
    (11, "temporal"),
    (12, "evidence"),
    (13, "authoring"),
    (14, "proof-set"),
]
FIELD_NAME_TO_ID = {n: i for i, n in FIELD_REGISTRY}

# Status codes for leaf encoding
STATUS_ABSENT  = 0x00
STATUS_PRESENT = 0x01
STATUS_NULL    = 0x02


def field_domain(field_id: int) -> str:
    return f"ADIE/vOmega/2/field/{field_id}"
