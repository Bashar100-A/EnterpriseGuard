#!/usr/bin/env python3
"""Authority model — Evidence != Authority."""
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from enterpriseguard.adie.canonical.authority import (
    Authority, AuthorityKind,
    AuthorityValidationError, AuthorityScopeMismatchError,
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
valid = Authority(
    authority_id="auth-1", authority_kind=AuthorityKind.MACHINE,
    policy_id="pol-1", policy_version="1.0",
    scope="decide", valid_from=now, valid_until=now + timedelta(hours=1),
)

print("="*72); print("Authority model"); print("="*72)

check("A01 constructed", valid.authority_id == "auth-1")
check("A02 is_active", valid.is_active(now + timedelta(minutes=30)))
check("A03 not active before", not valid.is_active(now - timedelta(hours=1)))
check("A04 not active after", not valid.is_active(now + timedelta(hours=2)))

# Empty id rejected
for i, field in enumerate(["authority_id", "policy_id", "policy_version", "scope"]):
    kwargs = dict(authority_id="a", authority_kind=AuthorityKind.MACHINE,
                  policy_id="p", policy_version="1", scope="s",
                  valid_from=now, valid_until=now+timedelta(hours=1))
    kwargs[field] = ""
    expect_raise(f"A{i+5:02d} empty {field}", lambda kw=kwargs: Authority(**kw),
                 AuthorityValidationError)

# Bad kind
expect_raise("A09 bad kind", lambda: Authority(
    authority_id="a", authority_kind="machine",
    policy_id="p", policy_version="1", scope="s",
    valid_from=now, valid_until=now+timedelta(hours=1)),
    AuthorityValidationError)

# Naive datetime
expect_raise("A10 naive valid_from", lambda: Authority(
    authority_id="a", authority_kind=AuthorityKind.MACHINE,
    policy_id="p", policy_version="1", scope="s",
    valid_from=datetime(2026,1,1), valid_until=now+timedelta(hours=1)),
    AuthorityValidationError)

# valid_until <= valid_from
expect_raise("A11 valid_until <= valid_from", lambda: Authority(
    authority_id="a", authority_kind=AuthorityKind.MACHINE,
    policy_id="p", policy_version="1", scope="s",
    valid_from=now, valid_until=now), AuthorityValidationError)

# Scope check
valid.requires_scope("decide")  # no raise
check("A12 requires_scope matching ok", True)
expect_raise("A13 requires_scope mismatch",
             lambda: valid.requires_scope("execute"),
             AuthorityScopeMismatchError)

# Frozen
try:
    valid.authority_id = "x"; check("A14 immutable", False, "mutated")
except Exception: check("A14 immutable", True)

# Fingerprint deterministic
check("A15 fingerprint deterministic",
      valid.fingerprint() == valid.fingerprint())
check("A16 fingerprint prefix sha256:", valid.fingerprint().startswith("sha256:"))
check("A17 fingerprint length 71",
      len(valid.fingerprint()) == 71)

# Three kinds
for i, k in enumerate([AuthorityKind.MACHINE, AuthorityKind.HUMAN, AuthorityKind.DUAL]):
    check(f"A{i+18} kind {k.value}", k.value in ("machine","human","dual"))

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
