#!/usr/bin/env python3
"""TBS builder — Python conformance tests."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from protocol.hybrid.tbs import DOMAIN_TAG, build_tbs


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
    print("ADIE TBS builder — Python conformance")
    print("=" * 72)

    # T01: domain tag exact bytes
    check("T01 domain tag = 12 bytes",
          len(DOMAIN_TAG) == 12,
          f"got {len(DOMAIN_TAG)}")
    check("T02 domain tag exact bytes",
          DOMAIN_TAG == bytes.fromhex("414449452d5349472d563200"),
          f"got {DOMAIN_TAG.hex()}")

    # T03: minimal cert
    minimal = {"dcp_version": "2.1", "claim_id": "c1"}
    tbs = build_tbs(minimal)
    check("T03 minimal TBS starts with domain tag",
          tbs.startswith(DOMAIN_TAG))
    check("T04 minimal TBS body is JCS",
          tbs[12:] == b'{"claim_id":"c1","dcp_version":"2.1"}',
          f"got {tbs[12:]!r}")

    # T05: reject cert with signatures field
    try:
        build_tbs({"signatures": []})
        check("T05 reject signatures field", False, "no error")
    except ValueError:
        check("T05 reject signatures field", True)

    # T06: reject cert with signature (singular) field
    try:
        build_tbs({"signature": {}})
        check("T06 reject signature field", False, "no error")
    except ValueError:
        check("T06 reject signature field", True)

    # T07: empty dict works
    tbs = build_tbs({})
    check("T07 empty dict TBS = tag || {}",
          tbs == DOMAIN_TAG + b"{}",
          f"got {tbs[12:]!r}")

    # T08: Unicode content
    tbs = build_tbs({"note": "café"})
    check("T08 Unicode JCS preserved",
          tbs.endswith('{"note":"café"}'.encode("utf-8")),
          f"got {tbs[12:]!r}")

    # T09: nested object sorted keys
    tbs = build_tbs({"b": {"y": 1, "x": 2}, "a": 3})
    body = tbs[12:]
    check("T09 nested sorted",
          body == b'{"a":3,"b":{"x":2,"y":1}}',
          f"got {body!r}")

    # T10: non-dict raises
    try:
        build_tbs([])
        check("T10 reject non-dict", False, "no error")
    except TypeError:
        check("T10 reject non-dict", True)

    # T11: determinism
    cert = {"dcp_version": "2.1", "claim_id": "c1", "issuer": {"did": "did:adie:i1"}}
    a = build_tbs(cert)
    b = build_tbs(cert)
    check("T11 determinism", a == b)

    # T12: JCS body has no whitespace
    tbs = build_tbs({"a": 1, "b": 2})
    check("T12 no whitespace in JCS",
          b" " not in tbs[12:] and b"\n" not in tbs[12:])

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
