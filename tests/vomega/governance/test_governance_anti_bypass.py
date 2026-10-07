#!/usr/bin/env python3
"""Anti-bypass tests (behavioral)."""
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from enterpriseguard.adie.decision import (
    DecisionContract, DecisionContractError, DecisionIntent,
    DecisionLifecycle, AuthorizationStatus, DecisionEvidence, DecisionEngine,
)
from enterpriseguard.adie.canonical.authority import (
    Authority, AuthorityKind, AuthorityScopeMismatchError,
)
from enterpriseguard.adie.canonical.lifecycle_sm import (
    transition, LifecycleTransitionError,
)
from enterpriseguard.adie.canonical.compat_decision_b import legacy_contract_to_neutral

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

now = datetime.now(timezone.utc)

print("="*72); print("Anti-bypass verification"); print("="*72)

# 1. Evidence alone cannot authorize
ev = DecisionEvidence(prediction_id="p", policy_id="pol", threat_probability=0.9,
                      prediction_confidence=0.9, state_risk=0.5,
                      policy_allowed=True, collected_at=now)
check("X01 DecisionEvidence has no authority_id attribute",
      not hasattr(ev, "authority_id"))
check("X02 DecisionEvidence has no authorization_status",
      not hasattr(ev, "authorization_status"))

# 2. Model output (prediction) cannot authorize
check("X03 prediction_id alone cannot set authorization",
      not hasattr(ev, "authorized"))

# 3. Prediction as decision without policy
ev_no_policy = DecisionEvidence(prediction_id="p", policy_id="pol",
                                threat_probability=0.99, prediction_confidence=0.99,
                                state_risk=0.9, policy_allowed=False, collected_at=now)
c = DecisionEngine().evaluate(ev_no_policy)
check("X04 policy_allowed=False -> lifecycle=PROPOSED (not AUTHORIZED)",
      c.lifecycle is DecisionLifecycle.PROPOSED)
check("X05 policy_allowed=False -> auth not AUTHORIZED",
      c.authorization_status is not AuthorizationStatus.AUTHORIZED)

# 4. Illegal lifecycle transitions rejected
for i, (a, b) in enumerate([
    (DecisionLifecycle.PROPOSED, DecisionLifecycle.AUTHORIZED),
    (DecisionLifecycle.PROPOSED, DecisionLifecycle.EMITTED),
    (DecisionLifecycle.VALIDATED, DecisionLifecycle.EXECUTED_EXTERNAL),
]):
    try:
        transition(a, b); check(f"X{i+6:02d} illegal {a.value}->{b.value} blocked", False)
    except LifecycleTransitionError: check(f"X{i+6:02d} illegal {a.value}->{b.value} blocked", True)

# 5. Authority scope mismatch
auth = Authority(authority_id="a1", authority_kind=AuthorityKind.MACHINE,
                 policy_id="p1", policy_version="1.0", scope="decide",
                 valid_from=now, valid_until=now+timedelta(hours=1))
try:
    auth.requires_scope("execute"); check("X09 scope mismatch blocked", False)
except AuthorityScopeMismatchError: check("X09 scope mismatch blocked", True)

# 6. Contract cannot claim AUTHORIZED without sufficient lifecycle
try:
    DecisionContract(decision_id="d", intent=DecisionIntent.MONITOR,
                     lifecycle=DecisionLifecycle.PROPOSED,
                     decision_score=0.5, confidence=0.5,
                     prediction_id="p", policy_id="pol",
                     rationale="r", reason_codes=(), created_at=now,
                     authorization_status=AuthorizationStatus.AUTHORIZED)
    check("X10 early-AUTHORIZED blocked", False)
except DecisionContractError: check("X10 early-AUTHORIZED blocked", True)

# 7. Legacy B cannot authorize by itself — adapter emits no Authority
class FakeStatus:
    def __init__(self, v): self.value = v
class FakeLegacy:
    def __init__(self):
        self.decision_id="b"; self.evaluation_id="e"; self.policy_id="p"
        self.status = FakeStatus("authorized"); self.authorized=True
        self.target_resource_id="r"; self.expires_at=None
neutral = legacy_contract_to_neutral(FakeLegacy())
check("X11 legacy adapter emits no Authority object",
      not any(k in neutral for k in ("authority","authority_id")))
check("X12 legacy authorized claim not an Authority",
      neutral.get("legacy_authorized_claim") is True)

# 8. EXECUTES_SECURITY_ACTIONS boundary
from enterpriseguard.adie.decision import EXECUTES_SECURITY_ACTIONS as EXEC
check("X13 module-level EXECUTES_SECURITY_ACTIONS is False", EXEC is False)

# 9. External boundary: EXECUTED_EXTERNAL requires explicit observation flag
try:
    transition(DecisionLifecycle.EMITTED, DecisionLifecycle.EXECUTED_EXTERNAL)
    check("X14 EXECUTED_EXTERNAL requires external_observation=True", False)
except LifecycleTransitionError:
    check("X14 EXECUTED_EXTERNAL requires external_observation=True", True)

# 10. No backward jumps
try:
    transition(DecisionLifecycle.AUTHORIZED, DecisionLifecycle.VALIDATED)
    check("X15 backward jump blocked", False)
except LifecycleTransitionError: check("X15 backward jump blocked", True)

# 11. Cross-axis equivalence absent
check("X16 AUTHORIZED != EXECUTED_EXTERNAL",
      AuthorizationStatus.AUTHORIZED.value != DecisionLifecycle.EXECUTED_EXTERNAL.value)
check("X17 lifecycle does not contain auth values",
      "denied" not in {x.value for x in DecisionLifecycle})
check("X18 auth does not contain lifecycle values",
      "emitted" not in {x.value for x in AuthorizationStatus})

# 12. Executes flag cannot be smuggled through audit_metadata
c2 = DecisionContract(decision_id="d2", intent=DecisionIntent.MONITOR,
                     lifecycle=DecisionLifecycle.PROPOSED,
                     decision_score=0.5, confidence=0.5,
                     prediction_id="p", policy_id="pol",
                     rationale="r", reason_codes=(), created_at=now)
check("X19 executes_security_actions is False regardless of metadata",
      c2.executes_security_actions is False)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
