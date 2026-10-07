"""ADIE raw-byte structural pre-check (Phase 3, Gate 1, 3A.3).

Mirror of rust/adie-primitives/src/cbor/rawcheck.rs.

Runs BEFORE cbor2. cbor2 collapses indefinite-length items and
interprets known semantic tags; this module rejects them on raw
bytes. It also detects trailing bytes after the top-level item.

Normative source: WIRE-FORMAT-0.2 §7 (forbidden types), §8 (rule 3,
rule 8), §9 (codes).

AUTHORITATIVE for tag rejection (Commander order §1):
any CBOR major type 6 is refused here, before cbor2 sees the bytes.
cbor2's tag_hook does not intercept built-in semantic tags; the
scanner does.
"""
from __future__ import annotations

from protocol.wire.error import (
    CborError, DuplicateKey, Float, Indefinite, InvalidUtf8, Malformed,
    NonCanonicalInt, Tag, Trailing,
)

MAX_DEPTH = 32


def scan_top_level(data: bytes) -> int:
    """Scan a single top-level CBOR item at offset 0 of `data`.

    Returns the number of bytes consumed.
    Raises a CborError subclass on any raw-byte violation.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise Malformed("input must be bytes")
    consumed, _ = _scan_item(bytes(data), 0, 0)
    if consumed != len(data):
        raise Trailing(len(data) - consumed)
    return consumed


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _read_u8(data: bytes, offset: int) -> int:
    if offset >= len(data):
        raise Malformed(f"unexpected end of input at offset {offset}")
    return data[offset]


def _read_bytes(data: bytes, offset: int, n: int) -> bytes:
    end = offset + n
    if end > len(data) or end < offset:
        raise Malformed(
            f"unexpected end of input: need {n} bytes at offset {offset}"
        )
    return data[offset:end]


def _read_length(data: bytes, offset: int, additional: int):
    """Read a CBOR length. Enforces shortest form; rejects indefinite.

    Returns (length: int, new_offset: int).
    """
    if additional <= 23:
        return additional, offset + 1
    if additional == 24:
        b = _read_u8(data, offset + 1)
        if b < 24:
            raise NonCanonicalInt()
        return b, offset + 2
    if additional == 25:
        raw = _read_bytes(data, offset + 1, 2)
        n = int.from_bytes(raw, "big")
        if n < 256:
            raise NonCanonicalInt()
        return n, offset + 3
    if additional == 26:
        raw = _read_bytes(data, offset + 1, 4)
        n = int.from_bytes(raw, "big")
        if n < 65536:
            raise NonCanonicalInt()
        return n, offset + 5
    if additional == 27:
        raw = _read_bytes(data, offset + 1, 8)
        n = int.from_bytes(raw, "big")
        if n < 0x1_0000_0000:
            raise NonCanonicalInt()
        return n, offset + 9
    if additional in (28, 29, 30):
        raise Malformed(f"reserved additional info {additional}")
    if additional == 31:
        raise Indefinite()
    raise Malformed(f"invalid additional info {additional}")


def _scan_item(data: bytes, offset: int, depth: int):
    """Scan one CBOR item. Returns (new_offset, depth)."""
    if depth > MAX_DEPTH:
        raise Malformed(f"max nesting depth {MAX_DEPTH} exceeded")

    head = _read_u8(data, offset)
    major = head >> 5
    additional = head & 0x1F

    # Major type 0: unsigned integer
    if major == 0:
        _, nxt = _read_length(data, offset, additional)
        return nxt, depth

    # Major type 1: negative integer
    if major == 1:
        _, nxt = _read_length(data, offset, additional)
        return nxt, depth

    # Major type 2: byte string
    if major == 2:
        length, nxt = _read_length(data, offset, additional)
        _read_bytes(data, nxt, length)  # verify presence
        return nxt + length, depth

    # Major type 3: text string
    if major == 3:
        length, nxt = _read_length(data, offset, additional)
        payload = _read_bytes(data, nxt, length)
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidUtf8()
        return nxt + length, depth

    # Major type 4: array
    if major == 4:
        count, cursor = _read_length(data, offset, additional)
        for _ in range(count):
            cursor, _ = _scan_item(data, cursor, depth + 1)
        return cursor, depth

    # Major type 5: map. Duplicate keys (byte-identical encoded keys)
    # are rejected here at the wire level, per DEFECT-027/038. This
    # must happen before cbor2, because cbor2 collapses duplicate keys
    # into a single entry (last wins), losing the wire-level fact.
    if major == 5:
        count, cursor = _read_length(data, offset, additional)
        key_ranges: list[bytes] = []
        for _ in range(count):
            k_start = cursor
            cursor, _ = _scan_item(data, cursor, depth + 1)
            k_end = cursor
            kb = data[k_start:k_end]
            for prev in key_ranges:
                if len(prev) == len(kb) and prev == kb:
                    raise DuplicateKey()
            key_ranges.append(kb)
            cursor, _ = _scan_item(data, cursor, depth + 1)
        return cursor, depth

    # Major type 6: tag — FORBIDDEN
    if major == 6:
        tag, _ = _read_length(data, offset, additional)
        raise Tag(tag)

    # Major type 7: simple values, floats
    if major == 7:
        if additional in (20, 21, 22):  # false, true, null
            return offset + 1, depth
        if additional == 23:  # undefined
            raise Malformed("undefined (0xF7) is not permitted")
        if additional == 24:  # simple value with 1-byte argument
            _read_u8(data, offset + 1)
            raise Malformed(
                "simple value with 1-byte argument is not permitted"
            )
        if additional in (25, 26, 27):  # float16/32/64
            raise Float()
        if additional in (28, 29, 30):
            raise Malformed(f"reserved simple-value additional {additional}")
        if additional == 31:  # break
            raise Malformed("stray break (0xFF) outside indefinite container")
        # 0..=19: unassigned simple values
        raise Malformed(f"simple value {additional} is not permitted")

    raise Malformed(f"invalid major type {major}")


__all__ = ["scan_top_level", "MAX_DEPTH"]
