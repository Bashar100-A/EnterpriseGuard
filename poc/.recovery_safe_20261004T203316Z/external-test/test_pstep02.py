#!/usr/bin/env python3
"""ADIE POC — P-STEP-02 Test Suite. 10 cases."""
import subprocess, sys, json
from pathlib import Path

HERE = Path(__file__).parent
VERIFY = HERE / "verify.py"
CERT = HERE / "certificate-001.json"
KEY = HERE / "public-key-001.pem"
WRONG_KEY = HERE / "wrong-key.pem"
TMP = HERE / ".tmp_test_cert.json"

def run(content, key=KEY):
    TMP.write_text(content)
    r = subprocess.run(
        [sys.executable, str(VERIFY), str(TMP), str(key)],
        capture_output=True, text=True
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def expect(content, code, key=KEY):
    rc, out, err = run(content, key)
    if code == "VALID":
        assert rc == 0 and out == "VALID", f"expected VALID, got rc={rc} out={out!r} err={err!r}"
    else:
        assert rc == 1, f"expected rc=1, got {rc} out={out!r}"
        assert code in out, f"expected {code}, got {out!r}"

def load():
    return json.loads(CERT.read_text())

results = []
def record(name, ok_):
    print(f"{'✅' if ok_ else '❌'} {name}")
    results.append((name, ok_))

# TC-01
try:
    expect(CERT.read_text(), "VALID"); record("TC-01 valid → VALID", True)
except AssertionError as e: record(f"TC-01: {e}", False)

# TC-02
try:
    c = load(); s = c["signature"]["value"]
    c["signature"]["value"] = ("0" if s[0] != "0" else "1") + s[1:]
    expect(json.dumps(c), "E001"); record("TC-02 signature tampered → E001", True)
except AssertionError as e: record(f"TC-02: {e}", False)

# TC-03
try:
    c = load(); c["decision_contract"]["parameters"] = {"tampered": True}
    expect(json.dumps(c), "E002"); record("TC-03 contract tampered → E002", True)
except AssertionError as e: record(f"TC-03: {e}", False)

# TC-04
try:
    c = load(); del c["signature"]
    expect(json.dumps(c), "E003"); record("TC-04 missing field → E003", True)
except AssertionError as e: record(f"TC-04: {e}", False)

# TC-05
try:
    c = load(); c["signature"]["algorithm"] = "none"
    expect(json.dumps(c), "E005"); record("TC-05 algorithm downgrade → E005", True)
except AssertionError as e: record(f"TC-05: {e}", False)

# TC-06
try:
    c = load(); c["issued_at"] = "not-a-date"
    expect(json.dumps(c), "E006"); record("TC-06 timestamp malformed → E006", True)
except AssertionError as e: record(f"TC-06: {e}", False)

# TC-07
try:
    c = load(); c["protocol"]["version"] = "0.9"
    expect(json.dumps(c), "E007"); record("TC-07 version mismatch → E007", True)
except AssertionError as e: record(f"TC-07: {e}", False)

# TC-08
try:
    content = CERT.read_text()
    content = content.replace('"adie-poc-001"', '"\\uD800"', 1)
    expect(content, "E009"); record("TC-08 invalid unicode → E009", True)
except AssertionError as e: record(f"TC-08: {e}", False)

# TC-09
try:
    expect(CERT.read_text(), "E001", key=WRONG_KEY)
    record("TC-09 wrong public key → E001", True)
except AssertionError as e: record(f"TC-09: {e}", False)

# TC-10
try:
    content = CERT.read_text()
    content = content.replace(
        '"protocol": {',
        '"protocol": {"name":"X","version":"Y","profile":"Z"}, "protocol": {',
        1
    )
    expect(content, "E010"); record("TC-10 duplicate key → E010", True)
except AssertionError as e: record(f"TC-10: {e}", False)

if TMP.exists():
    TMP.unlink()

passed = sum(1 for _, ok in results if ok)
print("")
print("=" * 60)
print(f"Results: {passed}/{len(results)} passed")
print("=" * 60)
sys.exit(0 if passed == len(results) else 1)
