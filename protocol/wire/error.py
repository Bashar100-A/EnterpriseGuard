"""ADIE wire error codes (Phase 3, Gate 1, 3A.3).

Mirror of rust/adie-primitives/src/cbor/error.rs.
14 codes, matching WIRE-FORMAT-0.2 §9 exactly.
"""
from __future__ import annotations


class CborError(Exception):
    """Base class for all ADIE wire rejections."""
    code: str = "E_WIRE_UNKNOWN"

    def __str__(self) -> str:
        return self.code


# ─────────────────────────────────────────────────────────────
# 14 concrete errors, one per WIRE-FORMAT-0.2 §9 code.
# ─────────────────────────────────────────────────────────────

class Malformed(CborError):
    code = "E_WIRE_MALFORMED"

    def __init__(self, detail: str = "") -> None:
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}" if self.detail else self.code


class Trailing(CborError):
    code = "E_WIRE_TRAILING"

    def __init__(self, extra: int) -> None:
        self.extra = extra

    def __str__(self) -> str:
        return f"{self.code}: {self.extra} byte(s) after top-level item"


class Indefinite(CborError):
    code = "E_WIRE_INDEFINITE"


class Float(CborError):
    code = "E_WIRE_FLOAT"


class Tag(CborError):
    code = "E_WIRE_TAG"

    def __init__(self, tag: int) -> None:
        self.tag = tag

    def __str__(self) -> str:
        return f"{self.code}: tag {self.tag}"


class DuplicateKey(CborError):
    code = "E_WIRE_DUP_KEY"


class NonCanonicalInt(CborError):
    code = "E_WIRE_NONCANONICAL_INT"


class NonCanonicalMap(CborError):
    code = "E_WIRE_NONCANONICAL_MAP"


class InvalidUtf8(CborError):
    code = "E_WIRE_INVALID_UTF8"


class TypeMismatch(CborError):
    code = "E_WIRE_TYPE_MISMATCH"

    def __init__(self, field: str, expected: str) -> None:
        self.field = field
        self.expected = expected

    def __str__(self) -> str:
        return f"{self.code}: field {self.field!r} must be {self.expected}"


class MissingField(CborError):
    code = "E_WIRE_MISSING_FIELD"

    def __init__(self, field: str) -> None:
        self.field = field

    def __str__(self) -> str:
        return f"{self.code}: missing field {self.field!r}"


class UnknownCritical(CborError):
    code = "E_WIRE_UNKNOWN_CRITICAL"

    def __init__(self, label: int) -> None:
        self.label = label

    def __str__(self) -> str:
        return f"{self.code}: unknown critical label {self.label}"


class Version(CborError):
    code = "E_WIRE_VERSION"

    def __init__(self, got: str) -> None:
        self.got = got

    def __str__(self) -> str:
        return f'{self.code}: dcp_version must be "2.1", got {self.got!r}'


class Ambiguous(CborError):
    code = "E_WIRE_AMBIGUOUS"

    def __init__(self, field: str) -> None:
        self.field = field

    def __str__(self) -> str:
        return f"{self.code}: field {self.field!r} requires external state"
