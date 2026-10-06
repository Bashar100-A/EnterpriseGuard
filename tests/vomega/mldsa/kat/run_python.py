#!/usr/bin/env python3
"""Python KAT runner: dilithium-py 1.4.0 vs NIST ACVP ML-DSA-65 pure vectors."""
import json
import sys
from pathlib import Path
from dilithium_py.ml_dsa import ML_DSA_65 as DLP

HERE = Path(__file__).resolve().parent


def h2b(h):
    return bytes.fromhex(h) if h else b""


def norm(h):
    return h.upper()


def run_keygen():
    vs = json.loads((HERE / "keygen_65.json").read_text())
    p = f = 0
    for v in vs:
        try:
            pk, sk = DLP.key_derive(h2b(v["seed_hex"]))
            if norm(pk.hex()) == norm(v["pk_hex"]) and norm(sk.hex()) == norm(v["sk_hex"]):
                p += 1
            else:
                f += 1
                print(f"  FAIL keygen tcId={v['tcId']}")
        except Exception as e:
            f += 1
            print(f"  ERR  keygen tcId={v['tcId']}: {type(e).__name__}: {str(e)[:80]}")
    return p, f


def run_siggen():
    vs = json.loads((HERE / "siggen_65.json").read_text())
    p = f = 0
    for v in vs:
        try:
            sig = DLP.sign(
                h2b(v["sk_hex"]),
                h2b(v["message_hex"]),
                ctx=h2b(v["context_hex"]),
                deterministic=True,
            )
            if norm(sig.hex()) == norm(v["signature_hex"]):
                p += 1
            else:
                f += 1
                print(f"  FAIL siggen tcId={v['tcId']}")
        except Exception as e:
            f += 1
            print(f"  ERR  siggen tcId={v['tcId']}: {type(e).__name__}: {str(e)[:80]}")
    return p, f


def run_sigver():
    vs = json.loads((HERE / "sigver_65.json").read_text())
    p = f = 0
    for v in vs:
        try:
            ok = DLP.verify(
                h2b(v["pk_hex"]),
                h2b(v["message_hex"]),
                h2b(v["signature_hex"]),
                ctx=h2b(v["context_hex"]),
            )
            if ok == v["testPassed"]:
                p += 1
            else:
                f += 1
                print(f"  FAIL sigver tcId={v['tcId']} got={ok} want={v['testPassed']}")
        except Exception as e:
            f += 1
            print(f"  ERR  sigver tcId={v['tcId']}: {type(e).__name__}: {str(e)[:80]}")
    return p, f


def main():
    print("=== Python KAT: dilithium-py 1.4.0 vs NIST ACVP ML-DSA-65 (pure) ===")
    p1, f1 = run_keygen()
    print(f"  keygen: {p1}/{p1+f1}")
    p2, f2 = run_siggen()
    print(f"  siggen: {p2}/{p2+f2}")
    p3, f3 = run_sigver()
    print(f"  sigver: {p3}/{p3+f3}")
    tp, tf = p1+p2+p3, f1+f2+f3
    print()
    print(f"TOTAL: {tp}/{tp+tf}")
    sys.exit(0 if tf == 0 else 1)


if __name__ == "__main__":
    main()
