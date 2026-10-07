#!/usr/bin/env python3
"""Canonical DecisionLifecycle + AuthorizationStatus — axis separation."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from enterpriseguard.adie.canonical.lifecycle import (
    DecisionLifecycle as L, AuthorizationStatus as A, EXECUTES_SECURITY_ACTIONS,
)

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

print("="*72); print("Canonical lifecycle + auth axis"); print("="*72)

# Lifecycle = 8 states
check("L01 lifecycle has 8 states", len(list(L)) == 8)
for i, name in enumerate(["PROPOSED","VALIDATED","AUTHORIZED","EMITTED",
                          "EXECUTED_EXTERNAL","OBSERVED","ASSESSED","CLOSED"]):
    check(f"L{i+2:02d} has {name}", hasattr(L, name))

# Authorization = 5 states
check("L10 authorization has 5 states", len(list(A)) == 5)
for i, name in enumerate(["PENDING","AUTHORIZED","DENIED","EXPIRED","SUPERSEDED"]):
    check(f"L{i+11} has AUTH {name}", hasattr(A, name))

# Separation: different enum types (values may coincide on "authorized")
lc = {x.value for x in L}
ac = {x.value for x in A}
check("L16 axis types are disjoint at type level",
      all(not isinstance(a, type(l)) and type(a) is not type(l)
          for l in L for a in A))
check("L16b both axes have distinct enum classes",
      type(list(L)[0]) is not type(list(A)[0]))

# EXECUTES_SECURITY_ACTIONS = False
check("L17 EXECUTES_SECURITY_ACTIONS is False", EXECUTES_SECURITY_ACTIONS is False)

# EXECUTED_EXTERNAL != AUTHORIZED
check("L18 EXECUTED_EXTERNAL != AUTHORIZED",
      L.EXECUTED_EXTERNAL != A.AUTHORIZED)
check("L19 EXECUTED_EXTERNAL not in authorization",
      "executed_external" not in ac)
# AUTHORIZED appears in both axes with same string but they are
# DIFFERENT objects of DIFFERENT enum classes. That is the invariant.
check("L20 L.AUTHORIZED and A.AUTHORIZED are different enum types",
      type(L.AUTHORIZED) is not type(A.AUTHORIZED))
check("L20b L.AUTHORIZED is not A.AUTHORIZED",
      L.AUTHORIZED is not A.AUTHORIZED)
check("L20c EXECUTED_EXTERNAL != any auth value",
      L.EXECUTED_EXTERNAL.value not in ac)
check("L20d EMITTED != any auth value",
      L.EMITTED.value not in ac)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
