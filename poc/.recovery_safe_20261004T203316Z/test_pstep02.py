import subprocess, sys, json
from pathlib import Path
HERE = Path(file).parent
VERIFY = HERE / "verify.py"
CERT = HERE / "certificate-001.json"
KEY = HERE / "public-key-001.pem"
WRONG_KEY = HERE / "wrong-key.pem"
TMP = HERE / ".tmp_fortress_cert.json"
def run(content, key=KEY):
TMP.write_text(content, encoding="utf-8")
r = subprocess.run([sys.executable, str(VERIFY), str(TMP), str(key)], capture_output=True, text=True)
return r.returncode, r.stdout.strip(), r.stderr.strip()
def expect(content, code, key=KEY):
rc, out, _ = run(content, key)
assert rc == 1 and code in out, f"Expected {code}, got {out!r}"
results = []
def record(n, ok): print(f"{'✅' if ok else '❌'} {n}"); results.append(ok)
## TC-01: Baseline
rc, out, _ = run(CERT.read_text(encoding="utf-8"))
record("TC-01 Baseline Valid", rc == 0 and out == "VALID")
## TC-02: Tampered Sig
c = json.loads(CERT.read_text(encoding="utf-8")); s = c["signature"]["value"]
c["signature"]["value"] = ("0" if s[0] != "0" else "1") + s[1:]
try: expect(json.dumps(c), "E001"); record("TC-02 Tampered Signature -> E001", True)
except Exception: record("TC-02 Failure", False)
## TC-03: Tampered Content
c = json.loads(CERT.read_text(encoding="utf-8")); c["decision_contract"]["parameters"] = {"attack": True}
try: expect(json.dumps(c), "E002"); record("TC-03 Tampered Content -> E002", True)
except Exception: record("TC-03 Failure", False)
## TC-04: Missing Field
c = json.loads(CERT.read_text(encoding="utf-8")); del c["signature"]
try: expect(json.dumps(c), "E003"); record("TC-04 Missing Field -> E003", True)
except Exception: record("TC-04 Failure", False)
## TC-05: Downgrade Attack
c = json.loads(CERT.read_text(encoding="utf-8")); c["signature"]["algorithm"] = "none"
try: expect(json.dumps(c), "E005"); record("TC-05 Downgrade Attempt -> E005", True)
except Exception: record("TC-05 Failure", False)
## TC-06: Bad Timestamp
c = json.loads(CERT.read_text(encoding="utf-8")); c["issued_at"] = "2026-99-99"
try: expect(json.dumps(c), "E006"); record("TC-06 Malformed Date -> E006", True)
except Exception: record("TC-06 Failure", False)
## TC-07: Version Drift
c = json.loads(CERT.read_text(encoding="utf-8")); c["protocol"]["version"] = "9.9"
try: expect(json.dumps(c), "E007"); record("TC-07 Version Mismatch -> E007", True)
except Exception: record("TC-07 Failure", False)
## TC-08: Malformed Unicode Surrogate
raw = CERT.read_text(encoding="utf-8").replace('"adie-poc-001"', '"\uD800"', 1)
try: expect(raw, "E009"); record("TC-08 Invalid Unicode -> E009", True)
except Exception: record("TC-08 Failure", False)
## TC-09: Wrong Key Lock
try: expect(CERT.read_text(encoding="utf-8"), "E001", key=WRONG_KEY); record("TC-09 Key Substitution -> E001", True)
except Exception: record("TC-09 Failure", False)
## TC-10: Duplicate Key Injection Attack
raw = CERT.read_text(encoding="utf-8").replace('"protocol": {', '"protocol": {"name":"FAIL"}, "protocol": {', 1)
try: expect(raw, "E010"); record("TC-10 Duplicate JSON Key Injection -> E010", True)
except Exception: record("TC-10 Failure", False)
if TMP.exists(): TMP.unlink()
print(f"\nFortress Test Result: {sum(results)}/10 Passed")
