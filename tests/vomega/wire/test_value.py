#!/usr/bin/env python3
"""ADIE wire value — Python conformance tests."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.wire.value import (
    UInt, Int, Bytes, Text, Array, Map, Bool, Null,
    encode_uint_shortest, cmp_uint_rfc8949, canonicalize_map,
)
from protocol.wire.error import DuplicateKey


PASS_N = FAIL_N = 0


def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"[PASS] {name}")
    else:
        FAIL_N += 1
        print(f"[FAIL] {name}: {detail}")


def main():
    print("=" * 72)
    print("ADIE wire value — Python conformance")
    print("=" * 72)

    # ── T01: encode boundaries (RFC 8949 §3.4.3) ──
    check("T01 encode 0", encode_uint_shortest(0) == b"\x00")
    check("T02 encode 1", encode_uint_shortest(1) == b"\x01")
    check("T03 encode 23", encode_uint_shortest(23) == b"\x17")
    check("T04 encode 24", encode_uint_shortest(24) == b"\x18\x18")
    check("T05 encode 25", encode_uint_shortest(25) == b"\x18\x19")
    check("T06 encode 255", encode_uint_shortest(255) == b"\x18\xff")
    check("T07 encode 256", encode_uint_shortest(256) == b"\x19\x01\x00")
    check("T08 encode 257", encode_uint_shortest(257) == b"\x19\x01\x01")
    check("T09 encode 65535", encode_uint_shortest(65535) == b"\x19\xff\xff")
    check("T10 encode 65536", encode_uint_shortest(65536) == b"\x1a\x00\x01\x00\x00")
    check("T11 encode u32::MAX", encode_uint_shortest(0xFFFFFFFF) == b"\x1a\xff\xff\xff\xff")
    check("T12 encode u32::MAX+1",
          encode_uint_shortest(0x100000000) == b"\x1b\x00\x00\x00\x01\x00\x00\x00\x00")
    check("T13 encode u64::MAX",
          encode_uint_shortest(0xFFFFFFFFFFFFFFFF) == b"\x1b\xff\xff\xff\xff\xff\xff\xff\xff")

    # ── T14-T15: cmp respects RFC 8949 order ──
    check("T14 cmp(24,255) < 0", cmp_uint_rfc8949(24, 255) < 0)
    check("T15 cmp(255,256) < 0", cmp_uint_rfc8949(255, 256) < 0)

    # ── T16: full boundary sweep ──
    bounds = [0, 1, 23, 24, 25, 255, 256, 257, 65535, 65536,
              0xFFFFFFFF, 0x100000000, 0xFFFFFFFFFFFFFFFF]
    sweep_ok = True
    for i in range(len(bounds)):
        for j in range(i + 1, len(bounds)):
            if not (cmp_uint_rfc8949(bounds[i], bounds[j]) < 0):
                sweep_ok = False
                print(f"  FAIL: {bounds[i]} should be < {bounds[j]}")
    check("T16 full boundary sweep", sweep_ok)

    # ── T17: canonicalize sorts correctly ──
    entries = [(256, Text("c")), (24, Text("a")), (255, Text("b"))]
    sorted_e = canonicalize_map(entries)
    check("T17 canonicalize order",
          [e[0] for e in sorted_e] == [24, 255, 256])

    # ── T18: duplicate rejection (NOT dedup) ──
    dup = [(1, Text("a")), (2, Text("b")), (1, Text("c"))]
    try:
        canonicalize_map(dup)
        check("T18 duplicates rejected", False, "no exception")
    except DuplicateKey:
        check("T18 duplicates rejected", True)

    # ── T19: empty map ok ──
    check("T19 empty map", canonicalize_map([]) == ())

    # ── T20: already sorted ok ──
    sorted_in = [(0, Null()), (24, Bool(True)), (256, UInt(99))]
    out = canonicalize_map(sorted_in)
    check("T20 already-sorted preserved",
          [e[0] for e in out] == [0, 24, 256])

    # ── T21: AdieValue equality ──
    check("T21 UInt equality", UInt(1) == UInt(1))
    check("T22 UInt != Int", UInt(1) != Int(1))
    check("T23 Null equality", Null() == Null())
    check("T24 Bool true != false", Bool(True) != Bool(False))

    # ── T25: UInt range check ──
    try:
        UInt(-1)
        check("T25 UInt rejects -1", False, "no error")
    except ValueError:
        check("T25 UInt rejects -1", True)

    # ── T26: Int range check ──
    try:
        Int(0x8000000000000000)
        check("T26 Int rejects overflow", False, "no error")
    except ValueError:
        check("T26 Int rejects overflow", True)

    # ── T27: encode_uint_shortest rejects > u64::MAX ──
    try:
        encode_uint_shortest(0x10000000000000000)
        check("T27 encode rejects >u64::MAX", False, "no error")
    except ValueError:
        check("T27 encode rejects >u64::MAX", True)

    # ── T28: frozen dataclasses (immutable) ──
    u = UInt(5)
    try:
        u.value = 6  # type: ignore
        check("T28 UInt immutable", False, "mutation allowed")
    except Exception:
        check("T28 UInt immutable", True)

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
