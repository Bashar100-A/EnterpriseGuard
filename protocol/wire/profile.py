"""ADIE CBOR profile validation (Phase 3, Gate 1, 3A.3).

Mirror of rust/adie-primitives/src/cbor/profile.rs.

Normative source: spec/WIRE-FORMAT-0.2.md §5, §7, §8, §9.

Authority for what CBOR-derived Python object is admissible as
DCP 2.1 payload. Both encoder and decoder route through validate().

This module operates on Python objects produced by cbor2.loads().
In the decoder pipeline, rawcheck has already rejected raw-byte
violations (tags, indefinite lengths, trailing bytes, non-shortest
integer encodings). profile.py is defense-in-depth for structure
and a positive authority for type/label validation.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from protocol.wire.error import (
    Float, Malformed, NonCanonicalInt, Tag, TypeMismatch,
)
from protocol.wire.value import (
    AdieValue, Array, Bool, Bytes, Int, Map, Null, Text, UInt,
    canonicalize_map,
)

MAX_DEPTH = 32

U64_MAX = 0xFFFFFFFF_FFFFFFFF
I64_MIN = -0x8000_0000_0000_0000
I64_MAX = 0x7FFF_FFFF_FFFF_FFFF


def validate(obj: Any) -> AdieValue:
    """Validate a cbor2-decoded Python object against the ADIE profile.

    Returns an AdieValue with maps canonicalized (sorted, dup-free).
    Raises a CborError subclass on violation.
    """
    return _validate_depth(obj, 0)


def _validate_depth(obj: Any, depth: int) -> AdieValue:
    if depth > MAX_DEPTH:
        raise Malformed(f"max nesting depth {MAX_DEPTH} exceeded")

    # None -> Null (must be checked before anything else)
    if obj is None:
        return Null()

    # Bool must be checked before int (bool is a subclass of int in Python)
    if isinstance(obj, bool):
        return Bool(obj)

    # Integer (may be UInt or Int depending on sign and range)
    if isinstance(obj, int):
        return _int_to_adie(obj)

    # Float -> rejected
    if isinstance(obj, float):
        raise Float()

    # Bytes
    if isinstance(obj, (bytes, bytearray)):
        return Bytes(bytes(obj))

    # Text
    if isinstance(obj, str):
        return Text(obj)

    # Array
    if isinstance(obj, list):
        return Array(tuple(_validate_depth(item, depth + 1) for item in obj))

    # Map (dict)
    if isinstance(obj, dict):
        entries: list[tuple[int, AdieValue]] = []
        for k, v in obj.items():
            # bool is a subclass of int in Python; reject it as key
            if isinstance(k, bool) or not isinstance(k, int):
                raise TypeMismatch("map key", "unsigned integer")
            if k < 0:
                raise TypeMismatch("map key", "unsigned integer")
            if k > U64_MAX:
                raise TypeMismatch("map key", "unsigned integer in u64 range")
            entries.append((k, _validate_depth(v, depth + 1)))
        # canonicalize_map rejects duplicates and sorts by RFC 8949 order.
        # Duplicate detection here is defense-in-depth: with
        # allow_duplicate_keys=False, cbor2 would have already raised.
        return Map(canonicalize_map(entries))

    # Known tag-result types (defense-in-depth). rawcheck is authoritative
    # for tag prohibition; this is a belt-and-braces check in case a
    # semantic tag slipped through the codec.
    if isinstance(obj, (datetime, date)):
        # We cannot recover the original tag number at this point.
        raise Tag(0)

    # Any other type is rejected (unrecognised profile value).
    raise Malformed(
        f"unrecognised Python type {type(obj).__name__!r} "
        f"(possibly a tag result or unknown value)"
    )


def _int_to_adie(n: int) -> AdieValue:
    """Map a Python int to UInt or Int, or reject if out of range.

    Python ints are arbitrary precision. cbor2 may produce ints outside
    u64/i64 range when a bignum tag (2/3) or a built-in semantic tag
    is decoded. rawcheck should reject such tags, but this is
    defense-in-depth.
    """
    if 0 <= n <= U64_MAX:
        return UInt(n)
    if I64_MIN <= n < 0:
        return Int(n)
    raise NonCanonicalInt()


__all__ = ["validate", "MAX_DEPTH"]
