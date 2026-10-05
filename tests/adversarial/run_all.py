#!/usr/bin/env python3
"""ADIE adversarial test suite — 50 tests."""
import base64, json, secrets, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "adie-cli.py"
PY = sys.executable

PASS, FAIL = 0, 0
RESULTS = []


def run(args, timeout=10):
    try:
        r = subprocess.run([PY, str(CLI)] + args, capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def setup():
    tmp = Path(tempfile.mkdtemp(prefix="adie-adv-"))
    ctx = {"tmp": tmp}
    for name in ("primary", "secondary", "attacker"):
        run(["keygen", "--out", str(tmp / f"{name}.pem"),
             "--pub", str(tmp / f"{name}-pub.pem")])
        ctx[f"{name}_priv"] = tmp / f"{name}.pem"
        ctx[f"{name}_pub"] = tmp / f"{name}-pub.pem"
    d = tmp / "decision.json"
    d.write_text(json.dumps({"applicant_id": "anon-4291", "amount": 25000,
                             "currency": "EUR", "decision": "REJECTED"}))
    ctx["decision"] = d
    valid = tmp / "valid.json"
    run(["issue", "--decision", str(d), "--policy", "credit-risk-v3",
         "--key", str(ctx["primary_priv"]), "--issuer", "test.local",
         "--out", str(valid)])
    ctx["valid"] = valid
    return ctx


def load(p):
    return json.loads(Path(p).read_text())


def save(cert, p):
    Path(p).write_text(json.dumps(cert, indent=2))
    return p


def mod(ctx, fn, name):
    cert = load(ctx["valid"])
    fn(cert)
    p = ctx["tmp"] / f"mod-{name}.json"
    save(cert, p)
    return p


def verify(cert_path, pub_path):
    out = run(["verify", "--cert", str(cert_path), "--pub", str(pub_path)])
    if out.startswith("INVALID: "):
        return out[len("INVALID: "):]
    return out


def fresh_issue(ctx, decision=None, policy="credit-risk-v3",
                key=None, issuer="test.local"):
    out = ctx["tmp"] / f"fresh-{secrets.token_hex(4)}.json"
    run(["issue", "--decision", str(decision or ctx["decision"]),
         "--policy", policy, "--key", str(key or ctx["primary_priv"]),
         "--issuer", issuer, "--out", str(out)])
    return out


def test(name, expected, fn):
    global PASS, FAIL
    try:
        actual = fn()
    except Exception as e:
        actual = f"EXC:{type(e).__name__}:{e}"
    ok = actual == expected or actual.startswith(expected)
    status = "PASS" if ok else "FAIL"
    RESULTS.append((name, expected, actual, status))
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"[{status}] {name}\n       expected: {expected}\n       actual:   {actual}")


