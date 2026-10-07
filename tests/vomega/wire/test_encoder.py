#!/usr/bin/env python3
"""ADIE encoder — Python conformance tests."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.wire.encoder import encode
from protocol.wire.value import (
    UInt, Int, Bytes, Text, Array, Map, Bool, Null,
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


def enc(v):
    return encode(v)


def main():
    print("=" * 72)
    print("ADIE encoder — Python conformance")
    print("=" * 72)

    # ── Primitives ──
    check("T01 null", enc(Null()) == b"\xf6")
    check("T02 true", enc(Bool(True)) == b"\xf5")
    check("T03 false", enc(Bool(False)) == b"\xf4")

    # ── UInt boundaries ──
    check("T04 uint 0", enc(UInt(0)) == b"\x00")
    check("T05 uint 1", enc(UInt(1)) == b"\x01")
    check("T06 uint 23", enc(UInt(23)) == b"\x17")
    check("T07 uint 24 (u8 form)", enc(UInt(24)) == b"\x18\x18")
    check("T08 uint 255", enc(UInt(255)) == b"\x18\xff")
    check("T09 uint 256 (u16 form)", enc(UInt(256)) == b"\x19\x01\x00")
    check("T10 uint 65535", enc(UInt(65535)) == b"\x19\xff\xff")
    check("T11 uint 65536 (u32 form)", enc(UInt(65536)) == b"\x1a\x00\x01\x00\x00")
    check("T12 uint u32::MAX", enc(UInt(0xFFFFFFFF)) == b"\x1a\xff\xff\xff\xff")
    check("T13 uint u64::MAX",
          enc(UInt(0xFFFFFFFFFFFFFFFF)) == b"\x1b\xff\xff\xff\xff\xff\xff\xff\xff")

    # ── Int ──
    check("T14 int -1", enc(Int(-1)) == b"\x20")
    check("T15 int -24", enc(Int(-24)) == b"\x37")
    check("T16 int -25 (u8 form)", enc(Int(-25)) == b"\x38\x18")

    # ── Text ──
    check("T17 empty text", enc(Text("")) == b"\x60")
    check("T18 text 'hi'", enc(Text("hi")) == b"\x62\x68\x69")
    check("T19 text 'é'", enc(Text("é")) == b"\x62\xc3\xa9")

    # ── Bytes ──
    check("T20 empty bytes", enc(Bytes(b"")) == b"\x40")
    check("T21 bytes 010203", enc(Bytes(b"\x01\x02\x03")) == b"\x43\x01\x02\x03")

    # ── Array ──
    check("T22 empty array", enc(Array(())) == b"\x80")
    check("T23 array 3 items",
          enc(Array((Bool(True), Bool(False), Null()))) == b"\x83\xf5\xf4\xf6")

    # ── Map ──
    check("T24 empty map", enc(Map(())) == b"\xa0")
    check("T25 single-entry map",
          enc(Map(((1, Bool(True)),))) == b"\xa1\x01\xf5")

    # ── Determinism ──
    v = Map((
        (1, Text("one")),
        (2, Array((UInt(10), UInt(20)))),
        (256, Bytes(b"\xde\xad")),
    ))
    check("T26 repeated encode byte-identical", enc(v) == enc(v))

    # ── RFC 8949 integer boundaries (empirical, per §7) ──
    check("T27 canonical int boundary 24",
          enc(Map(((24, Null()),))) == b"\xa1\x18\x18\xf6")
    check("T28 canonical int boundary 256",
          enc(Map(((256, Null()),))) == b"\xa1\x19\x01\x00\xf6")
    check("T29 canonical int boundary 65536",
          enc(Map(((65536, Null()),))) == b"\xa1\x1a\x00\x01\x00\x00\xf6")

    # ── Map key ordering: cbor2 canonical=True must sort ──
    unsorted = Map(((2, Text("b")), (1, Text("a"))))
    expect_sorted = b"\xa2\x01\x61\x61\x02\x61\x62"
    check("T30 encoder sorts map keys (canonical=True)",
          enc(unsorted) == expect_sorted)

    # ── Map key ordering across boundaries ──
    # Construct map in reverse bytewise order, verify encoder reorders.
    boundary_map = Map((
        (256, Text("c")),
        (24, Text("a")),
        (255, Text("b")),
    ))
    encoded = enc(boundary_map)
    # Expected: a2 + 24 + 1-byte "a" + 255 + 1-byte "b" + 256 + "c"
    # 24 encodes as 18 18; 255 as 18 ff; 256 as 19 01 00
    expected_order = (
        b"\xa3"
        b"\x18\x18" + b"\x61\x61"  # key 24, "a"
        + b"\x18\xff" + b"\x61\x62"  # key 255, "b"
        + b"\x19\x01\x00" + b"\x61\x63"  # key 256, "c"
    )
    check("T31 encoder boundary key order",
          encoded == expected_order,
          f"got {encoded.hex()}, expected {expected_order.hex()}")

    # ── Nested ──
    check("T32 nested {1:[true,null]}",
          enc(Map(((1, Array((Bool(True), Null()))),))) == b"\xa1\x01\x82\xf5\xf6")

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
