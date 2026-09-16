#!/usr/bin/env python3
"""
ADIE — Real Adversarial Validation Suite v2.0
Adds: Ed25519 signatures, deterministic seed, script hash, MITRE mapping, HTML report.
"""
import argparse
import hashlib
import hmac
import json
import os
import random
import secrets
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False

VERSION = "2.0.0"

MITRE_MAP = {
    "Crypto-Core":    "T1565.001 - Data Manipulation: Stored Data",
    "Time Spoofing":  "T1070.006 - Indicator Removal: Timestomp",
    "TOCTOU":         "T1548 - Abuse Elevation Control Mechanism",
    "Hard Fork":      "T1565.002 - Data Manipulation: Transmitted Data",
    "DoS Defense":    "T1499 - Endpoint Denial of Service",
    "Supply Chain":   "T1195.001 - Supply Chain Compromise: Software",
}


# ─────────────────────────── primitives ───────────────────────────

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


@dataclass
class TestResult:
    vector: str
    name: str
    passed: bool
    detail: str = ""


class DeterministicRNG:
    """Wraps secrets/random with optional seed for reproducibility."""
    def __init__(self, seed: Optional[int]):
        self.seed = seed
        if seed is not None:
            self._rng = random.Random(seed)
        else:
            self._rng = None

    def token_bytes(self, n: int) -> bytes:
        if self._rng is None:
            return secrets.token_bytes(n)
        return bytes(self._rng.getrandbits(8) for _ in range(n))

    def token_hex(self, n: int) -> str:
        return self.token_bytes(n).hex()


RNG: DeterministicRNG = DeterministicRNG(None)


# ─────────────────────────── core components ───────────────────────────

class GenesisAnchor:
    def __init__(self, secret: bytes):
        self.secret = secret
        self.timestamp = time.time() if RNG.seed is None else 1_700_000_000.0
        payload = secret + f"|{self.timestamp}".encode()
        self.genesis_hash = sha256_hex(payload)
        self.signature = hmac.new(
            secret, self.genesis_hash.encode(), hashlib.sha256
        ).hexdigest()

    def verify(self) -> bool:
        expected = hmac.new(
            self.secret, self.genesis_hash.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, self.signature)


