#!/usr/bin/env python3
"""B+ E2E: envelope → parse → verify hybrid signatures → ACCEPT/REJECT."""
import json, subprocess, sys, base64, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BIN = ROOT / "rust/adie-primitives/target/release/adie-cbor-envelope"

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from dilithium_py.ml_dsa import ML_DSA_65 as DLP

from protocol.hybrid.certificate import build_dcp21_payload, attach_signatures
from protocol.hybrid.sign import sign_hybrid
from protocol.hybrid.verify import verify_hybrid

PASS_N = FAIL_N = 0
def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"[PASS] {name}")
    else:
        FAIL_N += 1
        print(f"[FAIL] {name}: {detail}")

def r_call(p):
    r = subprocess.run([str(BIN)], input=json.dumps(p),
                       capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

print("=" * 72)
print("B+ E2E hybrid verification")
print("=" * 72)

# Fresh key material
rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
rsa_pub_pem = rsa_priv.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
rsa_priv_pem = rsa_priv.private_bytes(
    serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption())
seed = bytes([0x99]*32)
mldsa_pk, mldsa_sk = DLP.key_derive(seed)

payload = build_dcp21_payload(
    claim_id="e2e-bplus-001",
    issuer_did="did:adie:issuer-e2e",
    issuer_key_id="sha256:" + "0"*64,
    subject={"model_id": "credit-v7"},
    request={"id": "r1", "operation": "evaluate"},
    context={"locale": "en", "jurisdiction": "EU"},
    policy={"id": "credit-risk", "version": "7",
            "expression": {"op": "EXISTS", "path": "model.id"}},
    model={"id": "model-v1", "provider": "issuer-e2e"},
    data={"commitment": "sha256:" + "c"*64},
    runtime={"measurement": "sha256:" + "d"*64, "attestation": "ok"},
    output={"result": "REJECTED", "score": 0},
    binding={"audience": "com.example.deployment", "purpose": 7,
             "resource": "model://e2e-bplus-001",
             "request_hash": "sha256:" + "e"*64,
             "nonce": "a"*32,
             "certificate_id": "e2e-bplus-001"},
    temporal={"issued_at": "2026-10-07T00:00:00Z"},
    evidence={"attestations": []},
    authoring={"template_digest": "sha256:" + "0"*64,
               "parameter_digest": "sha256:" + "1"*64,
               "compiler_digest": "sha256:" + "2"*64,
               "acl_version": "0.1",
               "canonical_ast_digest": "sha256:" + "3"*64,
               "meta_manifest_digest": "sha256:" + "4"*64},
)
sigs = sign_hybrid(payload, rsa_pub_pem, rsa_priv_pem, mldsa_pk, mldsa_sk)
cert = attach_signatures(payload, sigs)

# ─── H01: Build envelope, parse, verify ───
r_build = r_call({"op":"build","certificate_json":json.dumps(cert)})
check("H01 envelope build", "envelope_hex" in r_build, str(r_build)[:80])
env_hex = r_build.get("envelope_hex","")

r_parse = r_call({"op":"parse","envelope_hex":env_hex})
check("H02 envelope parse", "certificate_json" in r_parse, str(r_parse)[:80])
cert_recovered = json.loads(r_parse["certificate_json"])

# ─── H03: Reconstruct TBS from recovered cert, verify hybrid ───
payload_recovered = {k: v for k, v in cert_recovered.items() if k != "signatures"}
r_verify = verify_hybrid(
    payload_recovered,
    cert_recovered["signatures"],
    ["RS256", "ML-DSA-65"],
    rs256_pub_pem=rsa_pub_pem,
    mldsa65_pub_raw=mldsa_pk,
)
check("H03 hybrid verify VALID (both sigs)", r_verify.get("status") == "VALID", str(r_verify)[:100])

# ─── H04: Tamper recovered cert output → REJECT ───
payload_tampered = dict(payload_recovered)
payload_tampered["output"] = {"result": "APPROVED", "score": 100}
try:
    r_t = verify_hybrid(payload_tampered, cert_recovered["signatures"],
                        ["RS256", "ML-DSA-65"],
                        rs256_pub_pem=rsa_pub_pem,
                        mldsa65_pub_raw=mldsa_pk)
    check("H04 tampered output rejected", r_t.get("status") != "VALID", str(r_t)[:80])
except Exception as e:
    check("H04 tampered output rejected", True, f"raised: {e}")

# ─── H05: Remove RS256 sig → downgrade rejected ───
sigs_no_rs = [s for s in cert_recovered["signatures"] if s["alg"] != "RS256"]
try:
    r_d = verify_hybrid(payload_recovered, sigs_no_rs, ["RS256","ML-DSA-65"],
                        rs256_pub_pem=rsa_pub_pem, mldsa65_pub_raw=mldsa_pk)
    check("H05 RS256-missing rejected", r_d.get("status") != "VALID", str(r_d)[:80])
except Exception as e:
    check("H05 RS256-missing rejected", True, f"raised: {e}")

# ─── H06: Remove ML-DSA sig → downgrade rejected ───
sigs_no_pq = [s for s in cert_recovered["signatures"] if s["alg"] != "ML-DSA-65"]
try:
    r_d = verify_hybrid(payload_recovered, sigs_no_pq, ["RS256","ML-DSA-65"],
                        rs256_pub_pem=rsa_pub_pem, mldsa65_pub_raw=mldsa_pk)
    check("H06 ML-DSA-missing rejected", r_d.get("status") != "VALID", str(r_d)[:80])
except Exception as e:
    check("H06 ML-DSA-missing rejected", True, f"raised: {e}")

# ─── H07: Tamper RS256 sig bytes → reject ───
tampered_sigs = json.loads(json.dumps(cert_recovered["signatures"]))
for s in tampered_sigs:
    if s["alg"] == "RS256":
        raw = bytearray(base64.b64decode(s["value"][7:]))
        raw[0] ^= 0xFF
        s["value"] = "base64:" + base64.b64encode(bytes(raw)).decode()
try:
    r_t = verify_hybrid(payload_recovered, tampered_sigs, ["RS256","ML-DSA-65"],
                        rs256_pub_pem=rsa_pub_pem, mldsa65_pub_raw=mldsa_pk)
    check("H07 tampered RS256 rejected", r_t.get("status") != "VALID", str(r_t)[:80])
except Exception as e:
    check("H07 tampered RS256 rejected", True, f"raised: {e}")

# ─── H08: Tamper ML-DSA sig bytes → reject ───
tampered_sigs = json.loads(json.dumps(cert_recovered["signatures"]))
for s in tampered_sigs:
    if s["alg"] == "ML-DSA-65":
        raw = bytearray(base64.b64decode(s["value"][7:]))
        raw[100] ^= 0xFF
        s["value"] = "base64:" + base64.b64encode(bytes(raw)).decode()
try:
    r_t = verify_hybrid(payload_recovered, tampered_sigs, ["RS256","ML-DSA-65"],
                        rs256_pub_pem=rsa_pub_pem, mldsa65_pub_raw=mldsa_pk)
    check("H08 tampered ML-DSA rejected", r_t.get("status") != "VALID", str(r_t)[:80])
except Exception as e:
    check("H08 tampered ML-DSA rejected", True, f"raised: {e}")

# ─── H09: TBS identity preserved ───
from protocol.hybrid.tbs import build_tbs, DOMAIN_TAG
tbs_orig = build_tbs({k:v for k,v in cert.items() if k != "signatures"})
tbs_rec = build_tbs(payload_recovered)
check("H09 TBS byte-identical after envelope round-trip",
      tbs_orig == tbs_rec,
      f"len_orig={len(tbs_orig)} len_rec={len(tbs_rec)}")

# ─── H10: domain tag unchanged ───
check("H10 domain tag 12 bytes = ADIE-SIG-V2\\0",
      DOMAIN_TAG == b"ADIE-SIG-V2\x00" and len(DOMAIN_TAG) == 12)

print()
print("=" * 72)
print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
print("=" * 72)
sys.exit(0 if FAIL_N == 0 else 1)
