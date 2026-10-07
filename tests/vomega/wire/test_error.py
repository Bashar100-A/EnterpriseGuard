#!/usr/bin/env python3
"""ADIE wire errors — Python conformance tests."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.wire.error import (
    CborError,
    Malformed, Trailing, Indefinite, Float, Tag, DuplicateKey,
    NonCanonicalInt, NonCanonicalMap, InvalidUtf8,
    TypeMismatch, MissingField, UnknownCritical, Version, Ambiguous,
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


def main():
    print("=" * 72)
    print("ADIE wire errors — Python conformance")
    print("=" * 72)

    # T01: stable codes
    check("T01 Malformed.code",
          Malformed("x").code == "E_WIRE_MALFORMED")
    check("T02 Trailing.code",
          Trailing(1).code == "E_WIRE_TRAILING")
    check("T03 Indefinite.code",
          Indefinite().code == "E_WIRE_INDEFINITE")
    check("T04 Float.code",
          Float().code == "E_WIRE_FLOAT")
    check("T05 Tag.code",
          Tag(1).code == "E_WIRE_TAG")
    check("T06 DuplicateKey.code",
          DuplicateKey().code == "E_WIRE_DUP_KEY")
    check("T07 NonCanonicalInt.code",
          NonCanonicalInt().code == "E_WIRE_NONCANONICAL_INT")
    check("T08 NonCanonicalMap.code",
          NonCanonicalMap().code == "E_WIRE_NONCANONICAL_MAP")
    check("T09 InvalidUtf8.code",
          InvalidUtf8().code == "E_WIRE_INVALID_UTF8")
    check("T10 TypeMismatch.code",
          TypeMismatch("x", "y").code == "E_WIRE_TYPE_MISMATCH")
    check("T11 MissingField.code",
          MissingField("x").code == "E_WIRE_MISSING_FIELD")
    check("T12 UnknownCritical.code",
          UnknownCritical(99).code == "E_WIRE_UNKNOWN_CRITICAL")
    check("T13 Version.code",
          Version("2.0").code == "E_WIRE_VERSION")
    check("T14 Ambiguous.code",
          Ambiguous("x").code == "E_WIRE_AMBIGUOUS")

    # T15: display includes code
    check("T15 Trailing str includes code",
          str(Trailing(3)).startswith("E_WIRE_TRAILING"))
    check("T16 Trailing str includes count",
          "3" in str(Trailing(3)))

    # T17: MissingField str shows name
    s = str(MissingField("binding"))
    check("T17 MissingField str includes 'binding'",
          "binding" in s and "E_WIRE_MISSING_FIELD" in s)

    # T18: Version str shows value
    s = str(Version("9.9"))
    check("T18 Version str includes '9.9'",
          "9.9" in s and "E_WIRE_VERSION" in s)

    # T19: Tag str shows tag number
    s = str(Tag(42))
    check("T19 Tag str includes 42",
          "42" in s and "E_WIRE_TAG" in s)

    # T20: all inherit from CborError
    all_errors = [
        Malformed(""), Trailing(0), Indefinite(), Float(), Tag(0),
        DuplicateKey(), NonCanonicalInt(), NonCanonicalMap(),
        InvalidUtf8(), TypeMismatch("", ""), MissingField(""),
        UnknownCritical(0), Version(""), Ambiguous(""),
    ]
    check("T20 all inherit CborError",
          all(isinstance(e, CborError) for e in all_errors))

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
