#!/usr/bin/env python3
"""Extract ML-DSA-65 pure-mode vectors from NIST ACVP JSON.

Filter: preHash == 'pure' AND externalMu == False
For sign: additionally deterministic == True.
"""
import json
from pathlib import Path

SRC = Path("/tmp/acvp-files")
DST = Path("tests/vomega/mldsa/kat")
DST.mkdir(parents=True, exist_ok=True)


def extract_keygen():
    d = json.loads((SRC / "ML-DSA-keyGen.json").read_text())
    out = []
    for tg in d["testGroups"]:
        if tg.get("parameterSet") != "ML-DSA-65":
            continue
        for t in tg.get("tests", []):
            if t.get("deferred"):
                continue
            if not all(k in t for k in ("seed", "pk", "sk")):
                continue
            out.append({
                "tcId": t["tcId"],
                "seed_hex": t["seed"],
                "pk_hex": t["pk"],
                "sk_hex": t["sk"],
            })
    (DST / "keygen_65.json").write_text(json.dumps(out, indent=2))
    print(f"✓ keygen_65.json: {len(out)} vectors (all pure)")
    return len(out)


def extract_siggen():
    d = json.loads((SRC / "ML-DSA-sigGen.json").read_text())
    out = []
    skipped = {"prehash": 0, "externalmu": 0, "randomized": 0, "missing": 0}
    for tg in d["testGroups"]:
        if tg.get("parameterSet") != "ML-DSA-65":
            continue
        if tg.get("preHash") != "pure":
            skipped["prehash"] += len(tg.get("tests", []))
            continue
        if tg.get("externalMu") is True:
            skipped["externalmu"] += len(tg.get("tests", []))
            continue
        if tg.get("deterministic") is not True:
            skipped["randomized"] += len(tg.get("tests", []))
            continue
        for t in tg.get("tests", []):
            if t.get("deferred"):
                continue
            if not all(k in t for k in ("sk", "message", "signature")):
                skipped["missing"] += 1
                continue
            out.append({
                "tcId": t["tcId"],
                "sk_hex": t["sk"],
                "message_hex": t["message"],
                "context_hex": t.get("context", ""),
                "signature_hex": t["signature"],
                "preHash": tg.get("preHash"),
                "externalMu": tg.get("externalMu", False),
                "deterministic": tg.get("deterministic"),
                "hashAlg": t.get("hashAlg"),
            })
    (DST / "siggen_65.json").write_text(json.dumps(out, indent=2))
    print(f"✓ siggen_65.json: {len(out)} vectors")
    print(f"  skipped: {skipped}")
    return len(out)


def extract_sigver():
    d = json.loads((SRC / "ML-DSA-sigVer.json").read_text())
    out = []
    skipped = {"prehash": 0, "externalmu": 0, "missing": 0}
    for tg in d["testGroups"]:
        if tg.get("parameterSet") != "ML-DSA-65":
            continue
        if tg.get("preHash") != "pure":
            skipped["prehash"] += len(tg.get("tests", []))
            continue
        if tg.get("externalMu") is True:
            skipped["externalmu"] += len(tg.get("tests", []))
            continue
        for t in tg.get("tests", []):
            if t.get("deferred"):
                continue
            if not all(k in t for k in ("pk", "message", "signature", "testPassed")):
                skipped["missing"] += 1
                continue
            out.append({
                "tcId": t["tcId"],
                "pk_hex": t["pk"],
                "message_hex": t["message"],
                "context_hex": t.get("context", ""),
                "signature_hex": t["signature"],
                "testPassed": t["testPassed"],
                "reason": t.get("reason", ""),
                "hashAlg": t.get("hashAlg"),
            })
    (DST / "sigver_65.json").write_text(json.dumps(out, indent=2))
    print(f"✓ sigver_65.json: {len(out)} vectors")
    print(f"  skipped: {skipped}")
    return len(out)


if __name__ == "__main__":
    print("=== Extraction (pure-only filter) ===")
    n1 = extract_keygen()
    n2 = extract_siggen()
    n3 = extract_sigver()
    print(f"\nTOTAL: {n1 + n2 + n3} (keygen={n1}, siggen={n2}, sigver={n3})")
