#!/usr/bin/env python3
"""ADIE-REGISTRY v0.1 — conformance suite (Phase 1.9)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from protocol.meta.registry import (
    RegistrySnapshot, Entry, CompatibilityRecord,
    RegistryError, parse_id,
)
from protocol.meta.core import Universe


PASS_N = FAIL_N = 0
RESULTS = []


def run(vid, name, fn, expected):
    global PASS_N, FAIL_N
    try:
        actual = fn()
    except RegistryError as e:
        actual = e.code
    except Exception as e:
        actual = f"EXC:{type(e).__name__}"
    ok = actual == expected
    RESULTS.append((vid, name, expected, actual, ok))
    if ok: PASS_N += 1
    else:  FAIL_N += 1
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {vid}: {name}")
    if not ok:
        print(f"       expected: {expected!r}")
        print(f"       actual:   {actual!r}")


# ─── helpers ─────────────────────────────────────────────
def mk_entry(id_str, type_="template", status="ACTIVE",
             effective=None, expiry=None, payload=None):
    return Entry(
        type=type_, id=id_str, version="1.0",
        payload=payload or {"k": "v"}, status=status,
        effective=effective, expiry=expiry, issuer="key1")


def mk_compat(from_id, to_id, relation="EXACT",
              scope=(), proof_digest=None,
              effective="2026-01-01T00:00:00Z",
              expiry=None):
    return CompatibilityRecord(
        from_id=from_id, to_id=to_id, relation=relation,
        scope=scope, constraints={}, proof_digest=proof_digest,
        authority="k1", effective=effective, expiry=expiry, issuer="k1")


# ─── R01–R04: id parsing ─────────────────────────────────
def r01():
    ns, lid = parse_id("main:T1")
    return "PASS" if ns == "main" and lid == "T1" else "FAIL"

def r02():
    return _expect_code("E-META-23", lambda: parse_id("no_colon"))

def r03():
    return _expect_code("E-META-23", lambda: parse_id("Main:T1"))

def r04():
    return _expect_code("E-META-23", lambda: parse_id("main:has space"))


# ─── R05–R08: registration + fork ────────────────────────
def r05():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1"))
    return "PASS" if s.lookup("main:T1") is not None else "FAIL"

def r06():
    s = RegistrySnapshot(snapshot_epoch=1)
    e = mk_entry("main:T1")
    s.register(e)
    s.register(e)  # idempotent
    return "PASS"

def r07():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1", payload={"v": 1}))
    return _expect_code("E-META-13",
        lambda: s.register(mk_entry("main:T1", payload={"v": 2})))

def r08():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1", status="PROPOSED"))
    return "PASS" if s.lookup("main:T1") is None else "FAIL"


# ─── R09–R11: lifecycle ──────────────────────────────────
def r09():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1"))
    s.deprecate("main:T1")
    e = s.lookup("main:T1", require_status=None)
    return "PASS" if e.status == "DEPRECATED" else "FAIL"

def r10():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1"))
    s.revoke("main:T1")
    e = s.lookup("main:T1", require_status=None)
    return "PASS" if e.status == "REVOKED" else "FAIL"

def r11():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1"))
    s.revoke("main:T1")
    return _expect_code("E-META-16c", lambda: s.revoke("main:T1"))


# ─── R12–R13: temporal windows ───────────────────────────
def r12():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1", expiry="2030-01-01T00:00:00Z"))
    return _expect_code("E-META-25",
        lambda: s.lookup("main:T1", now="2031-01-01T00:00:00Z"))

def r13():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.register(mk_entry("main:T1", effective="2030-01-01T00:00:00Z"))
    return _expect_code("E-META-25",
        lambda: s.lookup("main:T1", now="2026-01-01T00:00:00Z"))


# ─── R14–R18: compatibility ──────────────────────────────
def r14():
    return _expect_code("E-META-17",
        lambda: mk_compat("main:A", "main:B", relation="SEMANTIC",
                          proof_digest=None))

def r15():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.declare_compat(mk_compat("main:A", "main:B", relation="EXACT"))
    return "PASS" if s.lookup_compat("main:A", "main:B") == "EXACT" else "FAIL"

def r16():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.declare_compat(mk_compat("main:A", "main:B"))
    s.declare_compat(mk_compat("main:B", "main:C"))
    return "PASS" if s.lookup_compat("main:A", "main:C") is None else "FAIL"

def r17():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.declare_compat(mk_compat("main:A", "main:B", scope=("audit",)))
    return _expect_code("E-META-27",
        lambda: s.lookup_compat("main:A", "main:B", scope=["wrong"]))

def r18():
    s = RegistrySnapshot(snapshot_epoch=1)
    s.declare_compat(mk_compat("main:A", "main:B",
        effective="2020-01-01T00:00:00Z", expiry="2021-01-01T00:00:00Z"))
    return _expect_code("E-META-26",
        lambda: s.lookup_compat("main:A", "main:B",
                                now="2026-01-01T00:00:00Z"))


# ─── R19–R20: snapshot-level ─────────────────────────────
def r19():
    s = RegistrySnapshot(snapshot_epoch=5)
    return _expect_code("E-META-28", lambda: s.check_replay(known_epoch=99))

def r20():
    s1 = RegistrySnapshot(snapshot_epoch=1)
    s2 = RegistrySnapshot(snapshot_epoch=1)
    s1.register(mk_entry("main:T1", payload={"v": 1}))
    s2.register(mk_entry("main:T1", payload={"v": 2}))
    conflicts = s1.diff_fork(s2)
    return "PASS" if "main:T1" in conflicts else "FAIL"


def _expect_code(code, fn):
    try:
        fn()
        return f"NO_RAISE({code})"
    except RegistryError as e:
        return "PASS" if e.code == code else f"WRONG({e.code})"


TESTS = [
    ("R01", "parse_id valid", r01, "PASS"),
    ("R02", "parse_id missing colon", r02, "PASS"),
    ("R03", "parse_id uppercase namespace", r03, "PASS"),
    ("R04", "parse_id space in local_id", r04, "PASS"),
    ("R05", "register basic entry", r05, "PASS"),
    ("R06", "idempotent register", r06, "PASS"),
    ("R07", "intra-snapshot fork", r07, "PASS"),
    ("R08", "PROPOSED not returned as ACTIVE", r08, "PASS"),
    ("R09", "deprecate ACTIVE", r09, "PASS"),
    ("R10", "revoke ACTIVE", r10, "PASS"),
    ("R11", "revoke REVOKED rejected", r11, "PASS"),
    ("R12", "lookup expired", r12, "PASS"),
    ("R13", "lookup not-yet-effective", r13, "PASS"),
    ("R14", "SEMANTIC needs proof", r14, "PASS"),
    ("R15", "EXACT compat lookup", r15, "PASS"),
    ("R16", "no transitive inference", r16, "PASS"),
    ("R17", "scope mismatch", r17, "PASS"),
    ("R18", "compat expired", r18, "PASS"),
    ("R19", "snapshot replay", r19, "PASS"),
    ("R20", "inter-snapshot fork", r20, "PASS"),
]


def main():
    print("=" * 72)
    print("ADIE-REGISTRY v0.1 — conformance suite")
    print("=" * 72)
    for vid, name, fn, expected in TESTS:
        run(vid, name, fn, expected)

    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)

    if FAIL_N:
        print("\nFailed:")
        for vid, name, exp, act, ok in RESULTS:
            if not ok:
                print(f"  {vid}: {name} -> expected {exp!r}, got {act!r}")

    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