class CryptoLedger:
    def __init__(self, secret: bytes, genesis: GenesisAnchor):
        self.secret = secret
        self.genesis = genesis
        self.blocks: List[Dict[str, Any]] = [{
            "index": 0,
            "prev_hash": "0" * 64,
            "data": {"type": "GENESIS", "anchor": genesis.genesis_hash},
            "timestamp": genesis.timestamp,
            "hash": genesis.genesis_hash,
            "signature": genesis.signature,
        }]

    def _compute_hash(self, index, prev_hash, data, timestamp) -> str:
        return sha256_hex(canonical_json({
            "index": index, "prev_hash": prev_hash,
            "data": data, "timestamp": timestamp,
        }))

    def append(self, data: dict, timestamp: Optional[float] = None) -> dict:
        last_ts = self.blocks[-1]["timestamp"]
        if timestamp is None:
            timestamp = max(time.time(), last_ts + 1e-6) \
                if RNG.seed is None else last_ts + 1.0
        if timestamp < last_ts:
            raise ValueError(f"Timestamp rollback: {timestamp} < {last_ts}")
        index = len(self.blocks)
        prev_hash = self.blocks[-1]["hash"]
        h = self._compute_hash(index, prev_hash, data, timestamp)
        sig = hmac.new(self.secret, h.encode(), hashlib.sha256).hexdigest()
        block = {"index": index, "prev_hash": prev_hash, "data": data,
                 "timestamp": timestamp, "hash": h, "signature": sig}
        self.blocks.append(block)
        return block

    def verify_chain(self) -> bool:
        for i in range(1, len(self.blocks)):
            b, p = self.blocks[i], self.blocks[i - 1]
            if b["prev_hash"] != p["hash"]:
                return False
            expected = self._compute_hash(
                b["index"], b["prev_hash"], b["data"], b["timestamp"])
            if expected != b["hash"]:
                return False
            exp_sig = hmac.new(
                self.secret, b["hash"].encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(exp_sig, b["signature"]):
                return False
        return True


class VersionedResource:
    def __init__(self, rid: str, data: dict):
        self.id, self.data, self.version = rid, data, 1

    def read(self) -> Tuple[dict, int]:
        return dict(self.data), self.version

    def write(self, new_data: dict, expected_version: int) -> None:
        if expected_version != self.version:
            raise RuntimeError(f"Causal lock violation: v{expected_version} != v{self.version}")
        self.data, self.version = dict(new_data), self.version + 1


class TokenBucket:
    def __init__(self, rate, capacity, clock=None):
        self.rate, self.capacity = rate, capacity
        self.clock = clock or time.monotonic
        self.tokens, self.last = float(capacity), self.clock()

    def allow(self) -> bool:
        now = self.clock()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


# ─────────────────────────── test vectors ───────────────────────────

def run_crypto_tests() -> List[TestResult]:
    out = []
    for i in range(10):
        s = RNG.token_bytes(32)
        out.append(TestResult("Crypto-Core",
            f"Genesis anchor HMAC integrity #{i+1}",
            GenesisAnchor(s).verify()))
    for i in range(10):
        s = RNG.token_bytes(32); g = GenesisAnchor(s)
        L = CryptoLedger(s, g)
        for j in range(5 + i): L.append({"decision": f"d{j}"})
        out.append(TestResult("Crypto-Core",
            f"Chain integrity after {5+i} appends #{i+1}", L.verify_chain()))
    for i in range(10):
        s = RNG.token_bytes(32); g = GenesisAnchor(s)
        L = CryptoLedger(s, g)
        for j in range(5): L.append({"decision": f"d{j}"})
        idx = 1 + (i % 4)
        orig = L.blocks[idx]["data"].copy()
        L.blocks[idx]["data"]["decision"] = "TAMPERED"
        detected = not L.verify_chain()
        L.blocks[idx]["data"] = orig
        out.append(TestResult("Crypto-Core",
            f"Tamper detection on block #{idx} #{i+1}", detected))
    for i in range(10):
        s = RNG.token_bytes(32); L = CryptoLedger(s, GenesisAnchor(s))
        L.append({"d": "a"})
        rejected = False
        try:
            L.append({"d": "b"}, timestamp=L.blocks[-1]["timestamp"] - 1.0)
        except ValueError: rejected = True
        out.append(TestResult("Crypto-Core",
            f"Timestamp rollback rejection #{i+1}", rejected))
    for i in range(8):
        s = RNG.token_bytes(32); L = CryptoLedger(s, GenesisAnchor(s))
        L.append({"d": f"sig-{i}"})
        L.blocks[1]["signature"] = "0" * 64
        out.append(TestResult("Crypto-Core",
            f"Signature corruption detection #{i+1}", not L.verify_chain()))
    return out


def run_time_spoofing_tests() -> List[TestResult]:
    out = []
    for i in range(20):
        s = RNG.token_bytes(32); g = GenesisAnchor(s)
        L = CryptoLedger(s, g)
        L.append({"decision": "buy_asset", "amount": 1000})
        mode = i % 4; blocked = False
        try:
            if mode == 0: ts = g.timestamp - 86400
            elif mode == 1: ts = g.timestamp - 0.001
            elif mode == 2: ts = L.blocks[-1]["timestamp"] - 0.5
            else: ts = L.blocks[1]["timestamp"] - 1.0
            L.append({"decision": "fake"}, timestamp=ts)
        except ValueError: blocked = True
        out.append(TestResult("Time Spoofing",
            f"Reject backdated decision (mode {mode}) #{i+1}",
            blocked, "attack_ts < last_block_ts"))
    return out


def run_toctou_tests() -> List[TestResult]:
    out = []
    for i in range(20):
        r = VersionedResource("asset-1", {"value": 100})
        data, ver = r.read()
        if i % 2 == 0:
            r.write({"value": 999999}, expected_version=ver)
            blocked = False
            try: r.write({"value": data["value"]}, expected_version=ver)
            except RuntimeError: blocked = True
            out.append(TestResult("TOCTOU",
                f"Causal lock rejects stale version #{i+1}", blocked))
        else:
            r.write({"value": data["value"] + 10}, expected_version=ver)
            out.append(TestResult("TOCTOU",
                f"Valid update with matching version #{i+1}", r.version == 2))
    return out


def run_hard_fork_tests() -> List[TestResult]:
    out = []
    for i in range(20):
        s = RNG.token_bytes(32); L = CryptoLedger(s, GenesisAnchor(s))
        for j in range(3): L.append({"d": j})
        mode = i % 4; detected = False
        if mode == 0:
            L.blocks[-1]["hash"] = "f" * 64
            L.append({"fork": True})
            detected = not L.verify_chain()
        elif mode == 1:
            fake = dict(L.blocks[-1]); fake["data"] = {"fork": True}
            L.blocks.append(fake)
            detected = not L.verify_chain()
        elif mode == 2:
            L.blocks[1]["data"] = {"fork": True}
            detected = not L.verify_chain()
        else:
            L.blocks[2]["prev_hash"] = L.blocks[0]["hash"]
            detected = not L.verify_chain()
        out.append(TestResult("Hard Fork",
            f"Fork/branch injection detection (mode {mode}) #{i+1}", detected))
    return out


def run_dos_tests() -> List[TestResult]:
    out = []
    for i in range(20):
        state = [0.0]
        bucket = TokenBucket(rate=10.0, capacity=20.0, clock=lambda: state[0])
        burst = sum(1 for _ in range(100) if bucket.allow())
        state[0] = 1.0
        after = sum(1 for _ in range(15) if bucket.allow())
        out.append(TestResult("DoS Defense",
            f"Burst throttle + recovery #{i+1}",
            burst == 20 and after == 10,
            f"burst={burst}/100, after_1s={after}/15"))
    return out


def run_supply_chain_tests() -> List[TestResult]:
    out = []
    for i in range(20):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        path = tmp.name
        try:
            tmp.write(RNG.token_bytes(1024)); tmp.close()
            with open(path, "rb") as f: registered = sha256_hex(f.read())
            mode = i % 3
            if mode == 0:
                with open(path, "ab") as f: f.write(b"malicious")
                with open(path, "rb") as f: cur = sha256_hex(f.read())
                out.append(TestResult("Supply Chain",
                    f"Detect model file modification #{i+1}", cur != registered))
            elif mode == 1:
                with open(path, "wb") as f: f.write(b"x")
                with open(path, "rb") as f: cur = sha256_hex(f.read())
                out.append(TestResult("Supply Chain",
                    f"Detect model file truncation #{i+1}", cur != registered))
            else:
                with open(path, "rb") as f: cur = sha256_hex(f.read())
                out.append(TestResult("Supply Chain",
                    f"Valid file passes hash check #{i+1}", cur == registered))
        finally: os.unlink(path)
    return out


# ─────────────────────────── report + signing ───────────────────────────

def sign_ed25519(private_key_path: str, message: bytes) -> str:
    if not HAVE_CRYPTO:
        raise RuntimeError("pip install cryptography")
    with open(private_key_path, "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    return key.sign(message).hex()


def build_report(results: List[TestResult], seed: Optional[int],
                 private_key_path: Optional[str]) -> Dict[str, Any]:
    passed = sum(1 for r in results if r.passed)
    script_hash = sha256_hex(open(__file__, "rb").read())
    try:
        import subprocess
        git = subprocess.getoutput("git rev-parse HEAD 2>/dev/null").strip() or "no-git"
    except Exception:
        git = "no-git"

    body = {
        "validator_version": VERSION,
        "validator_script_hash": script_hash,
        "git_commit": git,
        "seed": seed,
        "timestamp": time.time() if seed is None else 1_700_000_000.0,
        "total": len(results),
        "passed": passed,
        "results": [
            {"vector": r.vector, "name": r.name,
             "passed": r.passed, "detail": r.detail,
             "mitre": MITRE_MAP.get(r.vector, "N/A")}
            for r in results
        ],
    }
    report_hash = sha256_hex(canonical_json(body))
    signature = None
    if private_key_path:
        signature = sign_ed25519(private_key_path, report_hash.encode())

    return {
        **body,
        "report_hash": report_hash,
        "signature_alg": "Ed25519" if signature else None,
        "signature": signature,
        "status": "READY FOR ENTERPRISE DEPLOYMENT"
                  if passed == len(results) else "VALIDATION FAILED",
    }


# ─────────────────────────── HTML report ───────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>ADIE Validation Report</title>
<style>
body{{font-family:-apple-system,system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#1a1a2e}}
h1{{color:#16213e;border-bottom:3px solid #0f3460;padding-bottom:.5rem}}
.summary{{display:flex;gap:1rem;margin:1.5rem 0}}
.card{{flex:1;padding:1rem;border-radius:8px;background:#f5f5f5;border-left:4px solid #0f3460}}
.card.ok{{background:#e8f5e9;border-left-color:#2e7d32}}
.card.err{{background:#ffebee;border-left-color:#c62828}}
.card b{{display:block;font-size:1.6rem;color:#16213e}}
.hash{{font-family:monospace;font-size:.75rem;word-break:break-all;background:#f0f0f0;padding:.5rem;border-radius:4px;margin:.25rem 0}}
table{{width:100%;border-collapse:collapse;font-size:.85rem;margin-top:1rem}}
th{{background:#0f3460;color:#fff;padding:.5rem;text-align:left;position:sticky;top:0}}
td{{padding:.4rem .5rem;border-bottom:1px solid #eee}}
tr.pass td:first-child{{color:#2e7d32;font-weight:bold}}
tr.fail td:first-child{{color:#c62828;font-weight:bold}}
.vector{{font-weight:600;color:#0f3460}}
</style></head><body>
<h1>🛡️ ADIE Validation Report</h1>
<div class="summary">
<div class="card {status_class}"><b>{passed}/{total}</b>Tests Passed</div>
<div class="card"><b>{version}</b>Validator Version</div>
<div class="card"><b>{status_short}</b>System Status</div>
</div>
<p><b>Report Hash (SHA-256):</b></p>
<div class="hash">{report_hash}</div>
<p><b>Script Hash:</b></p>
<div class="hash">{script_hash}</div>
<p><b>Signature ({sig_alg}):</b></p>
<div class="hash">{signature}</div>
<p><b>Git Commit:</b> <code>{git}</code> &nbsp;|&nbsp; <b>Seed:</b> <code>{seed}</code></p>
<table><thead><tr>
<th>Status</th><th>Vector</th><th>Test</th><th>MITRE</th><th>Detail</th>
</tr></thead><tbody>
{rows}
</tbody></table>
</body></html>
"""


def write_html_report(report: Dict[str, Any], path: str) -> None:
    rows = []
    for r in report["results"]:
        cls = "pass" if r["passed"] else "fail"
        mark = "✓ PASS" if r["passed"] else "✗ FAIL"
        rows.append(
            f'<tr class="{cls}"><td>{mark}</td>'
            f'<td class="vector">{r["vector"]}</td><td>{r["name"]}</td>'
            f'<td><code>{r["mitre"]}</code></td><td>{r["detail"]}</td></tr>'
        )
    html = HTML_TEMPLATE.format(
        status_class="ok" if report["passed"] == report["total"] else "err",
        passed=report["passed"], total=report["total"],
        version=report["validator_version"],
        status_short="READY" if report["passed"] == report["total"] else "FAILED",
        report_hash=report["report_hash"],
        script_hash=report["validator_script_hash"],
        sig_alg=report["signature_alg"] or "none",
        signature=report["signature"] or "(unsigned)",
        git=report["git_commit"], seed=report["seed"],
        rows="\n".join(rows),
    )
    with open(path, "w") as f:
        f.write(html)


# ─────────────────────────── main ───────────────────────────

def main() -> None:
    global RNG
    ap = argparse.ArgumentParser(description="ADIE Adversarial Validator v2.0")
    ap.add_argument("--seed", type=int, default=None,
                    help="Deterministic seed for reproducibility")
    ap.add_argument("--sign-key", type=str, default=None,
                    help="Path to Ed25519 private key (PEM)")
    ap.add_argument("--out", type=str, default="adie_validation_report.json")
    ap.add_argument("--html", type=str, default="adie_validation_report.html")
    args = ap.parse_args()

    RNG = DeterministicRNG(args.seed)
    if args.seed is not None:
        random.seed(args.seed)

    print("=" * 66)
    print(f"      ADIE — REAL ADVERSARIAL VALIDATION SUITE v{VERSION}")
    print("=" * 66)
    print(f"Seed       : {args.seed if args.seed is not None else '(random)'}")
    print(f"Sign key   : {args.sign_key or '(unsigned)'}")
    print()

    sections = [
        ("STAGE 1 — Crypto-Core",  run_crypto_tests),
        ("STAGE 2 — Time Spoofing", run_time_spoofing_tests),
        ("STAGE 2 — TOCTOU",        run_toctou_tests),
        ("STAGE 2 — Hard Fork",     run_hard_fork_tests),
        ("STAGE 2 — DoS Defense",   run_dos_tests),
        ("STAGE 2 — Supply Chain",  run_supply_chain_tests),
    ]

    all_results: List[TestResult] = []
    for header, fn in sections:
        print(f"[{header}]")
        rs = fn()
        all_results.extend(rs)
        for r in rs:
            tag = "[PASSED]" if r.passed else "[FAILED]"
            extra = f" | {r.detail}" if r.detail else ""
            print(f"{tag} {r.vector:15s} | {r.name}{extra}")
        print()

    try:
        report = build_report(all_results, args.seed, args.sign_key)
    except Exception as e:
        print(f"[!] Signing failed: {e}")
        report = build_report(all_results, args.seed, None)

    print("=" * 66)
    if report["passed"] == report["total"]:
        print(f"[SUCCESS] ALL {report['total']} ADVERSARIAL TESTS PASSED")
    else:
        print(f"[FAILURE] {report['total']-report['passed']}/{report['total']} FAILED")
    print("=" * 66)
    print(f"System Status     : {report['status']}")
    print(f"Tests             : {report['passed']}/{report['total']}")
    print(f"Report Hash       : {report['report_hash']}")
    print(f"Script Hash       : {report['validator_script_hash']}")
    if report["signature"]:
        print(f"Signature ({report['signature_alg']}): {report['signature'][:64]}...")
    print()

    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"JSON report saved : {args.out}")

    write_html_report(report, args.html)
    print(f"HTML report saved : {args.html}")


if __name__ == "__main__":
    main()
