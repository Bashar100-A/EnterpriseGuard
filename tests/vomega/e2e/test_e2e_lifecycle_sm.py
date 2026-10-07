#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.lifecycle import DecisionLifecycle as L
from enterpriseguard.adie.canonical.lifecycle_sm import (
    is_legal, transition, LifecycleTransitionError, legal_transitions, TERMINAL)

h = Harness("E2E lifecycle state machine — exhaustive 8x8")

states = list(L)
legal_count = 0
illegal_count = 0
for src in states:
    for dst in states:
        if is_legal(src, dst): legal_count += 1
        else: illegal_count += 1

h.check("L01 exactly 13 legal pairs", legal_count == 13, f"got {legal_count}")
h.check("L02 exactly 51 illegal pairs", illegal_count == 51, f"got {illegal_count}")
h.check("L03 64 total pairs", legal_count + illegal_count == 64)

# Legal forward
for i, (a, b) in enumerate([
    (L.PROPOSED, L.VALIDATED), (L.VALIDATED, L.AUTHORIZED),
    (L.AUTHORIZED, L.EMITTED), (L.EMITTED, L.EXECUTED_EXTERNAL),
    (L.EXECUTED_EXTERNAL, L.OBSERVED), (L.OBSERVED, L.ASSESSED),
    (L.ASSESSED, L.CLOSED)]):
    h.check(f"L{i+4:02d} forward {a.value}->{b.value}", is_legal(a, b))

# Illegal skips (any non-CLOSED -> CLOSED is LEGAL by 3B design,
# as early-abort; only skip-jumps are illegal).
for i, (a, b) in enumerate([
    (L.PROPOSED, L.AUTHORIZED), (L.PROPOSED, L.EMITTED),
    (L.PROPOSED, L.EXECUTED_EXTERNAL), (L.VALIDATED, L.EMITTED),
    (L.VALIDATED, L.EXECUTED_EXTERNAL),
    (L.EMITTED, L.AUTHORIZED), (L.CLOSED, L.PROPOSED)]):
    h.check(f"L{i+11:02d} illegal {a.value}->{b.value}", not is_legal(a, b))

# Every non-CLOSED -> CLOSED legal
for i, s in enumerate([x for x in states if x is not L.CLOSED]):
    h.check(f"L{i+19:02d} {s.value}->CLOSED legal", is_legal(s, L.CLOSED))

# EXECUTED_EXTERNAL requires external_observation
try:
    transition(L.EMITTED, L.EXECUTED_EXTERNAL)
    h.check("L26 EXECUTED_EXTERNAL requires ext_obs flag", False)
except LifecycleTransitionError:
    h.check("L26 EXECUTED_EXTERNAL requires ext_obs flag", True)

t = transition(L.EMITTED, L.EXECUTED_EXTERNAL, external_observation=True)
h.check("L27 EXECUTED_EXTERNAL external=True", t.external is True)

h.check("L28 CLOSED terminal", L.CLOSED in TERMINAL)
h.check("L29 CLOSED no outgoing", len(legal_transitions(L.CLOSED)) == 0)

h.finish()
