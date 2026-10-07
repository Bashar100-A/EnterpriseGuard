"""ADIE canonical CBOR encoder (Phase 3, Gate 1, 3A.3).

Mirror of rust/adie-primitives/src/cbor/encoder.rs.

Normative source: WIRE-FORMAT-0.2 §7, §8.

This is a thin serializer over cbor2. It assumes the input is a
valid AdieValue (produced by profile.validate or by hand):
  - only profile types
  - maps already sorted and duplicate-free
  - keys already u64

cbor2's canonical=True flag produces shortest-form integers and
definite-length items, and orders map keys. The encoder is NOT an
authority — authority lives in profile.py. The encoder simply
emits bytes for already-valid values.
"""
from __future__ import annotations

import cbor2

from protocol.wire.error import CborError, Malformed
from protocol.wire.value import (
    AdieValue, Array, Bool, Bytes, Int, Map, Null, Text, UInt,
)


def encode(value: AdieValue) -> bytes:
    """Encode an AdieValue to canonical CBOR bytes.

    Determinism: calling this twice with the same input yields
    byte-identical output, because:
      - AdieValue::Map carries sorted keys (invariant)
      - cbor2 canonical=True produces shortest-form, definite-length,
        sorted-key output
    """
    obj = _to_python(value)
    try:
        return cbor2.dumps(obj, canonical=True)
    except Exception as e:
        raise Malformed(f"cbor2 encode: {type(e).__name__}: {e}")


def _to_python(v: AdieValue):
    if isinstance(v, UInt):
        return v.value
    if isinstance(v, Int):
        return v.value
    if isinstance(v, Bool):
        # Bool must be checked before int (bool is int subclass)
        return v.value
    if isinstance(v, Bytes):
        return v.value
    if isinstance(v, Text):
        return v.value
    if isinstance(v, Null):
        return None
    if isinstance(v, Array):
        return [_to_python(item) for item in v.value]
    if isinstance(v, Map):
        # AdieValue.Map invariant: sorted, duplicate-free.
        # We preserve that order verbatim.
        return {k: _to_python(val) for k, val in v.value}
    raise Malformed(f"unknown AdieValue type: {type(v).__name__}")


__all__ = ["encode"]
