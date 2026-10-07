#!/usr/bin/env python3
"""ADIE wire profile validation — Python conformance tests."""
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.wire.profile import validate, MAX_DEPTH
from protocol.wire.value import (
    UInt, Int, Bytes, Text, Array, Map, Bool, Null,
)
from protocol.wire.error import (
    Float, Tag, TypeMismatch, Malformed, NonCanonicalInt,
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


def expect_err(fn, err_type):
    try:
        fn()
        return False
    except err_type:
        return True
    except Exception:
        return False


def main():
    print("=" * 72)
    print("ADIE wire profile validation — Python conformance")
    print("=" * 72)

    # ── Accepts primitives ──
    check("T01 accepts None", validate(None) == Null())
    check("T02 accepts True", validate(True) == Bool(True))
    check("T03 accepts False", validate(False) == Bool(False))
    check("T04 accepts empty text", validate("") == Text(""))
    check("T05 accepts text", validate("hello") == Text("hello"))
    check("T06 accepts empty bytes", validate(b"") == Bytes(b""))
    check("T07 accepts bytes", validate(b"\x01\x02\x03") == Bytes(b"\x01\x02\x03"))
    check("T08 accepts uint 0", validate(0) == UInt(0))
    check("T09 accepts uint 42", validate(42) == UInt(42))
    check("T10 accepts uint u64::MAX", validate(0xFFFFFFFFFFFFFFFF) == UInt(0xFFFFFFFFFFFFFFFF))
    check("T11 accepts negative -1", validate(-1) == Int(-1))
    check("T12 accepts negative i64::MIN",
          validate(-0x8000000000000000) == Int(-0x8000000000000000))

    # ── Rejects floats ──
    check("T13 rejects float 1.0",
          expect_err(lambda: validate(1.0), Float))
    check("T14 rejects float NaN-ish",
          expect_err(lambda: validate(float("inf")), Float))

    # ── Arrays ──
    check("T15 accepts empty array", validate([]) == Array(()))
    check("T16 accepts array of primitives",
          validate(["a", 1, True, None]) == Array((
              Text("a"), UInt(1), Bool(True), Null(),
          )))
    check("T17 rejects array with float",
          expect_err(lambda: validate(["a", 1.5]), Float))

    # ── Maps ──
    check("T18 accepts empty map", validate({}) == Map(()))
    check("T19 accepts integer-keyed map",
          validate({1: "a", 2: "b"}) == Map(((1, Text("a")), (2, Text("b")))))
    check("T20 canonicalizes unsorted map",
          validate({2: "b", 1: "a"}) == Map(((1, Text("a")), (2, Text("b")))))
    check("T21 rejects text key",
          expect_err(lambda: validate({"k": 1}), TypeMismatch))
    check("T22 rejects bytes key",
          expect_err(lambda: validate({b"k": 1}), TypeMismatch))
    check("T23 rejects negative key",
          expect_err(lambda: validate({-1: "x"}), TypeMismatch))
    check("T24 rejects bool key",
          expect_err(lambda: validate({True: 1}), TypeMismatch))

    # ── Depth ──
    def nested(depth):
        v = None
        for _ in range(depth):
            v = [v]
        return v

    check("T25 accepts depth 32", validate(nested(32)) is not None)
    check("T26 rejects depth 33",
          expect_err(lambda: validate(nested(33)), Malformed))

    # ── Nested structure ──
    check("T27 accepts nested",
          validate({1: "v", 2: [1, 2], 3: {10: False}}) is not None)

    # ── Out-of-range int ──
    check("T28 rejects int > u64::MAX",
          expect_err(lambda: validate(0x10000000000000000), NonCanonicalInt))

    # ── Tag-result types (defense-in-depth) ──
    check("T29 rejects datetime",
          expect_err(lambda: validate(datetime.now(timezone.utc)), Tag))

    # ── Unrecognised type ──
    class Custom:
        pass

    check("T30 rejects custom object",
          expect_err(lambda: validate(Custom()), Malformed))

    # ── UInt range guard on construction ──
    check("T31 UInt rejects -1 constructor",
          expect_err(lambda: UInt(-1), ValueError))

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
