#!/usr/bin/env python3
"""ADIE decoder — Python conformance tests."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.wire import decode, encode
from protocol.wire.value import (
    UInt, Int, Bytes, Text, Array, Map, Bool, Null,
)
from protocol.wire.error import (
    Malformed, Trailing, Indefinite, Float, Tag,
    DuplicateKey, NonCanonicalInt, NonCanonicalMap, InvalidUtf8,
    TypeMismatch,
)


PASS_N = FAIL_N = 0


def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"[PASS] {name}")
    else:
        FAIL_N += 1
        print(f"[FAIL] {name}: {detail}")


def ok(data):
    return decode(data)


def expect_err(data, err_type):
    try:
        decode(data)
        return False
    except err_type:
        return True
    except Exception as e:
        print(f"    (wrong exception: {type(e).__name__}: {e})")
        return False


def main():
    print("=" * 72)
    print("ADIE decoder — Python conformance")
    print("=" * 72)

    # ── Valid primitives ──
    check("T01 null", ok(b"\xf6") == Null())
    check("T02 true", ok(b"\xf5") == Bool(True))
    check("T03 false", ok(b"\xf4") == Bool(False))
    check("T04 uint 0", ok(b"\x00") == UInt(0))
    check("T05 uint 23", ok(b"\x17") == UInt(23))
    check("T06 uint 24", ok(b"\x18\x18") == UInt(24))
    check("T07 uint 256", ok(b"\x19\x01\x00") == UInt(256))
    check("T08 uint 65536", ok(b"\x1a\x00\x01\x00\x00") == UInt(65536))
    check("T09 neg int -1", ok(b"\x20") == Int(-1))
    check("T10 text 'hi'", ok(b"\x62\x68\x69") == Text("hi"))
    check("T11 bytes 010203", ok(b"\x43\x01\x02\x03") == Bytes(b"\x01\x02\x03"))
    check("T12 empty array", ok(b"\x80") == Array(()))
    check("T13 empty map", ok(b"\xa0") == Map(()))
    check("T14 single map", ok(b"\xa1\x01\xf5") == Map(((1, Bool(True)),)))
    check("T15 nested",
          ok(b"\xa1\x01\x82\xf5\xf6") == Map(((1, Array((Bool(True), Null()))),)))

    # ── Trailing ──
    check("T16 trailing after null", expect_err(b"\xf6\x00", Trailing))
    check("T17 trailing after empty map", expect_err(b"\xa0\xff", Trailing))

    # ── Indefinite ──
    check("T18 indefinite map", expect_err(b"\xbf\x01\x61\x78\xff", Indefinite))
    check("T19 indefinite array", expect_err(b"\x9f\x01\xff", Indefinite))

    # ── Floats ──
    check("T20 float16", expect_err(b"\xf9\x3c\x00", Float))
    check("T21 float64", expect_err(b"\xfb\x3f\xf0\x00\x00\x00\x00\x00\x00", Float))

    # ── Tags (rawcheck authoritative — DEFECT-021 coverage) ──
    check("T22 tag 1 (epoch) rejected before cbor2",
          expect_err(b"\xc1\x01", Tag))
    check("T23 tag 0 (date string) rejected",
          expect_err(b"\xc0\x6a" + b"2026-10-07", Tag))
    check("T24 tag 2 (bignum) rejected",
          expect_err(b"\xc2\x41\x01", Tag))

    # ── Duplicate keys ──
    check("T25 duplicate keys rejected",
          expect_err(b"\xa2\x01\x61\x61\x01\x61\x62", DuplicateKey))

    # ── Non-canonical integers ──
    check("T26 noncanonical uint8 for 1",
          expect_err(b"\x18\x01", NonCanonicalInt))
    check("T27 noncanonical uint16 for 1",
          expect_err(b"\x19\x00\x01", NonCanonicalInt))

    # ── Non-canonical map (unsorted keys) ──
    check("T28 unsorted map rejected",
          expect_err(b"\xa2\x02\x61\x62\x01\x61\x61", NonCanonicalMap))

    # ── Wrong key types ──
    check("T29 text map key rejected",
          expect_err(b"\xa1\x61\x61\x01", TypeMismatch))
    check("T30 bytes map key rejected",
          expect_err(b"\xa1\x41\x61\x01", TypeMismatch))

    # ── Invalid UTF-8 ──
    check("T31 invalid utf-8 rejected",
          expect_err(b"\x62\xff\xfe", InvalidUtf8))

    # ── Undefined ──
    check("T32 undefined 0xf7 rejected",
          expect_err(b"\xf7", Malformed))

    # ── Truncated ──
    check("T33 truncated bytes rejected",
          expect_err(b"\x43\x01\x02", Malformed))
    check("T34 empty input rejected",
          expect_err(b"", Malformed))

    # ── Round-trip ──
    v = Map((
        (1, Text("a")),
        (2, Array((UInt(10), UInt(20)))),
        (256, Bytes(b"\xde\xad")),
    ))
    bytes_ = encode(v)
    check("T35 encode then decode value-stable", decode(bytes_) == v)
    check("T36 decode then re-encode byte-stable", encode(decode(bytes_)) == bytes_)

    # ── Canonical bytes round-trip with mixed types ──
    canonical = (
        b"\xa3"
        b"\x01\x82\xf5\xf6"        # key 1: [true, null]
        b"\x02\x62\x68\x69"        # key 2: "hi"
        b"\x19\x01\x00\x43\x01\x02\x03"  # key 256: h'010203'
    )
    check("T37 canonical bytes decode", decode(canonical) is not None)
    check("T38 canonical bytes re-encode stable",
          encode(decode(canonical)) == canonical)

    # ── Determinism ──
    b1 = encode(v)
    b2 = encode(decode(b1))
    check("T39 determinism after round-trip", b1 == b2)

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
