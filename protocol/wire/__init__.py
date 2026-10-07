"""ADIE wire format adapter (Phase 3, Gate 1, 3A.3).

Public API:
    encode(value: AdieValue) -> bytes
    decode(data: bytes) -> AdieValue

Normative source: spec/WIRE-FORMAT-0.2.md.
Reference behavior: rust/adie-primitives/src/cbor/.
The Python layer conforms; it does not redefine semantics.
"""
from protocol.wire.decoder import decode
from protocol.wire.encoder import encode
from protocol.wire.error import (
    Ambiguous, CborError, DuplicateKey, Float, Indefinite, InvalidUtf8,
    Malformed, MissingField, NonCanonicalInt, NonCanonicalMap, Tag,
    Trailing, TypeMismatch, UnknownCritical, Version,
)
from protocol.wire.value import (
    AdieValue, Array, Bool, Bytes, Int, Map, Null, Text, UInt,
)

__all__ = [
    "decode", "encode",
    "CborError",
    "Malformed", "Trailing", "Indefinite", "Float", "Tag",
    "DuplicateKey", "NonCanonicalInt", "NonCanonicalMap", "InvalidUtf8",
    "TypeMismatch", "MissingField", "UnknownCritical", "Version",
    "Ambiguous",
    "AdieValue", "Array", "Bool", "Bytes", "Int", "Map", "Null",
    "Text", "UInt",
]
