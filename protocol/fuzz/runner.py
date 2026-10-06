#!/usr/bin/env python3
"""ADIE-FUZZ v0.1 — differential runner (Phase 1.11).

For each generated input, run Python and JavaScript implementations
and compare byte-for-byte.

Usage:
  python3 -m protocol.fuzz.runner <suite> <seed> <budget>
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def py_eval_acl(expr, state):
    """Run Python ACL in-process."""
    sys.path.insert(0, str(ROOT))
    from protocol.acl.ast import ACLError
    from protocol.acl.eval import eval_checked
    from protocol.acl.normalize import canonical_bytes, canonical_ast
    try:
        verdict = eval_checked(expr, state)
        norm = canonical_bytes(canonical_ast(expr)).decode("utf-8")
        return {"verdict": verdict, "normalized": norm, "err": None}
    except ACLError as e:
        return {"verdict": None, "normalized": None, "err": e.code}


def js_eval_acl(expr, state):
    """Run JS ACL in a subprocess."""
    script = """
import {evalExpr, canonicalBytes, canonicalAst} from './protocol/acl/acl.mjs';
const input = JSON.parse(await new Response(process.stdin).text());
try {
  const v = evalExpr(input.expr, input.state);
  const n = canonicalBytes(canonicalAst(input.expr));
  console.log(JSON.stringify({verdict: v, normalized: n, err: null}));
} catch (e) {
  console.log(JSON.stringify({verdict: null, normalized: null, err: e.code || 'UNKNOWN'}));
}
"""
    r = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        input=json.dumps({"expr": expr, "state": state}),
        capture_output=True, text=True, cwd=str(ROOT), timeout=10)
    if r.returncode != 0:
        return {"verdict": None, "normalized": None, "err": "NODE_EXIT"}
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return {"verdict": None, "normalized": None, "err": "PARSE_FAIL"}


def py_claimroot(fields):
    sys.path.insert(0, str(ROOT))
    from protocol.core.claim_root import claim_root_hex
    try:
        return claim_root_hex(fields)
    except Exception as e:
        return f"ERR:{type(e).__name__}"


def js_claimroot(fields):
    script = """
import {claimRootHex} from './protocol/core/claim_root.mjs';
const input = JSON.parse(await new Response(process.stdin).text());
try {
  console.log(claimRootHex(input.fields));
} catch (e) {
  console.log('ERR:' + (e.code || e.constructor.name));
}
"""
    r = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        input=json.dumps({"fields": fields}),
        capture_output=True, text=True, cwd=str(ROOT), timeout=10)
    if r.returncode != 0:
        return "NODE_EXIT"
    return r.stdout.strip()


def suite_acl(seed, budget):
    sys.path.insert(0, str(ROOT))
    from protocol.fuzz.generator import rand_expr, rand_state
    import random
    rng = random.Random(seed)
    passed = failed = 0
    failures = []
    for i in range(budget):
        expr = rand_expr(rng, 0, 3)
        state = rand_state(rng)
        py = py_eval_acl(expr, state)
        js = js_eval_acl(expr, state)
        if py == js:
            passed += 1
        else:
            failed += 1
            failures.append({"i": i, "expr": expr, "state": state,
                             "py": py, "js": js})
    return passed, failed, failures


def suite_claimroot(seed, budget):
    sys.path.insert(0, str(ROOT))
    from protocol.fuzz.generator import rand_fields
    import random
    rng = random.Random(seed)
    passed = failed = 0
    failures = []
    for i in range(budget):
        fields = rand_fields(rng)
        py = py_claimroot(fields)
        js = js_claimroot(fields)
        if py == js:
            passed += 1
        else:
            failed += 1
            failures.append({"i": i, "fields": fields,
                             "py": py, "js": js})
    return passed, failed, failures


def py_authoring(template, params):
    sys.path.insert(0, str(ROOT))
    from protocol.fuzz.authoring_fuzz import build_manifest, MANIFEST_DICT
    from protocol.authoring.compiler import Compiler, AuthoringError
    compiler = Compiler(manifest=build_manifest(), acl_version="0.1")
    try:
        closure = compiler.compile(template, params)
        return {"kind": "ok", "closure": closure}
    except AuthoringError as e:
        return {"kind": "err", "code": e.code}
    except Exception as e:
        return {"kind": "err", "code": f"EXC:{type(e).__name__}"}


def js_authoring(template, params):
    sys.path.insert(0, str(ROOT))
    from protocol.fuzz.authoring_fuzz import MANIFEST_DICT
    payload = {
        "manifest": MANIFEST_DICT,
        "template": template,
        "params": params,
        "acl_version": "0.1",
    }
    r = subprocess.run(
        ["node", str(ROOT / "protocol" / "authoring" / "compiler.mjs")],
        input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(ROOT), timeout=10)
    if r.returncode == 0:
        try:
            closure = json.loads(r.stdout.strip())
            return {"kind": "ok", "closure": closure}
        except Exception:
            return {"kind": "err", "code": "PARSE_FAIL"}
    else:
        code = r.stderr.strip().splitlines()[0] if r.stderr.strip() else "NO_ERR"
        return {"kind": "err", "code": code}


def suite_authoring(seed, budget):
    sys.path.insert(0, str(ROOT))
    from protocol.fuzz.generator import rand_template, rand_params
    import random
    rng = random.Random(seed)
    passed = failed = 0
    failures = []
    for i in range(budget):
        template = rand_template(rng)
        params = rand_params(rng, template)
        py = py_authoring(template, params)
        js = js_authoring(template, params)
        if py == js:
            passed += 1
        else:
            failed += 1
            failures.append({"i": i, "template": template, "params": params,
                             "py": py, "js": js})
    return passed, failed, failures


SUITES = {
    "acl": suite_acl,
    "claimroot": suite_claimroot,
    "authoring": suite_authoring,
}


def main():
    if len(sys.argv) < 4:
        print("usage: runner.py <suite> <seed> <budget>")
        print("suites:", ", ".join(sorted(SUITES.keys())))
        sys.exit(2)
    suite, seed, budget = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    if suite not in SUITES:
        print(f"unknown suite: {suite}")
        print("suites:", ", ".join(sorted(SUITES.keys())))
        sys.exit(2)

    passed, failed, failures = SUITES[suite](seed, budget)

    print(f"suite={suite} seed={seed} budget={budget}")
    print(f"passed={passed} failed={failed}")
    if failures:
        print("\nFirst 3 divergences:")
        for f in failures[:3]:
            print(json.dumps(f, ensure_ascii=False)[:400])

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
