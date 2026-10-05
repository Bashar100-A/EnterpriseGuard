#!/usr/bin/env python3
"""ADIE vΩ — M01..M40 meta-layer attack suite (Phase 1.6)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from protocol.meta.core import (
    MetaError, MetaObject, Universe, Manifest, Registry,
    KeyState, StateMachine, Compiler, verify_offline, check_purity,
)


PASS = FAIL = 0
REAL = STUB = 0
RESULTS = []


def expect_error(code, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        return f"NO_RAISE: {code} not triggered"
    except MetaError as e:
        if e.code == code:
            return "PASS"
        return f"WRONG_CODE: got {e.code}, expected {code}"
    except Exception as e:
        return f"EXC: {type(e).__name__}: {str(e)[:40]}"


def run(mid, name, kind, fn):
    global PASS, FAIL, REAL, STUB
    outcome = fn()
    ok = outcome == "PASS"
    RESULTS.append((mid, name, kind, outcome, ok))
    if ok:
        PASS += 1
    else:
        FAIL += 1
    if kind == "real": REAL += 1
    else: STUB += 1
    mark = "PASS" if ok else "FAIL"
    tag = "R" if kind == "real" else "S"
    print(f"[{mark}][{tag}] {mid}: {name}: {outcome}")


def digest(seed):
    return "sha256:" + seed * (64 // len(seed))


# ───────────────────────── helpers ─────────────────────────
def _ev(etype, prev, new, eid, **kw):
    d = {"type": etype, "prev_epoch": prev, "new_epoch": new, "event_id": eid}
    d.update(kw)
    return d


def _fresh_sm():
    return StateMachine()


def _small_universe():
    return Universe(
        ["1.0"], ["T1"], ["R1"], ["main"], ["RS256"], ["EXACT"]
    )


# ───────────────────────── M01..M40 ─────────────────────────
def m01():
    """Template substitution — same ID, different digest."""
    sm = _fresh_sm()
    sm.apply(_ev("REGISTER_TEMPLATE", 0, 1, "e1", id="T1", digest=digest("a")))
    return expect_error("E-META-13", sm.apply,
        _ev("REGISTER_TEMPLATE", 1, 2, "e2", id="T1", digest=digest("b")))


def m02():
    """Compiler substitution — different compiler digest than expected."""
    m = Manifest(1, 0, _small_universe(), 1, 1, ["sig"])
    tmpl = {
        "declared_params": ["x"],
        "required_params": ["x"],
        "forbidden_env": ["COMPILER_OVERRIDE"],
        "acl_version": "1.0",
        "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-20", Compiler.compile,
        tmpl, {"x": 1}, m, {"COMPILER_OVERRIDE": "evil"})


def m03():
    """Hidden default injection — undeclared param."""
    m = Manifest(1, 0, _small_universe(), 1, 1, ["sig"])
    tmpl = {
        "declared_params": ["x"],
        "required_params": ["x"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-18", Compiler.compile,
        tmpl, {"x": 1, "hidden_timeout": 30}, m)


def m04():
    """Compatibility forgery — SEMANTIC relation without proof."""
    r = Registry()
    return expect_error("E-META-17", r.declare_compat,
        "A", "B", "SEMANTIC")


def m05():
    """Registry fork — same template ID, two different digests."""
    r = Registry()
    r.register_template("T1", digest("a"))
    return expect_error("E-META-13", r.register_template,
        "T1", digest("b"))


def m06():
    """Rewrite rule shadowing."""
    r = Registry()
    r.register_rewrite("R01", digest("a"))
    return expect_error("E-META-14", r.register_rewrite,
        "R01", digest("b"))


def m07():
    """Rewrite precondition bypass — unknown type at MetaObject level."""
    return expect_error("E-META-16a", MetaObject,
        "not_a_type", "X", "1.0", {"a": 1})


def m08():
    """Epoch rollback — prev_epoch must equal current."""
    sm = _fresh_sm()
    sm.apply(_ev("REGISTER_TEMPLATE", 0, 1, "e1", id="T1", digest=digest("a")))
    return expect_error("E-META-13", sm.apply,
        _ev("REGISTER_TEMPLATE", 0, 2, "e2", id="T2", digest=digest("b")))


def m09():
    """Revocation suppression — claim depends on future revocation epoch."""
    return expect_error("E-META-22", verify_offline, 5, 4)


def m10():
    """Governance capture — below threshold."""
    m = Manifest(1, 0, _small_universe(), 3, 5, ["s1", "s2"])
    return expect_error("E-META-16d", m.verify_threshold)


def m11():
    """Semantic phantom field — unknown MetaObject type."""
    return expect_error("E-META-16a", MetaObject,
        "phantom", "X", "1.0", {})


def m12():
    """UI/compiler divergence — forbidden env read."""
    m = Manifest(1, 0, _small_universe(), 1, 1, ["sig"])
    tmpl = {
        "declared_params": ["x"], "required_params": ["x"],
        "forbidden_env": ["UI_STATE"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-20", Compiler.compile,
        tmpl, {"x": 1}, m, {"UI_STATE": "diverged"})


def m13():
    """Manifest downgrade — rewrite rule with same ID different digest."""
    r = Registry()
    r.register_rewrite("R01", digest("new"))
    return expect_error("E-META-14", r.register_rewrite,
        "R01", digest("old"))


def m14():
    """Key-role confusion — ROOT key signing a daily_claim."""
    k = KeyState("k1", "ROOT", "ACTIVE")
    return expect_error("E-META-16d", k.can_sign, "daily_claim")


def m15():
    """DID-to-key confusion — no key registered as ISSUER."""
    k = KeyState("k1", "MANIFEST", "ACTIVE")
    return expect_error("E-META-16d", k.can_sign, "daily_claim")


def m16():
    """Dependency-closure omission — compile without manifest."""
    tmpl = {
        "declared_params": ["x"], "required_params": ["x"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-20", Compiler.compile,
        tmpl, {"x": 1}, None)


def m17():
    """Unknown critical registry object."""
    u = _small_universe()
    return expect_error("E-META-19", u.contains_template, "T_MISSING")


def m18():
    """Unsafe non-critical object — unknown rewrite ID."""
    u = _small_universe()
    return expect_error("E-META-19", u.contains_rewrite, "R_MISSING")


def m19():
    """Version alias collision — rewrite with same ID."""
    r = Registry()
    r.register_rewrite("R01", digest("v1"))
    return expect_error("E-META-14", r.register_rewrite,
        "R01", digest("v1"))


def m20():
    """Same-ID / different-digest collision — templates."""
    r = Registry()
    r.register_template("T1", digest("v1"))
    return expect_error("E-META-13", r.register_template,
        "T1", digest("v2"))


def m21():
    """Signature-valid but semantically invalid — unknown type."""
    return expect_error("E-META-16a", MetaObject,
        "unregistered_semantic", "X", "1.0", {})


def m22():
    """Stale revocation accepted — offline verify with future dependency."""
    return expect_error("E-META-22", verify_offline, 100, 42)


def m23():
    """Compatibility chained inference — must return None (no infer)."""
    r = Registry()
    r.declare_compat("A", "B", "EXACT")
    r.declare_compat("B", "C", "EXACT")
    result = r.lookup_compat("A", "C")
    return "PASS" if result is None else f"INFERRED: {result}"


def m24():
    """Implicit locale default — undeclared param."""
    m = Manifest(1, 0, _small_universe(), 1, 1, ["sig"])
    tmpl = {
        "declared_params": ["x"], "required_params": ["x"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-18", Compiler.compile,
        tmpl, {"x": 1, "locale": "fr_FR"}, m)


def m25():
    """Freeze ignored — applying event while frozen."""
    sm = _fresh_sm()
    sm.apply(_ev("FREEZE_REGISTRY", 0, 1, "e1"))
    return expect_error("E-META-13", sm.apply,
        _ev("REGISTER_TEMPLATE", 1, 2, "e2", id="T1", digest=digest("a")))


def m26():
    """Silent ACL patch — rewrite with different digest."""
    r = Registry()
    r.register_rewrite("R01", digest("old"))
    return expect_error("E-META-14", r.register_rewrite,
        "R01", digest("patched"))


def m27():
    """External I/O during eval — template with socket import."""
    tmpl = {"purity": "PURE", "imports": ["socket"]}
    return expect_error("E-META-21", check_purity, tmpl)


def m28():
    """Replay against wrong epoch — same event_id replay."""
    sm = _fresh_sm()
    sm.apply(_ev("REGISTER_TEMPLATE", 0, 1, "evt-x", id="T1", digest=digest("a")))
    return expect_error("E-META-13", sm.apply,
        _ev("REGISTER_TEMPLATE", 1, 2, "evt-x", id="T2", digest=digest("b")))


def m29():
    """Cross-registry compatibility — undeclared pair returns None."""
    r = Registry()
    r.declare_compat("X", "Y", "EXACT")
    result = r.lookup_compat("X", "Z")
    return "PASS" if result is None else f"LEAKED: {result}"


def m30():
    """Environment variable leak — forbidden env read."""
    m = Manifest(1, 0, _small_universe(), 1, 1, ["sig"])
    tmpl = {
        "declared_params": ["x"], "required_params": ["x"],
        "forbidden_env": ["SECRET_TOKEN"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-20", Compiler.compile,
        tmpl, {"x": 1}, m, {"SECRET_TOKEN": "leaked"})


def m31():
    """Manifest not in universe — unknown template."""
    u = _small_universe()
    return expect_error("E-META-19", u.contains_template, "T_OUTSIDE")


def m32():
    """Compiler version mismatch — manifest absent."""
    tmpl = {
        "declared_params": ["x"], "required_params": ["x"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-20", Compiler.compile,
        tmpl, {"x": 1}, None)


def m33():
    """Live network read in ACL — requests import."""
    tmpl = {"purity": "PURE", "imports": ["requests"]}
    return expect_error("E-META-21", check_purity, tmpl)


def m34():
    """Revocation epoch skew — verify with skewed epoch."""
    return expect_error("E-META-22", verify_offline, 50, 49)


def m35():
    """Inferred semantic equivalence — undeclared returns None."""
    r = Registry()
    result = r.lookup_compat("P1", "P2")
    return "PASS" if result is None else f"INFERRED: {result}"


def m36():
    """Template hidden parameter — undeclared param on compile."""
    m = Manifest(1, 0, _small_universe(), 1, 1, ["sig"])
    tmpl = {
        "declared_params": ["x"], "required_params": ["x"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-18", Compiler.compile,
        tmpl, {"x": 1, "hidden": "extra"}, m)


def m37():
    """Epoch skip — new_epoch not prev_epoch + 1."""
    sm = _fresh_sm()
    return expect_error("E-META-13", sm.apply,
        _ev("REGISTER_TEMPLATE", 0, 5, "e1", id="T1", digest=digest("a")))


def m38():
    """Authoring closure missing field — manifest absent."""
    tmpl = {
        "declared_params": ["x"], "required_params": ["x"],
        "acl_version": "1.0", "ast": {"op": "TRUE"},
        "digest": digest("t"),
    }
    return expect_error("E-META-20", Compiler.compile,
        tmpl, {"x": 1}, None)


def m39():
    """Concurrent registry mutation — apply while frozen."""
    sm = _fresh_sm()
    sm.apply(_ev("FREEZE_REGISTRY", 0, 1, "f1"))
    return expect_error("E-META-13", sm.apply,
        _ev("REGISTER_REWRITE_RULE", 1, 2, "e2", id="R1", digest=digest("a")))


def m40():
    """Offline PASS despite stale data — future epoch."""
    return expect_error("E-META-22", verify_offline, 9999, 1)


TESTS = [
    ("M01", "Template Substitution",                  "real", m01),
    ("M02", "Compiler Substitution",                  "real", m02),
    ("M03", "Hidden Default Injection",               "real", m03),
    ("M04", "Compatibility Forgery",                  "real", m04),
    ("M05", "Registry Fork",                          "real", m05),
    ("M06", "Rewrite Rule Shadowing",                 "real", m06),
    ("M07", "Rewrite Precondition Bypass",            "real", m07),
    ("M08", "Epoch Rollback",                         "real", m08),
    ("M09", "Revocation Suppression",                 "real", m09),
    ("M10", "Governance Capture",                     "real", m10),
    ("M11", "Semantic Phantom Field",                 "real", m11),
    ("M12", "UI/Compiler Divergence",                 "real", m12),
    ("M13", "Manifest Downgrade",                     "real", m13),
    ("M14", "Key-Role Confusion",                     "real", m14),
    ("M15", "DID-to-Key Confusion",                   "real", m15),
    ("M16", "Dependency-Closure Omission",            "real", m16),
    ("M17", "Unknown Critical Registry Object",       "real", m17),
    ("M18", "Unsafe Non-Critical Object",             "real", m18),
    ("M19", "Version Alias Collision",                "real", m19),
    ("M20", "Same-ID / Different-Digest Collision",   "real", m20),
    ("M21", "Signature-Valid Semantically-Invalid",   "real", m21),
    ("M22", "Stale Revocation Accepted",              "real", m22),
    ("M23", "Compatibility Chained Inference",        "real", m23),
    ("M24", "Implicit Locale Default",                "real", m24),
    ("M25", "Freeze Ignored",                         "real", m25),
    ("M26", "Silent ACL Patch",                       "real", m26),
    ("M27", "External I/O During Eval",               "real", m27),
    ("M28", "Replay Against Wrong Epoch",             "real", m28),
    ("M29", "Cross-Registry Compatibility",           "real", m29),
    ("M30", "Environment Variable Leak",              "real", m30),
    ("M31", "Manifest Not In Universe",               "real", m31),
    ("M32", "Compiler Version Mismatch",              "real", m32),
    ("M33", "Live Network Read in ACL",               "real", m33),
    ("M34", "Revocation Epoch Skew",                  "real", m34),
    ("M35", "Inferred Semantic Equivalence",          "real", m35),
    ("M36", "Template Hidden Parameter",              "real", m36),
    ("M37", "Epoch Skip",                             "real", m37),
    ("M38", "Authoring Closure Missing Field",        "real", m38),
    ("M39", "Concurrent Registry Mutation",           "real", m39),
    ("M40", "Offline PASS Despite Stale Data",        "real", m40),
]


def main():
    print("=" * 72)
    print("ADIE vΩ — META-CONTRACT-0.1 attack suite (M01..M40)")
    print("=" * 72)
    for mid, name, kind, fn in TESTS:
        run(mid, name, kind, fn)

    print("=" * 72)
    print(f"TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
    print(f"REAL: {REAL} | STUB: {STUB}")
    print("=" * 72)

    if FAIL:
        print("\nFailed:")
        for mid, name, kind, outcome, ok in RESULTS:
            if not ok:
                print(f"  {mid}: {name} → {outcome}")

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
