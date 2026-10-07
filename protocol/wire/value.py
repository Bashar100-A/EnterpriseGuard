"""ADIE value model (Phase 3, Gate 1, 3A.3).

Mirror of rust/adie-primitives/src/cbor/value.rs.

Profile types only — not a CBOR type system.
Map keys: unsigned integers, shortest-form, RFC 8949 bytewise order.

Commander order (§6): duplicate keys are REJECTED, never deduplicated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from protocol.wire.error import DuplicateKey


# ─────────────────────────────────────────────────────────────
# AdieValue: closed profile type set
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class UInt:
    value: int

    def __post_init__(self):
        if not (0 <= self.value <= 0xFFFFFFFF_FFFFFFFF):
            raise ValueError(f"UInt out of range: {self.value}")


@dataclass(frozen=True)
class Int:
    value: int

    def __post_init__(self):
        # Signed 64-bit range.
        if not (-0x8000_0000_0000_0000 <= self.value <= 0x7FFF_FFFF_FFFF_FFFF):
            raise ValueError(f"Int out of range: {self.value}")


@dataclass(frozen=True)
class Bytes:
    value: bytes


@dataclass(frozen=True)
class Text:
    value: str


@dataclass(frozen=True)
class Array:
    value: tuple  # tuple of AdieValue


@dataclass(frozen=True)
class Map:
    # tuple of (u64 key, AdieValue), in RFC 8949 canonical order
    value: tuple


@dataclass(frozen=True)
class Bool:
    value: bool


@dataclass(frozen=True)
class Null:
    pass


AdieValue = Union[UInt, Int, Bytes, Text, Array, Map, Bool, Null]


# ─────────────────────────────────────────────────────────────
# Minimal CBOR integer encoding (mirror of encode_uint_shortest)
# ─────────────────────────────────────────────────────────────

def encode_uint_shortest(n: int) -> bytes:
    """Shortest-form CBOR encoding of an unsigned integer.

    RFC 8949 §3.4.3 preferred serialization.
    """
    if n < 24:
        return bytes([n])
    if n <= 0xFF:
        return bytes([0x18, n])
    if n <= 0xFFFF:
        return bytes([0x19]) + n.to_bytes(2, "big")
    if n <= 0xFFFF_FFFF:
        return bytes([0x1A]) + n.to_bytes(4, "big")
    if n <= 0xFFFF_FFFF_FFFF_FFFF:
        return bytes([0x1B]) + n.to_bytes(8, "big")
    raise ValueError(f"uint64 overflow: {n}")


# ─────────────────────────────────────────────────────────────
# RFC 8949 bytewise-lexicographic ordering for u64 map keys
# ─────────────────────────────────────────────────────────────

def cmp_uint_rfc8949(a: int, b: int) -> int:
    """Compare two u64 by RFC 8949 bytewise order of their
    deterministic (shortest-form) CBOR encodings.

    Returns negative, zero, or positive.
    """
    ea = encode_uint_shortest(a)
    eb = encode_uint_shortest(b)
    if ea < eb:
        return -1
    if ea > eb:
        return 1
    return 0


# ─────────────────────────────────────────────────────────────
# Map canonicalization: sort + reject duplicates (NO dedup)
# ─────────────────────────────────────────────────────────────

def canonicalize_map(entries):
    """Sort a map's entries by RFC 8949 order and reject duplicate keys.

    Input: iterable of (u64, AdieValue).
    Output: tuple of (u64, AdieValue), sorted, duplicate-free.

    Duplicate keys raise DuplicateKey — the input is not modified,
    not deduplicated. WIRE-FORMAT-0.2 §3.
    """
    from functools import cmp_to_key

    sorted_entries = sorted(entries, key=cmp_to_key(
        lambda a, b: cmp_uint_rfc8949(a[0], b[0])))

    for i in range(1, len(sorted_entries)):
        if sorted_entries[i - 1][0] == sorted_entries[i][0]:
            raise DuplicateKey()

    return tuple(sorted_entries)


__all__ = [
    "UInt", "Int", "Bytes", "Text", "Array", "Map", "Bool", "Null",
    "AdieValue",
    "encode_uint_shortest",
    "cmp_uint_rfc8949",
    "canonicalize_map",
]
