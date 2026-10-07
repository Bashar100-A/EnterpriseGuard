#!/usr/bin/env python3
"""Canonical DecisionContract with Stage-3B fields."""
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from enterpriseguard.adie.decision import (
    DecisionContract, DecisionContractError, DecisionIntent,
    DecisionLifecycle, AuthorizationStatus,
)

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

def expect_raise(n, fn, exc):
    try: fn(); check(n, False, "did not raise")
    except exc: check(n, True)
    except Exception as e: check(n, False, f"wrong exc {type(e).__name__}")

now = datetime.now(timezone.utc)
base = dict(
    decision_id="d1", intent=DecisionIntent.MONITOR,
    lifecycle=DecisionLifecycle.PROPOSED,
    decision_score=0.5, confidence=0.5,
    prediction_id="p1", policy_id="pol1",
    rationale="test", reason_codes=("R1",), created_at=now,
)

print("="*72); print("Canonical DecisionContract"); print("="*72)

c = DecisionContract(**base)
check("D01 constructed", c.decision_id == "d1")
check("D02 default authorization_status == PENDING",
      c.authorization_status is AuthorizationStatus.PENDING)
check("D03 default authority_id None", c.authority_id is None)
check("D04 executes_security_actions False", c.executes_security_actions is False)

# Set authorization to AUTHORIZED with lifecycle < AUTHORIZED -> reject
expect_raise("D05 auth=AUTHORIZED + lifecycle=PROPOSED rejected",
             lambda: DecisionContract(**{**base,
                                         "authorization_status": AuthorizationStatus.AUTHORIZED}),
             DecisionContractError)

expect_raise("D06 auth=AUTHORIZED + lifecycle=VALIDATED rejected",
             lambda: DecisionContract(**{**base,
                                         "lifecycle": DecisionLifecycle.VALIDATED,
                                         "authorization_status": AuthorizationStatus.AUTHORIZED}),
             DecisionContractError)

# auth=AUTHORIZED + lifecycle=AUTHORIZED -> OK
c_ok = DecisionContract(**{**base,
                           "lifecycle": DecisionLifecycle.AUTHORIZED,
                           "authorization_status": AuthorizationStatus.AUTHORIZED})
check("D07 auth=AUTHORIZED + lifecycle=AUTHORIZED accepted",
      c_ok.authorization_status is AuthorizationStatus.AUTHORIZED)

# auth=DENIED allowed on any lifecycle
c_denied = DecisionContract(**{**base, "authorization_status": AuthorizationStatus.DENIED})
check("D08 DENIED allowed on PROPOSED", c_denied.authorization_status is AuthorizationStatus.DENIED)

# new IDs visible in to_dict
d = c.to_dict()
for i, key in enumerate(["evidence_set_id","state_id","authority_id",
                          "checkpoint_id","execution_manifest_id","outcome_id"]):
    check(f"D{i+9:02d} to_dict has {key}", key in d)
check("D15 to_dict has authorization_status",
      d["authorization_status"] == "pending")
check("D16 to_dict executes_security_actions False",
      d["executes_security_actions"] is False)

# authority_id can be set
c_auth = DecisionContract(**{**base, "authority_id": "auth-xyz"})
check("D17 authority_id set", c_auth.authority_id == "auth-xyz")

# executes_security_actions=True rejected
expect_raise("D18 executes_security_actions=True rejected",
             lambda: DecisionContract(**{**base, "executes_security_actions": True}),
             DecisionContractError)

# Invalid authorization_status type
expect_raise("D19 invalid authorization_status type",
             lambda: DecisionContract(**{**base, "authorization_status": "authorized"}),
             Exception)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