def main():
    ctx = setup()
    ZERO = "sha256:" + "0" * 64
    V = ctx["valid"]
    P = ctx["primary_pub"]
    print("=" * 70)
    print("ADIE Adversarial Test Suite — 50 tests")
    print("=" * 70)
    print(f"Fixture: {ctx['tmp']}\n")

    # ── Group A: Valid (3) ─────────────────────────────────────────
    test("A01 valid certificate", "VALID", lambda: verify(V, P))
    test("A02 valid, different policy", "VALID",
         lambda: verify(fresh_issue(ctx, policy="other-v1"), P))
    test("A03 valid, different issuer", "VALID",
         lambda: verify(fresh_issue(ctx, issuer="bank.example"), P))

    # ── Group B: Content tampering → E002 (8) ──────────────────────
    for field, val in [
        ("decision_hash", ZERO), ("policy_version", "evil-v9"),
        ("issued_at", "2026-10-05T00:00:00Z"),
        ("expires_at", "2030-10-05T00:00:00Z"),
        ("nonce", "a" * 32), ("evidence_ref", ZERO),
        ("issuer", "evil.example"),
    ]:
        test(f"B {field} tampered → E002", "E002_HASH_MISMATCH",
             lambda f=field, v=val: verify(mod(ctx, lambda c: c.update({f: v}), f), P))

    test("B version tampered → E009", "E009_VERSION_MISMATCH",
         lambda: verify(mod(ctx, lambda c: c.update(version="9.9"), "ver"), P))

    # ── Group C: Key substitution → E003 (4) ───────────────────────
    test("C01 wrong public key (attacker)", "E003_KEY_SUBSTITUTION",
         lambda: verify(V, ctx["attacker_pub"]))
    test("C02 wrong public key (secondary)", "E003_KEY_SUBSTITUTION",
         lambda: verify(V, ctx["secondary_pub"]))
    test("C03 fingerprint altered in cert", "E003_KEY_SUBSTITUTION",
         lambda: verify(mod(ctx, lambda c: c.update(issuer_fingerprint=ZERO), "fp"), P))
    test("C04 cert signed w/ attacker, verified w/ primary", "E003_KEY_SUBSTITUTION",
         lambda: verify(fresh_issue(ctx, key=ctx["attacker_priv"]), P))

    # ── Group D: Expiry → E001/E008 (3) ────────────────────────────
    test("D01 expired certificate", "E001_EXPIRED",
         lambda: verify(mod(ctx, lambda c: c.update(
             issued_at="2020-01-01T00:00:00Z",
             expires_at="2021-01-01T00:00:00Z"), "exp"), P))
    test("D02 expires_at = now-ish past", "E001_EXPIRED",
         lambda: verify(mod(ctx, lambda c: c.update(
             issued_at="2020-01-01T00:00:00Z",
             expires_at="2024-01-01T00:00:00Z"), "exp2"), P))
    test("D03 issued_at > expires_at", "E008_INVALID_TIMESTAMP",
         lambda: verify(mod(ctx, lambda c: c.update(
             issued_at="2030-01-01T00:00:00Z",
             expires_at="2025-01-01T00:00:00Z"), "inv"), P))

    # ── Group E: Signature tampering (4) ───────────────────────────
    def truncate(c):
        s = c["signature"]
        c["signature"] = s[:30]
    def zero_sig(c):
        c["signature"] = "base64:" + base64.b64encode(b"\x00" * 256).decode()
    def flip_bit(c):
        s = base64.b64decode(c["signature"][7:])
        s = bytes([s[0] ^ 1]) + s[1:]
        c["signature"] = "base64:" + base64.b64encode(s).decode()
    def empty_sig(c):
        c["signature"] = "base64:"

    test("E01 truncated signature → E006", "E006_INVALID_SIGNATURE_FORMAT",
         lambda: verify(mod(ctx, truncate, "trunc"), P))
    test("E02 zero signature → E002", "E002_HASH_MISMATCH",
         lambda: verify(mod(ctx, zero_sig, "zero"), P))
    test("E03 flipped bit in signature → E002", "E002_HASH_MISMATCH",
         lambda: verify(mod(ctx, flip_bit, "flip"), P))
    test("E04 empty signature → E006", "E006_INVALID_SIGNATURE_FORMAT",
         lambda: verify(mod(ctx, empty_sig, "empty"), P))

    # ── Group F: JSON structure (8) ────────────────────────────────
    def drop(field):
        return lambda c: c.pop(field, None)
    for field in ["signature", "decision_hash", "issuer", "version", "nonce"]:
        test(f"F missing {field} → E005", "E005_MISSING_FIELD",
             lambda f=field: verify(mod(ctx, drop(f), f"drop-{f}"), P))

    def write_raw(ctx, name, content):
        p = ctx["tmp"] / name
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content)
        return p

    test("F06 malformed JSON → E004", "E004_MALFORMED_JSON",
         lambda: verify(write_raw(ctx, "bad.json", "{not json}"), P))
    test("F07 empty file → E004", "E004_MALFORMED_JSON",
         lambda: verify(write_raw(ctx, "empty.json", ""), P))
    test("F08 array instead of object → E011", "E011_SCHEMA_VIOLATION",
         lambda: verify(write_raw(ctx, "arr.json", "[1,2,3]"), P))
    test("F09 JSON string → E011", "E011_SCHEMA_VIOLATION",
         lambda: verify(write_raw(ctx, "str.json", '"hello"'), P))

    # ── Group G: Base64 manipulation (4) ───────────────────────────
    test("G01 signature without base64: prefix → E006", "E006_INVALID_SIGNATURE_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             signature=c["signature"].replace("base64:", "")), "nopfx"), P))
    test("G02 signature with invalid base64 → E006", "E006_INVALID_SIGNATURE_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             signature="base64:!!!invalid!!!"), "bad64"), P))
    test("G03 signature with wrong case prefix → E006", "E006_INVALID_SIGNATURE_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             signature=c["signature"].replace("base64:", "BASE64:")), "case"), P))
    test("G04 signature with whitespace → E006", "E006_INVALID_SIGNATURE_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             signature="base64: AAA AAAA"), "ws"), P))

    # ── Group H: Fingerprint format (4) ────────────────────────────
    test("H01 fingerprint missing sha256: → E007", "E007_INVALID_FINGERPRINT_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             issuer_fingerprint=c["issuer_fingerprint"][7:]), "nopfx-fp"), P))
    test("H02 fingerprint uppercase → E007", "E007_INVALID_FINGERPRINT_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             issuer_fingerprint=c["issuer_fingerprint"].upper()), "up"), P))
    test("H03 fingerprint too short → E007", "E007_INVALID_FINGERPRINT_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             issuer_fingerprint="sha256:abc"), "short"), P))
    test("H04 fingerprint non-hex → E007", "E007_INVALID_FINGERPRINT_FORMAT",
         lambda: verify(mod(ctx, lambda c: c.update(
             issuer_fingerprint="sha256:" + "z" * 64), "nonhex"), P))

    # ── Group I: Time format (4) ───────────────────────────────────
    test("I01 issued_at without timezone → E008", "E008_INVALID_TIMESTAMP",
         lambda: verify(mod(ctx, lambda c: c.update(
             issued_at="2026-10-05T10:00:00"), "tz1"), P))
    test("I02 expires_at without timezone → E008", "E008_INVALID_TIMESTAMP",
         lambda: verify(mod(ctx, lambda c: c.update(
             expires_at="2027-10-05T10:00:00"), "tz2"), P))
    test("I03 invalid timestamp string → E008", "E008_INVALID_TIMESTAMP",
         lambda: verify(mod(ctx, lambda c: c.update(
             issued_at="not-a-date"), "baddate"), P))
    test("I04 non-string timestamp → E008", "E008_INVALID_TIMESTAMP",
         lambda: verify(mod(ctx, lambda c: c.update(
             issued_at=12345), "nonstr"), P))

    # ── Group J: Encoding / Unicode (3) ────────────────────────────
    test("J01 invalid UTF-8 bytes → E010", "E010_INVALID_UNICODE",
         lambda: verify(write_raw(ctx, "utf8.json", b'\xff\xfe\x00\x00bad'), P))
    test("J02 valid UTF-8 issuer with emoji → VALID", "VALID",
         lambda: verify(fresh_issue(ctx, issuer="банк.example"), P))
    test("J03 cert with escaped Unicode → VALID", "VALID",
         lambda: verify(fresh_issue(ctx, issuer="テスト.example"), P))

    # ── Group K: Cross-key (3) ─────────────────────────────────────
    test("K01 attacker cert verified w/ attacker pub → VALID", "VALID",
         lambda: verify(fresh_issue(ctx, key=ctx["attacker_priv"]),
                        ctx["attacker_pub"]))
    test("K02 secondary cert verified w/ attacker pub → E003", "E003_KEY_SUBSTITUTION",
         lambda: verify(fresh_issue(ctx, key=ctx["secondary_priv"]),
                        ctx["attacker_pub"]))
    test("K03 primary cert verified w/ secondary pub → E003", "E003_KEY_SUBSTITUTION",
         lambda: verify(V, ctx["secondary_pub"]))

    # ── Group L: Misc (2) ──────────────────────────────────────────
    test("L01 empty nonce → E002", "E002_HASH_MISMATCH",
         lambda: verify(mod(ctx, lambda c: c.update(nonce=""), "en"), P))
    test("L02 signature-nonce swap → E002", "E002_HASH_MISMATCH",
         lambda: verify(mod(ctx, lambda c: c.update(
             nonce=c["nonce"][::-1]), "rev"), P))

    # ── Summary ────────────────────────────────────────────────────
    print("=" * 70)
    print(f"TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
    print("=" * 70)
    if FAIL:
        print("\nFailed tests:")
        for name, exp, act, st in RESULTS:
            if st == "FAIL":
                print(f"  • {name}: expected {exp}, got {act}")
    shutil.rmtree(ctx["tmp"], ignore_errors=True)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
