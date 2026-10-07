#!/usr/bin/env python3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from enterpriseguard.adie.canonical.trust.authority_to_revoke import (
    RevocationAuthority, RevocationKind,
    RevocationAuthorityValidationError, RevocationNotPermittedError,
)

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

def expect(n, fn, exc):
    try: fn(); check(n, False, "did not raise")
    except exc: check(n, True)
    except Exception as e: check(n, False, f"wrong {type(e).__name__}")

print("="*72); print("RevocationAuthority"); print("="*72)
now = datetime.now(timezone.utc)

good = RevocationAuthority(
    revocation_authority_id="ra-1", revocation_authority_ref="authority:gov-1",
    permitted_kinds=frozenset({RevocationKind.REVOKE, RevocationKind.SUSPEND}),
    revocable_subject_ids=frozenset({"auth-A","auth-B"}),
    valid_from=now-timedelta(hours=1), valid_until=now+timedelta(hours=1))

check("R01 constructed", good.revocation_authority_id == "ra-1")
check("R02 active now", good.is_active(now))
check("R03 inactive before", not good.is_active(now-timedelta(hours=2)))
check("R04 inactive after", not good.is_active(now+timedelta(hours=2)))

# permits matrix
for i, (sid, kind) in enumerate([
    ("auth-A", RevocationKind.REVOKE), ("auth-A", RevocationKind.SUSPEND),
    ("auth-B", RevocationKind.REVOKE), ("auth-B", RevocationKind.SUSPEND)]):
    good.permits(sid, kind, at=now)
    check(f"R{i+5:02d} permits {sid} {kind.value}", True)

expect("R09 no SUPERSEDE", lambda: good.permits("auth-A", RevocationKind.SUPERSEDE, at=now), RevocationNotPermittedError)
expect("R10 no EXPIRE", lambda: good.permits("auth-A", RevocationKind.EXPIRE, at=now), RevocationNotPermittedError)
expect("R11 out-of-scope subject", lambda: good.permits("auth-Z", RevocationKind.REVOKE, at=now), RevocationNotPermittedError)
expect("R12 inactive at earlier time", lambda: good.permits("auth-A", RevocationKind.REVOKE, at=now-timedelta(hours=2)), RevocationNotPermittedError)
expect("R13 inactive at later time", lambda: good.permits("auth-A", RevocationKind.REVOKE, at=now+timedelta(hours=2)), RevocationNotPermittedError)

# construction validation
base = dict(revocation_authority_id="ra", revocation_authority_ref="auth:x",
            permitted_kinds=frozenset({RevocationKind.REVOKE}),
            revocable_subject_ids=frozenset({"s"}),
            valid_from=now, valid_until=now+timedelta(hours=1))

for i, f in enumerate(["revocation_authority_id","revocation_authority_ref"]):
    kw = dict(base); kw[f] = ""
    expect(f"R{i+14:02d} empty {f}", lambda k=kw: RevocationAuthority(**k), RevocationAuthorityValidationError)

kw = dict(base); kw["permitted_kinds"] = frozenset()
expect("R16 empty permitted_kinds", lambda: RevocationAuthority(**kw), RevocationAuthorityValidationError)

kw = dict(base); kw["permitted_kinds"] = frozenset({"revoke"})
expect("R17 non-RevocationKind in kinds", lambda: RevocationAuthority(**kw), RevocationAuthorityValidationError)

kw = dict(base); kw["revocable_subject_ids"] = ["a"]
expect("R18 non-frozenset subjects", lambda: RevocationAuthority(**kw), RevocationAuthorityValidationError)

kw = dict(base); kw["valid_from"] = datetime(2026,1,1)
expect("R19 naive valid_from", lambda: RevocationAuthority(**kw), RevocationAuthorityValidationError)

kw = dict(base); kw["valid_until"] = now
expect("R20 valid_until <= valid_from", lambda: RevocationAuthority(**kw), RevocationAuthorityValidationError)

try:
    good.revocation_authority_id = "x"; check("R21 frozen", False)
except Exception: check("R21 frozen", True)

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
