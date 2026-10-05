#!/usr/bin/env python3
"""ADIE-AUTHORING v0.1 — differential conformance suite (Phase 1.8)."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VECTORS = HERE / "vectors.json"

PY_CLI = [sys.executable, "-m", "protocol.authoring.compile_cli"]
JS_CLI = ["node", str(ROOT / "protocol" / "authoring" / "compiler.mjs")]

PASS_N = FAIL_N = 0
RESULTS = []


def run(cmd, payload):
    r = subprocess.run(cmd, input=payload, capture_output=True,
                       text=True, cwd=str(ROOT), timeout=20)
    return r.stdout, r.stderr, r.returncode


def extract_code(stderr):
    lines = stderr.strip().splitlines()
    if not lines:
        return ""
    return lines[0].split(":", 1)[0].strip()


def build_payload(v, manifest_base):
    inp = dict(v["input"])
    inp.setdefault("manifest", manifest_base)
    inp.setdefault("acl_version", "0.1")
    return json.dumps(inp)


def run_vector(v, manifest_base):
    payload = build_payload(v, manifest_base)
    py_out, py_err, py_rc = run(PY_CLI, payload)
    js_out, js_err, js_rc = run(JS_CLI, payload)
    py_out2, _, _ = run(PY_CLI, payload)

    exp = v["expected"]
    problems = []

    if exp == "OK":
        if py_rc != 0:
            problems.append(f"py rc={py_rc} err={py_err[:80]!r}")
        if js_rc != 0:
            problems.append(f"js rc={js_rc} err={js_err[:80]!r}")
        if py_out != js_out:
            problems.append("py/js stdout diverge")
        if not py_out.strip():
            problems.append("py stdout empty")
        if py_out != py_out2:
            problems.append("py non-deterministic")
    else:
        py_code = extract_code(py_err)
        js_code = extract_code(js_err)
        if py_code != exp:
            problems.append(f"py code={py_code!r} expected {exp!r}")
        if js_code != exp:
            problems.append(f"js code={js_code!r} expected {exp!r}")
        if py_rc == 0:
            problems.append("py rc=0 (expected nonzero)")
        if js_rc == 0:
            problems.append("js rc=0 (expected nonzero)")

    return problems


def main():
    global PASS_N, FAIL_N
    data = json.loads(VECTORS.read_text())
    manifest_base = data["manifest_base"]
    vecs = data["vectors"]

    print("=" * 72)
    print(f"ADIE-AUTHORING v0.1 — differential suite ({len(vecs)} vectors)")
    print("=" * 72)

    for v in vecs:
        problems = run_vector(v, manifest_base)
        ok = not problems
        mark = "PASS" if ok else "FAIL"
        if ok:
            PASS_N += 1
        else:
            FAIL_N += 1
        RESULTS.append((v["id"], v["name"], problems))
        print(f"[{mark}] {v['id']}: {v['name']}")
        for p in problems:
            print(f"       {p}")

    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
