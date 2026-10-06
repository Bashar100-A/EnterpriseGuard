#!/usr/bin/env python3
"""ADIE vΩ — Rust third-verifier conformance (Phase 1.11).

Suites:
  RUST-HA       (20 cases)         H_A byte-equality with Python
  RUST-CR       (200 fuzzed)       ClaimRoot byte-equality with Python
  RUST-ACL      (200 fuzzed)       ACL eval + canon byte-equality with Python
"""
import json, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from protocol.core.domain_hash import H_A
from protocol.core.claim_root import claim_root_hex as py_cr
from protocol.acl.ast import ACLError
from protocol.acl.eval import eval_checked
from protocol.acl.normalize import canonical_bytes, canonical_ast
from protocol.fuzz.generator import rand_fields, rand_expr, rand_state

RUST_DIR = ROOT / "rust" / "adie-primitives" / "target" / "release"
RUST_HA = str(RUST_DIR / "adie-h-a")
RUST_CR = str(RUST_DIR / "adie-claimroot")
RUST_ACL = str(RUST_DIR / "adie-acl")


def rust_ha(tag, x):
    r = subprocess.run([RUST_HA, tag, x.hex()], capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else f"ERR:{r.stderr.strip()[:40]}"


def rust_cr(fields):
    r = subprocess.run([RUST_CR], input=json.dumps(fields), capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else f"ERR:{r.stderr.strip()[:40]}"


def rust_acl(expr, state):
    r = subprocess.run([RUST_ACL], input=json.dumps({"expr": expr, "state": state}),
                       capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        return {"verdict": None, "canon": None, "err": f"RUST_EXIT"}
    return json.loads(r.stdout.strip())


def py_acl(expr, state):
    try:
        canon = canonical_bytes(canonical_ast(expr)).decode("utf-8")
    except ACLError as e:
        return {"verdict": None, "canon": None, "err": e.code}
    try:
        v = eval_checked(expr, state)
        return {"verdict": v, "canon": canon, "err": None}
    except ACLError as e:
        return {"verdict": None, "canon": canon, "err": e.code}


def suite_ha():
    cases = [(f"tag{i}", bytes(range(i))) for i in range(20)]
    pass_n = fail_n = 0
    for tag, x in cases:
        py = "sha256:" + H_A(tag, x).hex()
        rs = rust_ha(tag, x)
        if py == rs: pass_n += 1
        else:
            fail_n += 1
            print(f"  HA diverge: tag={tag!r} len={len(x)}")
    return pass_n, fail_n


def suite_cr():
    rng = random.Random(2026)
    pass_n = fail_n = 0
    for _ in range(200):
        f = rand_fields(rng)
        if py_cr(f) == rust_cr(f): pass_n += 1
        else:
            fail_n += 1
            print(f"  CR diverge: {json.dumps(f)[:100]}")
    return pass_n, fail_n


def suite_acl():
    rng = random.Random(2026)
    pass_n = fail_n = 0
    for _ in range(200):
        e = rand_expr(rng, 0, 3)
        s = rand_state(rng)
        if py_acl(e, s) == rust_acl(e, s): pass_n += 1
        else:
            fail_n += 1
            print(f"  ACL diverge: expr={json.dumps(e)[:80]}")
    return pass_n, fail_n


def main():
    print("=" * 72)
    print("ADIE vΩ — Rust third-verifier conformance")
    print("=" * 72)
    total_pass = total_fail = 0
    for name, fn in [("RUST-HA", suite_ha), ("RUST-CR", suite_cr), ("RUST-ACL", suite_acl)]:
        p, f = fn()
        total_pass += p
        total_fail += f
        mark = "PASS" if f == 0 else "FAIL"
        print(f"[{mark}] {name}: pass={p} fail={f}")
    print("=" * 72)
    print(f"TOTAL: {total_pass + total_fail} | PASS: {total_pass} | FAIL: {total_fail}")
    print("=" * 72)
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
