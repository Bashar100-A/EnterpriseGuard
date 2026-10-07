#!/usr/bin/env python3
"""ADIE raw-byte scanner — Python conformance tests."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.wire.rawcheck import scan_top_level, MAX_DEPTH
from protocol.wire.error import (
    Malformed, Trailing, Indefinite, Float, Tag,
    NonCanonicalInt, InvalidUtf8,
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
    return scan_top_level(data)


def expect_err(data, err_type):
    try:
        scan_top_level(data)
        return False
    except err_type:
        return True
    except Exception:
        return False


def main():
    print("=" * 72)
    print("ADIE raw-byte scanner — Python conformance")
    print("=" * 72)

    # ── Valid primitives ──
    check("T01 valid null", ok(b"\xf6") == 1)
    check("T02 valid true", ok(b"\xf5") == 1)
    check("T03 valid false", ok(b"\xf4") == 1)
    check("T04 valid uint 0", ok(b"\x00") == 1)
    check("T05 valid uint 1", ok(b"\x01") == 1)
    check("T06 valid uint 23", ok(b"\x17") == 1)
    check("T07 valid uint 24 (u8 form)", ok(b"\x18\x18") == 2)
    check("T08 valid uint 256 (u16 form)", ok(b"\x19\x01\x00") == 3)
    check("T09 valid neg int -1", ok(b"\x20") == 1)
    check("T10 valid neg int -24", ok(b"\x37") == 1)
    check("T11 valid neg int -25 (u8 form)", ok(b"\x38\x18") == 2)
    check("T12 valid empty bytes", ok(b"\x40") == 1)
    check("T13 valid empty text", ok(b"\x60") == 1)
    check("T14 valid bytes payload", ok(b"\x43\x01\x02\x03") == 4)
    check("T15 valid text payload", ok(b"\x62\x68\x69") == 3)  # "hi"
    check("T16 valid utf-8 é", ok(b"\x62\xc3\xa9") == 3)
    check("T17 valid empty array", ok(b"\x80") == 1)
    check("T18 valid empty map", ok(b"\xa0") == 1)
    check("T19 valid nested {1:[true,null]}",
          ok(b"\xa1\x01\x82\xf5\xf6") == 5)

    # ── Trailing bytes ──
    check("T20 trailing after null",
          expect_err(b"\xf6\x00", Trailing))
    check("T21 trailing after map",
          expect_err(b"\xa0\xff", Trailing))

    # ── Indefinite-length ──
    check("T22 indefinite map",
          expect_err(b"\xbf\x01\x61\x78\xff", Indefinite))
    check("T23 indefinite array",
          expect_err(b"\x9f\x01\xff", Indefinite))
    check("T24 indefinite bytes",
          expect_err(b"\x5f\x41\x78\xff", Indefinite))
    check("T25 indefinite text",
          expect_err(b"\x7f\x61\x78\xff", Indefinite))

    # ── Floats ──
    check("T26 float16",
          expect_err(b"\xf9\x3c\x00", Float))
    check("T27 float32",
          expect_err(b"\xfa\x3f\x80\x00\x00", Float))
    check("T28 float64",
          expect_err(b"\xfb\x3f\xf0\x00\x00\x00\x00\x00\x00", Float))

    # ── Tags (authoritative) ──
    check("T29 tag 1",
          expect_err(b"\xc1\x01", Tag))
    check("T30 tag 0 (date string)",
          expect_err(b"\xc0\x6a" + b"2026-10-07", Tag))
    check("T31 tag 2 (bignum)",
          expect_err(b"\xc2\x41\x01", Tag))

    # ── Non-canonical integers ──
    check("T32 noncanonical uint8 for 1",
          expect_err(b"\x18\x01", NonCanonicalInt))
    check("T33 noncanonical uint16 for 1",
          expect_err(b"\x19\x00\x01", NonCanonicalInt))
    check("T34 noncanonical uint32 for 1",
          expect_err(b"\x1a\x00\x00\x00\x01", NonCanonicalInt))
    check("T35 noncanonical uint64 for 1",
          expect_err(b"\x1b\x00\x00\x00\x00\x00\x00\x00\x01", NonCanonicalInt))
    check("T36 noncanonical byte-string length",
          expect_err(b"\x58\x01\x78", NonCanonicalInt))

    # ── Undefined ──
    check("T37 undefined (0xf7)",
          expect_err(b"\xf7", Malformed))

    # ── Truncated input ──
    check("T38 truncated byte string",
          expect_err(b"\x43\x01\x02", Malformed))
    check("T39 empty input",
          expect_err(b"", Malformed))

    # ── Invalid UTF-8 ──
    check("T40 invalid utf-8",
          expect_err(b"\x62\xff\xfe", InvalidUtf8))

    # ── Stray break ──
    check("T41 stray break",
          expect_err(b"\xff", Malformed))

    # ── Depth ──
    deep_ok = b"\x81" * 32 + b"\xf6"
    check("T42 depth 32 ok", ok(deep_ok) == 33)

    deep_bad = b"\x81" * 33 + b"\xf6"
    check("T43 depth 33 rejected",
          expect_err(deep_bad, Malformed))

    # ── Non-bytes input ──
    try:
        scan_top_level("string")  # type: ignore
        check("T44 rejects non-bytes", False, "no error")
    except Malformed:
        check("T44 rejects non-bytes", True)

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
