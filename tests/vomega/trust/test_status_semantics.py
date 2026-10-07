#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from enterpriseguard.adie.canonical.trust.status import TrustStatus as T, TERMINAL, REVERSIBLE

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

print("="*72); print("TrustStatus semantics"); print("="*72)

for i, (name, val) in enumerate([
    ("ACTIVE","active"),("SUSPENDED","suspended"),("REVOKED","revoked"),
    ("EXPIRED","expired"),("SUPERSEDED","superseded")]):
    check(f"S{i+1:02d} {name}.value == {val!r}", getattr(T, name).value == val)

check("S06 5 states total", len(list(T)) == 5)

# Terminal
for i, s in enumerate([T.REVOKED, T.EXPIRED, T.SUPERSEDED]):
    check(f"S{i+7:02d} {s.value} in TERMINAL", s in TERMINAL)
for i, s in enumerate([T.ACTIVE, T.SUSPENDED]):
    check(f"S{i+10:02d} {s.value} NOT terminal", s not in TERMINAL)

# Reversible
for i, s in enumerate([T.ACTIVE, T.SUSPENDED]):
    check(f"S{i+12:02d} {s.value} reversible", s in REVERSIBLE)
for i, s in enumerate([T.REVOKED, T.EXPIRED, T.SUPERSEDED]):
    check(f"S{i+14:02d} {s.value} NOT reversible", s not in REVERSIBLE)

# Non-overlap
check("S17 TERMINAL and REVERSIBLE disjoint", TERMINAL & REVERSIBLE == set())
check("S18 union covers all", TERMINAL | REVERSIBLE == set(T))

# String-typed
for i, s in enumerate(T):
    check(f"S{i+19:02d} {s.name} is str-instanceof", isinstance(s, str))

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
