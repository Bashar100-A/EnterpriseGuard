#!/usr/bin/env python3
"""Legacy B -> canonical adapter (one direction)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from enterpriseguard.adie.canonical.compat_decision_b import (
    legacy_status_to_authorization, legacy_contract_to_neutral,
    LegacyAdapterError,
)
from enterpriseguard.adie.canonical.lifecycle import AuthorizationStatus as A

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

def expect_raise(n, fn, exc=LegacyAdapterError):
    try: fn(); check(n, False, "did not raise")
    except exc: check(n, True)
    except Exception as e: check(n, False, f"wrong exc {type(e).__name__}")

print("="*72); print("Legacy B adapter"); print("="*72)

# Status mapping
for i, (legacy, expected) in enumerate([
    ("pending", A.PENDING), ("PENDING", A.PENDING),
    ("authorized", A.AUTHORIZED), ("AUTHORIZED", A.AUTHORIZED),
    ("denied", A.DENIED), ("expired", A.EXPIRED), ("superseded", A.SUPERSEDED),
]):
    check(f"C{i+1:02d} {legacy!r} -> {expected.value}",
          legacy_status_to_authorization(legacy) == expected)

expect_raise("C08 unknown status", lambda: legacy_status_to_authorization("bogus"))

# Contract projection
class FakeLegacyStatus:
    def __init__(self, v): self.value = v
class FakeLegacyContract:
    def __init__(self):
        self.decision_id = "b-1"
        self.evaluation_id = "ev-1"
        self.policy_id = "pol-x"
        self.status = FakeLegacyStatus("authorized")
        self.authorized = True
        self.target_resource_id = "res-1"
        self.expires_at = None

neutral = legacy_contract_to_neutral(FakeLegacyContract())
check("C09 legacy_decision_id", neutral["legacy_decision_id"] == "b-1")
check("C10 authorization_status", neutral["authorization_status"] is A.AUTHORIZED)
check("C11 legacy_authorized_claim preserved",
      neutral["legacy_authorized_claim"] is True)
check("C12 does NOT invent authority_id", "authority_id" not in neutral)

# Adapter does NOT upgrade legacy "authorized" claim to canonical Authority
# (it only maps to the authorization axis; explicit Authority is still required)
check("C13 no Authority object emitted",
      "authority" not in neutral and "authority_id" not in neutral)

# Denied path
f = FakeLegacyContract(); f.status = FakeLegacyStatus("denied"); f.authorized = False
n2 = legacy_contract_to_neutral(f)
check("C14 denied -> DENIED", n2["authorization_status"] is A.DENIED)
check("C15 denied authorized_claim False",
      n2["legacy_authorized_claim"] is False)

expect_raise("C16 bad object",
             lambda: legacy_contract_to_neutral(object()))

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
