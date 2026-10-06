#!/usr/bin/env python3
"""Rust KAT runner: RustCrypto ml-dsa 0.1.1 vs NIST ACVP ML-DSA-65 pure vectors.

Delegates each vector to the adie-mldsa Rust binary via stdin JSON.
Also cross-checks against Python for byte-equality.
"""
import json
import subprocess
import sys
from pathlib import Path
from dilithium_py.ml_dsa import ML_DSA_65 as DLP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BIN = ROOT / "rust" / "adie-primitives" / "target" / "release" / "adie-mldsa"


def rust_call(payload):
    r = subprocess.run([str(BIN)], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"rc={r.returncode}: {r.stderr[:120]}")
    return json.loads(r.stdout)


def norm(h):
    return h.upper() if h else ""


def run_keygen():
    vs = json.loads((HERE / "keygen_65.json").read_text())
    p = f = cross_ok = 0
    for v in vs:
        try:
            out = rust_call({"op": "keygen", "seed_hex": v["seed_hex"]})
            rust_pk = out["public_key_hex"]
            if norm(rust_pk) == norm(v["pk_hex"]):
                p += 1
                # cross-check against Python
                pk_py, _ = DLP.key_derive(bytes.fromhex(v["seed_hex"]))
                if norm(pk_py.hex()) == norm(rust_pk):
                    cross_ok += 1
            else:
                f += 1
                print(f"  FAIL keygen tcId={v['tcId']} (rust pk first32: {rust_pk[:64]}, expected: {v['pk_hex'][:64]})")
        except Exception as e:
            f += 1
            print(f"  ERR  keygen tcId={v['tcId']}: {type(e).__name__}: {str(e)[:100]}")
    print(f"  keygen: {p}/{p+f} (cross-python: {cross_ok}/{p})")
    return p, f


def run_siggen():
    vs = json.loads((HERE / "siggen_65.json").read_text())
    p = f = cross_ok = 0
    for v in vs:
        try:
            out = rust_call({
                "op": "sign",
                "seed_hex": None,   # not used; we pass sk via seed-equivalent reconstruction
                "msg_hex": v["message_hex"],
                "ctx_hex": v["context_hex"],
                # For Rust we only have seed-based API, not raw-sk API.
                # We need to use verify_with_ctx instead, since ACVP siggen gives raw sk.
                # Alternative: reconstruct seed from sk? Not possible.
                # So we verify the given signature via Rust's verify_with_ctx.
            })
        except Exception:
            pass
        # Sign path is not supported: ACVP gives sk (4032B), Rust API takes seed (32B).
        # We use the verify path instead for cross-check.
        p += 0
        f += 0
    return p, f


def run_sigver():
    vs = json.loads((HERE / "sigver_65.json").read_text())
    p = f = cross_ok = 0
    for v in vs:
        try:
            out = rust_call({
                "op": "verify",
                "public_key_hex": v["pk_hex"],
                "msg_hex": v["message_hex"],
                "ctx_hex": v["context_hex"],
                "signature_hex": v["signature_hex"],
            })
            rust_ok = bool(out["valid"])
            if rust_ok == v["testPassed"]:
                p += 1
                py_ok = DLP.verify(
                    bytes.fromhex(v["pk_hex"]),
                    bytes.fromhex(v["message_hex"]),
                    bytes.fromhex(v["signature_hex"]),
                    ctx=bytes.fromhex(v["context_hex"]) if v["context_hex"] else b"",
                )
                if py_ok == rust_ok:
                    cross_ok += 1
            else:
                f += 1
                print(f"  FAIL sigver tcId={v['tcId']} rust={rust_ok} want={v['testPassed']}")
        except Exception as e:
            f += 1
            print(f"  ERR  sigver tcId={v['tcId']}: {type(e).__name__}: {str(e)[:100]}")
    print(f"  sigver: {p}/{p+f} (cross-python: {cross_ok}/{p})")
    return p, f


def run_siggen_via_verify():
    """Alternative sigGen check: for each ACVP sigGen vector, verify the
    ACVP signature with Rust. Confirms Rust can parse and verify the
    same signature bytes that Python produced."""
    vs = json.loads((HERE / "siggen_65.json").read_text())
    # We have sk, message, signature. We can't derive pk from sk with our API.
    # But the ACVP sigVer file may include the same pk. Instead, derive pk
    # from sk using Python (key_derive does not work on raw sk either).
    # The cleanest path: verify via Python, cross-check with Rust verify.
    # We need pk. Since we don't have it in sigGen vectors, skip.
    return 0, 0


def main():
    print("=== Rust KAT: RustCrypto ml-dsa 0.1.1 vs NIST ACVP ML-DSA-65 (pure) ===")
    print("(keyGen uses seed; sigVer uses pk+msg+sig+ctx)")
    print()
    p1, f1 = run_keygen()
    p3, f3 = run_sigver()
    tp, tf = p1 + p3, f1 + f3
    print()
    print(f"TOTAL: {tp}/{tp+tf}")
    if tf:
        sys.exit(1)


if __name__ == "__main__":
    main()
