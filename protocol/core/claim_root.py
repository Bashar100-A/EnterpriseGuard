"""ADIE vΩ — ClaimRoot Merkle construction (Phase 1, normative)."""
from .domain_hash import (H_A, FIELD_REGISTRY, STATUS_ABSENT,
                          STATUS_PRESENT, STATUS_NULL)
from .jcs import canonical_bytes


def _leaf(field_id: int, status: int, canonical: bytes) -> bytes:
    import struct
    body = (struct.pack(">H", field_id)
            + bytes([status])
            + struct.pack(">I", len(canonical))
            + canonical)
    return H_A("leaf", body)


def _padding_leaf() -> bytes:
    return H_A("padding", b"")


def _parent(l: bytes, r: bytes) -> bytes:
    return H_A("node", l + r)


def compute_claim_root(fields: dict) -> bytes:
    """fields: {name: value} where value may be absent, None, or dict/list/etc.

    Returns 32-byte digest.
    """
    leaves = []
    for fid, name in FIELD_REGISTRY:
        if name not in fields:
            leaves.append(_leaf(fid, STATUS_ABSENT, b""))
            continue
        v = fields[name]
        if v is None:
            leaves.append(_leaf(fid, STATUS_NULL, b""))
            continue
        try:
            cb = canonical_bytes(v)
        except Exception as e:
            raise ValueError(f"cannot canonicalize field {name}: {e}")
        leaves.append(_leaf(fid, STATUS_PRESENT, cb))

    # pad to next power of 2
    n = 1
    while n < len(leaves):
        n *= 2
    pad = _padding_leaf()
    while len(leaves) < n:
        leaves.append(pad)

    # Merkle reduce
    level = leaves
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            nxt.append(_parent(level[i], level[i + 1]))
        level = nxt
    return level[0]


def claim_root_hex(fields: dict) -> str:
    return "sha256:" + compute_claim_root(fields).hex()
