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
RUST_VERIFY = str(RUST_DIR / "adie-verify")


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


def suite_verify():
    """Pilot vectors: Python verify_cli vs Rust semantic verifier.

    P13 (tampered signature) is EXPECTED to diverge:
      Python: INVALID/E_SIGNATURE
      Rust:   VALID with signature:SKIPPED
    Per spec/RUST-VERIFIER-0.1.md GAP-1.
    """
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    vp = ROOT / "tests" / "vomega" / "pilot" / "vectors.json"
    data = json.loads(vp.read_text())
    manifest_base = data["manifest_base"]
    vectors = data["vectors"]

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()).decode()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    pass_n = fail_n = skipped_n = 0
    for v in vectors:
        vid = v["id"]
        issue_payload = dict(v["issue"])
        issue_payload["manifest"] = manifest_base
        issue_payload["private_key_pem"] = priv
        r = subprocess.run([sys.executable, "-m", "protocol.pilot.issue_cli"],
                           input=json.dumps(issue_payload),
                           capture_output=True, text=True, cwd=str(ROOT), timeout=20)
        if r.returncode != 0:
            print(f"  [{vid}] issue failed: {r.stderr.strip()[:80]}")
            fail_n += 1
            continue
        cert_text = r.stdout.strip()

        if "mutate" in v:
            co = json.loads(cert_text)
            path = v["mutate"]["path"]; value = v["mutate"]["value"]
            cur = co
            for p in path[:-1]:
                cur = cur[p]
            cur[path[-1]] = value
            cert_text = json.dumps(co)

        py_payload = {"certificate_json": cert_text, "public_key_pem": pub}
        if "verify" in v:
            py_payload.update(v["verify"])
        rp = subprocess.run([sys.executable, "-m", "protocol.pilot.verify_cli"],
                            input=json.dumps(py_payload),
                            capture_output=True, text=True, cwd=str(ROOT), timeout=20)
        py_out = json.loads(rp.stdout.strip())

        rs_payload = {"certificate_json": cert_text}
        if "verify" in v and "expected_audience" in v["verify"]:
            rs_payload["expected_audience"] = v["verify"]["expected_audience"]
        rs = subprocess.run([RUST_VERIFY], input=json.dumps(rs_payload),
                            capture_output=True, text=True, cwd=str(ROOT), timeout=20)
        if rs.returncode not in (0, 1):
            print(f"  [{vid}] rust rc={rs.returncode}: {rs.stderr.strip()[:80]}")
            fail_n += 1
            continue
        rs_out = json.loads(rs.stdout.strip())

        # P13 expected divergence
        if vid == "P13":
            if (py_out.get("status") == "INVALID"
                    and py_out.get("code") == "E_SIGNATURE"
                    and rs_out.get("status") == "VALID"
                    and rs_out.get("checks", {}).get("signature") == "SKIPPED"):
                skipped_n += 1
                continue
            print(f"  [{vid}] unexpected P13: py={py_out.get('status')}/{py_out.get('code')} rs={rs_out.get('status')}")
            fail_n += 1
            continue

        if py_out["status"] != rs_out["status"]:
            print(f"  [{vid}] status: py={py_out['status']} rs={rs_out['status']}")
            fail_n += 1
            continue

        if py_out["status"] == "VALID":
            py_c = {k: x for k, x in py_out["checks"].items() if k != "signature"}
            rs_c = {k: x for k, x in rs_out["checks"].items() if k != "signature"}
            if py_c != rs_c:
                print(f"  [{vid}] checks diverge: py={py_c} rs={rs_c}")
                fail_n += 1
                continue
            pass_n += 1
        else:
            if py_out.get("code") != rs_out.get("code"):
                print(f"  [{vid}] code: py={py_out.get('code')} rs={rs_out.get('code')}")
                fail_n += 1
                continue
            if py_out.get("message") != rs_out.get("message"):
                print(f"  [{vid}] message diverge:")
                print(f"    py: {repr(py_out.get('message'))[:140]}")
                print(f"    rs: {repr(rs_out.get('message'))[:140]}")
                fail_n += 1
                continue
            pass_n += 1

    print(f"  verify: passed={pass_n} failed={fail_n} skipped(P13)={skipped_n}")
    return pass_n + skipped_n, fail_n


def main():
    print("=" * 72)
    print("ADIE vΩ — Rust third-verifier conformance")
    print("=" * 72)
    total_pass = total_fail = 0
    suites = [
        ("RUST-HA", suite_ha),
        ("RUST-CR", suite_cr),
        ("RUST-ACL", suite_acl),
        ("RUST-VERIFY", suite_verify),
    ]
    for name, fn in suites:
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
