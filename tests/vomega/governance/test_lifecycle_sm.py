#!/usr/bin/env python3
"""Lifecycle state machine."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from enterpriseguard.adie.canonical.lifecycle import DecisionLifecycle as L
from enterpriseguard.adie.canonical.lifecycle_sm import (
    is_legal, require_legal, transition, legal_transitions,
    LifecycleTransitionError, TERMINAL, all_states,
)

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

def expect_raise(n, fn, exc=LifecycleTransitionError):
    try:
        fn(); check(n, False, "did not raise")
    except exc: check(n, True)
    except Exception as e: check(n, False, f"wrong exc {type(e).__name__}")

print("="*72); print("Lifecycle state machine"); print("="*72)

# Forward path
forward = [
    (L.PROPOSED, L.VALIDATED), (L.VALIDATED, L.AUTHORIZED),
    (L.AUTHORIZED, L.EMITTED), (L.EMITTED, L.EXECUTED_EXTERNAL),
    (L.EXECUTED_EXTERNAL, L.OBSERVED), (L.OBSERVED, L.ASSESSED),
    (L.ASSESSED, L.CLOSED),
]
for i, (a, b) in enumerate(forward):
    check(f"S{i+1:02d} {a.value}->{b.value} legal", is_legal(a, b))

# Skips forbidden
for i, (a, b) in enumerate([
    (L.PROPOSED, L.AUTHORIZED), (L.PROPOSED, L.EMITTED),
    (L.VALIDATED, L.EMITTED), (L.AUTHORIZED, L.EXECUTED_EXTERNAL),
    (L.EMITTED, L.OBSERVED), (L.EXECUTED_EXTERNAL, L.ASSESSED),
]):
    check(f"S{i+8:02d} skip {a.value}->{b.value} illegal", not is_legal(a, b))

# Backward forbidden
check("S14 backward AUTHORIZED->VALIDATED illegal",
      not is_legal(L.AUTHORIZED, L.VALIDATED))
check("S15 backward EMITTED->AUTHORIZED illegal",
      not is_legal(L.EMITTED, L.AUTHORIZED))

# Any state -> CLOSED allowed
for i, s in enumerate([L.PROPOSED, L.VALIDATED, L.AUTHORIZED,
                        L.EMITTED, L.EXECUTED_EXTERNAL, L.OBSERVED, L.ASSESSED]):
    check(f"S{i+16:02d} {s.value}->CLOSED legal", is_legal(s, L.CLOSED))

# CLOSED is terminal
check("S23 CLOSED terminal", L.CLOSED in TERMINAL)
check("S24 CLOSED has no outgoing", len(legal_transitions(L.CLOSED)) == 0)

# Full coverage: 8 sources x 8 dests = 64 pairs, exhaustively classify
states = list(L)
legal_count = 0
for s in states:
    for d in states:
        if is_legal(s, d): legal_count += 1
check("S25 legal-pair total == 13", legal_count == 13, f"got {legal_count}")

# require_legal raises on illegal
expect_raise("S26 require_legal on illegal", lambda: require_legal(L.PROPOSED, L.EMITTED))
require_legal(L.PROPOSED, L.VALIDATED); check("S27 require_legal on legal", True)

# transition to EXECUTED_EXTERNAL requires external_observation=True
expect_raise("S28 EXECUTED_EXTERNAL requires external_observation=True",
             lambda: transition(L.EMITTED, L.EXECUTED_EXTERNAL))
t = transition(L.EMITTED, L.EXECUTED_EXTERNAL, external_observation=True)
check("S29 EXECUTED_EXTERNAL with external_observation=True",
      t.external is True and t.dst is L.EXECUTED_EXTERNAL)

# transition record for non-external
t2 = transition(L.PROPOSED, L.VALIDATED)
check("S30 normal transition has external=False", t2.external is False)

# all_states returns 8
check("S31 all_states returns 8", len(all_states()) == 8)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
