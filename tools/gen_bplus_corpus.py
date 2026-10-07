#!/usr/bin/env python3
"""Generate B+ canonical corpus (Amendment-2).
Real DCP 2.1 certs via existing machinery — no hand-authored data.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from dilithium_py.ml_dsa import ML_DSA_65 as DLP

from protocol.hybrid.certificate import build_dcp21_payload, attach_signatures
from protocol.hybrid.sign import sign_hybrid
from protocol.hybrid.tbs import build_tbs, DOMAIN_TAG
from protocol.core.jcs import canonical_bytes

NESTED = ['issuer','subject','request','context','policy','model','data',
          'runtime','output','binding','temporal','evidence','authoring']

def make_vector(idx):
    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pub_pem = rsa_priv.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    rsa_priv_pem = rsa_priv.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    seed = bytes([0x42 + idx] * 32)
    mldsa_pk, mldsa_sk = DLP.key_derive(seed)

    payload = build_dcp21_payload(
        claim_id=f"bplus-{idx:03d}",
        issuer_did="did:adie:issuer-bplus",
        issuer_key_id="sha256:" + "0"*64,
        subject={"model_id": "credit-v7", "version": "2026.10"},
        request={"id": f"r-{idx}", "operation": "evaluate"},
        context={"locale": "en", "jurisdiction": "EU"},
        policy={"id": "credit-risk", "version": "7",
                "expression": {"op": "EXISTS", "path": "model.id"}},
        model={"id": "model-v1", "provider": "issuer-bplus"},
        data={"commitment": "sha256:" + "c"*64},
        runtime={"measurement": "sha256:" + "d"*64, "attestation": "ok"},
        output={"result": "REJECTED", "score": 0},
        binding={"audience": "com.example.deployment", "purpose": 7,
                 "resource": f"model://bplus-{idx:03d}",
                 "request_hash": "sha256:" + "e"*64,
                 "nonce": "a"*32,
                 "certificate_id": f"bplus-{idx:03d}"},
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

    tbs = build_tbs(payload)
    nested_jcs = {f: canonical_bytes(cert[f]).hex() for f in NESTED}
    cr_hex = cert["claim_root"].removeprefix("sha256:")
    return {
        "id": f"P{idx:02d}",
        "certificate": cert,
        "tbs_hex": tbs.hex(),
        "tbs_len": len(tbs),
        "domain_tag_hex": DOMAIN_TAG.hex(),
        "nested_jcs_hex": nested_jcs,
        "claim_root_hex": cr_hex,
        "signature_lengths": {
            "RS256": len(__import__("base64").b64decode(
                [s for s in cert["signatures"] if s["alg"]=="RS256"][0]["value"].removeprefix("base64:"))),
            "ML-DSA-65": len(__import__("base64").b64decode(
                [s for s in cert["signatures"] if s["alg"]=="ML-DSA-65"][0]["value"].removeprefix("base64:"))),
        },
    }

def main():
    vectors = [make_vector(i) for i in range(1, 6)]  # 5 vectors
    corpus = {
        "version": "3A.5-B+-CORPUS-1",
        "amendment": "WIRE-FORMAT-0.2-AMENDMENT-2",
        "positive": vectors,
    }
    out = ROOT / "tests/vomega/b-plus/corpus.json"
    out.write_text(json.dumps(corpus, indent=2, sort_keys=True))
    print(f"OK corpus written: {out}")
    print(f"   positive vectors: {len(vectors)}")
    v = vectors[0]
    print(f"   sample id: {v['id']}")
    print(f"   tbs_len: {v['tbs_len']}")
    print(f"   sig lengths: RS256={v['signature_lengths']['RS256']} ML-DSA-65={v['signature_lengths']['ML-DSA-65']}")
    print(f"   nested fields: {len(v['nested_jcs_hex'])}")

if __name__ == "__main__":
    main()
