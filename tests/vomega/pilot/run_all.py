#!/usr/bin/env python3
"""ADIE-PILOT v0.1 — end-to-end differential suite (Phase 1.10).

Each vector:
  1. Issue a certificate (Python issue_cli)
  2. Optionally mutate
  3. Verify with Python verify_cli
  4. Verify with JS verify.mjs
  5. Assert identical stdout AND expected decision
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VECTORS = HERE / "vectors.json"

PY_ISSUE = [sys.executable, "-m", "protocol.pilot.issue_cli"]
PY_VERIFY = [sys.executable, "-m", "protocol.pilot.verify_cli"]
JS_VERIFY = ["node", str(ROOT / "protocol" / "pilot" / "verify.mjs")]

PASS_N = FAIL_N = 0
RESULTS = []


def run(cmd, payload, timeout=20):
    r = subprocess.run(cmd, input=json.dumps(payload),
                       capture_output=True, text=True,
                       cwd=str(ROOT), timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def gen_keypair():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()).decode()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return priv, pub


def apply_mutation(cert_obj, mutation):
    path = mutation["path"]
    value = mutation["value"]
    cur = cert_obj
    for p in path[:-1]:
        cur = cur[p]
    cur[path[-1]] = value


def run_vector(v, manifest_base, priv, pub):
    problems = []

    # 1. issue
    issue_payload = dict(v["issue"])
    issue_payload["manifest"] = manifest_base
    issue_payload["private_key_pem"] = priv
    rc, cert_text, err = run(PY_ISSUE, issue_payload)
    if rc != 0:
        return [f"issue failed rc={rc} err={err[:80]}"]

    cert_obj = json.loads(cert_text)

    # 2. mutate if requested
    if "mutate" in v:
        apply_mutation(cert_obj, v["mutate"])
        cert_text = json.dumps(cert_obj)

    # 3. verify with Python
    verify_payload = {
        "certificate_json": cert_text,
        "public_key_pem": pub,
    }
    if "verify" in v:
        verify_payload.update(v["verify"])
    py_rc, py_out, py_err = run(PY_VERIFY, verify_payload)
    py_res = json.loads(py_out) if py_out else {}

    # 4. verify with JS
    js_rc, js_out, js_err = run(JS_VERIFY, verify_payload)
    js_res = json.loads(js_out) if js_out else {}

    # 5. assert identical bytes
    if py_out != js_out:
        problems.append(f"py/js diverge:\n  py={py_out[:160]}\n  js={js_out[:160]}")

    # 6. assert expected decision
    expected = v["expected"]
    if expected == "VALID":
        if py_res.get("status") != "VALID":
            problems.append(f"expected VALID, got {py_res.get('status')} ({py_res.get('code')})")
    else:
        if py_res.get("status") != "INVALID":
            problems.append(f"expected INVALID, got {py_res.get('status')}")
        else:
            code = py_res.get("code")
            if "expected_code" in v:
                if code != v["expected_code"]:
                    problems.append(f"expected code {v['expected_code']}, got {code}")
            elif "expected_code_any" in v:
                if code not in v["expected_code_any"]:
                    problems.append(f"expected code in {v['expected_code_any']}, got {code}")

    return problems


def main():
    global PASS_N, FAIL_N
    data = json.loads(VECTORS.read_text())
    manifest_base = data["manifest_base"]
    vectors = data["vectors"]

    print("=" * 72)
    print(f"ADIE-PILOT v0.1 — end-to-end differential suite ({len(vectors)} vectors)")
    print("=" * 72)

    priv, pub = gen_keypair()

    for v in vectors:
        problems = run_vector(v, manifest_base, priv, pub)
        ok = not problems
        mark = "PASS" if ok else "FAIL"
        if ok:
            PASS_N += 1
        else:
            FAIL_N += 1
        RESULTS.append((v["id"], v["name"], problems))
        print(f"[{mark}] {v['id']}: {v['name']}")
        for p in problems:
            for line in p.split("\n"):
                print(f"       {line}")

    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)

    if FAIL_N:
        print("\nFailed:")
        for vid, name, problems in RESULTS:
            if problems:
                print(f"  {vid}: {name}")
                for p in problems:
                    print(f"    - {p[:120]}")

    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
