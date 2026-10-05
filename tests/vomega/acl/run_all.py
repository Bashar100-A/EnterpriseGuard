#!/usr/bin/env python3
"""ADIE-ACL v0.1 — conformance + attack suite (Phase 1.7)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from protocol.acl.ast import (
    ACLError, AND, OR, NOT, TRUE, FALSE,
    EQ, NEQ, LT, LTE, GT, GTE, IN, EXISTS,
    FIELD, INT, STR, BOOL, validate,
)
from protocol.acl.eval import eval_checked, PASS, FAIL, UNKNOWN
from protocol.acl.normalize import canonical_ast, canonical_bytes


PASS_N = FAIL_N = 0
RESULTS = []


def run(vid, name, fn, expected):
    global PASS_N, FAIL_N
    try:
        actual = fn()
    except ACLError as e:
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


# ───────────── helpers ─────────────
def ev(e, s=None):
    return eval_checked(e, s or {})


def norm(e):
    return canonical_ast(e)


# ───────────── A01–A08: Kleene basics ─────────────
def a01(): return ev(TRUE());                          # PASS
def a02(): return ev(FALSE());                         # FAIL
def a03(): return ev(NOT(TRUE()));                     # FAIL
def a04(): return ev(NOT(FALSE()));                    # PASS
def a05(): return ev(NOT(EXISTS("missing")));          # NOT(FAIL)=PASS
def a06(): return ev(AND(TRUE(), TRUE()));             # PASS
def a07(): return ev(AND(TRUE(), FALSE()));            # FAIL
def a08(): return ev(OR(FALSE(), TRUE()));             # PASS


# ───────────── A09–A16: Kleene UNKNOWN semantics ─────────────
def a09():
    # EQ on missing field → UNKNOWN (not FAIL)
    return ev(EQ(FIELD("a.x"), INT(1)), {"a": {}})
def a10():
    # AND(PASS, UNKNOWN) → UNKNOWN
    return ev(AND(TRUE(), EQ(FIELD("a.x"), INT(1))), {"a": {}})
def a11():
    # AND(FAIL, UNKNOWN) → FAIL
    return ev(AND(FALSE(), EQ(FIELD("a.x"), INT(1))), {"a": {}})
def a12():
    # OR(FAIL, UNKNOWN) → UNKNOWN
    return ev(OR(FALSE(), EQ(FIELD("a.x"), INT(1))), {"a": {}})
def a13():
    # OR(PASS, UNKNOWN) → PASS
    return ev(OR(TRUE(), EQ(FIELD("a.x"), INT(1))), {"a": {}})
def a14():
    # NOT(UNKNOWN) → UNKNOWN
    return ev(NOT(EQ(FIELD("a.x"), INT(1))), {"a": {}})
def a15():
    # EXISTS(present) → PASS
    return ev(EXISTS("a.b"), {"a": {"b": 1}})
def a16():
    # EXISTS(absent) → FAIL (not UNKNOWN)
    return ev(EXISTS("a.x"), {"a": {"b": 1}})


# ───────────── A17–A24: comparisons + IN ─────────────
def a17(): return ev(EQ(INT(5), INT(5)))
def a18(): return ev(NEQ(INT(5), INT(6)))
def a19(): return ev(LT(INT(3), INT(5)))
def a20(): return ev(GTE(INT(5), INT(5)))
def a21(): return ev(EQ(STR("x"), STR("x")))
def a22(): return ev(IN(STR("x"), ["x", "y"]))
def a23(): return ev(IN(STR("z"), ["x", "y"]))
def a24(): return ev(EQ(FIELD("a.b"), INT(1)), {"a": {"b": 1}})


# ───────────── A25–A32: error cases ─────────────
def a25():
    # EQ int/str → E200_TYPE_MISMATCH
    return ev(EQ(INT(5), STR("x")))
def a26():
    # LT on bool → E200
    return ev(LT(BOOL(True), BOOL(False)))
def a27():
    # unknown operator
    return eval_checked({"op": "XYZZY"}, {})
def a28():
    # malformed AST (missing op)
    return eval_checked({"no_op": True}, {})
def a29():
    # AND() empty
    return eval_checked({"op": "AND", "args": []}, {})
def a30():
    # OR() empty
    return eval_checked({"op": "OR", "args": []}, {})
def a31():
    # INT with bool value → E211
    return eval_checked({"op": "EQ",
                        "args": [{"t": "INT", "v": True},
                                 {"t": "INT", "v": 1}]}, {})
def a32():
    # depth > 32 → E208
    e = TRUE()
    for _ in range(40):
        e = NOT(e)
    return eval_checked(e, {})


# ───────────── A33–A40: normalization ─────────────
def a33(): return norm(NOT(NOT(TRUE())))              # {'op':'TRUE'}
def a34(): return norm(AND(TRUE(), TRUE()))           # {'op':'TRUE'}
def a35(): return norm(AND(TRUE(), FALSE()))          # {'op':'FALSE'}
def a36(): return norm(OR(FALSE(), TRUE()))           # {'op':'TRUE'}
def a37(): return norm(AND(TRUE()))                   # {'op':'TRUE'}
def a38():
    # flatten AND nested
    return norm(AND(AND(TRUE(), TRUE()), TRUE()))     # {'op':'TRUE'}
def a39():
    # OR with all FALSE collapses to FALSE
    return norm(OR(FALSE(), FALSE()))                 # {'op':'FALSE'}
def a40():
    # commutative sort determinism
    e1 = norm(AND(EQ(INT(2), INT(2)), EQ(INT(1), INT(1))))
    e2 = norm(AND(EQ(INT(1), INT(1)), EQ(INT(2), INT(2))))
    return "SAME" if canonical_bytes(e1) == canonical_bytes(e2) else "DIFF"


TESTS = [
    ("A01", "TRUE", PASS, a01),
    ("A02", "FALSE", FAIL, a02),
    ("A03", "NOT(TRUE)", FAIL, a03),
    ("A04", "NOT(FALSE)", PASS, a04),
    ("A05", "NOT(EXISTS missing)", PASS, a05),
    ("A06", "AND(T,T)", PASS, a06),
    ("A07", "AND(T,F)", FAIL, a07),
    ("A08", "OR(F,T)", PASS, a08),
    ("A09", "EQ on missing → UNKNOWN", UNKNOWN, a09),
    ("A10", "AND(P,UNK) → UNKNOWN", UNKNOWN, a10),
    ("A11", "AND(F,UNK) → FAIL", FAIL, a11),
    ("A12", "OR(F,UNK) → UNKNOWN", UNKNOWN, a12),
    ("A13", "OR(P,UNK) → PASS", PASS, a13),
    ("A14", "NOT(UNK) → UNKNOWN", UNKNOWN, a14),
    ("A15", "EXISTS present → PASS", PASS, a15),
    ("A16", "EXISTS absent → FAIL", FAIL, a16),
    ("A17", "EQ int", PASS, a17),
    ("A18", "NEQ int", PASS, a18),
    ("A19", "LT int", PASS, a19),
    ("A20", "GTE int", PASS, a20),
    ("A21", "EQ str", PASS, a21),
    ("A22", "IN present", PASS, a22),
    ("A23", "IN absent", FAIL, a23),
    ("A24", "FIELD present EQ", PASS, a24),
    ("A25", "EQ int/str → E200", "E200_TYPE_MISMATCH", a25),
    ("A26", "LT bool → E200", "E200_TYPE_MISMATCH", a26),
    ("A27", "unknown op → E201", "E201_UNKNOWN_OPERATOR", a27),
    ("A28", "malformed → E202", "E202_MALFORMED_AST", a28),
    ("A29", "AND() → E209", "E209_EMPTY_AND", a29),
    ("A30", "OR() → E210", "E210_EMPTY_OR", a30),
    ("A31", "INT bool → E211", "E211_NON_CANONICAL_INT", a31),
    ("A32", "depth>32 → E208", "E208_NESTED_TOO_DEEP", a32),
    ("A33", "norm NOT NOT", {"op": "TRUE"}, a33),
    ("A34", "norm AND(T,T)", {"op": "TRUE"}, a34),
    ("A35", "norm AND(T,F)", {"op": "FALSE"}, a35),
    ("A36", "norm OR(F,T)", {"op": "TRUE"}, a36),
    ("A37", "norm AND(T)", {"op": "TRUE"}, a37),
    ("A38", "norm flatten AND", {"op": "TRUE"}, a38),
    ("A39", "norm OR(F,F)", {"op": "FALSE"}, a39),
    ("A40", "commutative sort", "SAME", a40),
]


def main():
    print("=" * 72)
    print("ADIE-ACL v0.1 — conformance + attack suite")
    print("=" * 72)
    for vid, name, expected, fn in TESTS:
        run(vid, name, fn, expected)

    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)

    if FAIL_N:
        print("\nFailed:")
        for vid, name, exp, act, ok in RESULTS:
            if not ok:
                print(f"  {vid}: {name} → expected {exp!r}, got {act!r}")

    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
