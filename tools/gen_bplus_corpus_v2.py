#!/usr/bin/env python3
"""Expanded B+ corpus for fuzzing (Stage 3A.6)."""
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

NESTED = ['issuer','subject','request','context','policy','model','data',
          'runtime','output','binding','temporal','evidence','authoring']


def base_fields(idx):
    i = idx
    f = dict(
        subject={"model_id": "credit-v7", "version": "2026.10"},
        request={"id": "r-%d" % i, "operation": "evaluate"},
        context={"locale": "en", "jurisdiction": "EU"},
        policy={"id": "credit-risk", "version": "7",
                "expression": {"op": "EXISTS", "path": "model.id"}},
        model={"id": "model-v1", "provider": "issuer-bplus"},
        data={"commitment": "sha256:" + "c"*64},
        runtime={"measurement": "sha256:" + "d"*64, "attestation": "ok"},
        output={"result": "REJECTED", "score": 0},
        binding={"audience": "com.example.deployment", "purpose": 7,
                 "resource": "model://bplus-%03d" % i,
                 "request_hash": "sha256:" + "e"*64,
                 "nonce": "a"*32,
                 "certificate_id": "bplus-%03d" % i},
        temporal={"issued_at": "2026-10-07T00:00:00Z"},
        evidence={"attestations": []},
        authoring={"template_digest": "sha256:" + "0"*64,
                   "parameter_digest": "sha256:" + "1"*64,
                   "compiler_digest": "sha256:" + "2"*64,
                   "acl_version": "0.1",
                   "canonical_ast_digest": "sha256:" + "3"*64,
                   "meta_manifest_digest": "sha256:" + "4"*64},
    )
    if 5 <= i < 10:
        variants = [
            {"model_id": "m", "meta": {"tier": "gold", "score": 99}},
            {},
            {"model_id": "m", "tags": ["a","b","c"]},
            {"model_id": "m", "nested": {"a": {"b": {"c": 1}}}},
            {"model_id": "m", "active": True, "count": 0, "ratio": None},
        ]
        f["subject"] = variants[i-5]
    elif 10 <= i < 15:
        variants = [
            {"id": "p", "expression": {"op": "AND", "args": [
                {"op": "EXISTS", "path": "a"},
                {"op": "GT", "left": "x", "right": 5}]}},
            {"id": "p", "expression": {"op": "TRUE"}},
            {},
            {"id": "p", "rules": [{"k": 1, "v": True}, {"k": 2, "v": False}]},
            {"id": "p", "expression": {"op": "AND", "args": [
                {"op": "OR", "args": [{"op": "TRUE"}, {"op": "FALSE"}]},
                {"op": "NOT", "arg": {"op": "FALSE"}}]}},
        ]
        f["policy"] = variants[i-10]
    elif 15 <= i < 20:
        variants = [
            ({"locale": "en-US", "region": "NA", "tz": "UTC"},
             {"id": "r", "amount": 1000, "currency": "USD"}),
            ({"locale": "ar-SA"},
             {"id": "r", "flags": ["a", "b"], "urgent": True}),
            ({}, {}),
            ({"locale": "en", "tags": ["x"]*5},
             {"id": "r", "meta": {"k": "v", "n": 0}}),
            ({"locale": "fr-FR", "channel": "web"},
             {"id": "r", "user": {"id": "u1", "role": "admin"}}),
        ]
        f["context"], f["request"] = variants[i-15]
    elif 20 <= i < 25:
        ev_variants = [
            {"attestations": [{"type": "sgx", "quote": "aa"}]},
            {"attestations": [{"type": "a"}, {"type": "b"}, {"type": "c"}]},
            {},
            {"attestations": [{"type": "tpm", "measurement": "sha256:" + "f"*64}]},
            {"attestations": [{"nested": {"deep": {"deeper": 1}}}]},
        ]
        f["evidence"] = ev_variants[i-20]
    return f


def make_cert(idx):
    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pub_pem = rsa_priv.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    rsa_priv_pem = rsa_priv.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    seed = bytes([0x10 + idx] * 32)
    mldsa_pk, mldsa_sk = DLP.key_derive(seed)

    f = base_fields(idx)
    payload = build_dcp21_payload(
        claim_id="fuzz-%03d" % idx,
        issuer_did="did:adie:issuer-fuzz",
        issuer_key_id="sha256:" + "0"*64,
        subject=f["subject"],
        request=f["request"],
        context=f["context"],
        policy=f["policy"],
        model=f["model"],
        data=f["data"],
        runtime=f["runtime"],
        output=f["output"],
        binding=f["binding"],
        temporal=f["temporal"],
        evidence=f["evidence"],
        authoring=f["authoring"],
    )
    sigs = sign_hybrid(payload, rsa_pub_pem, rsa_priv_pem, mldsa_pk, mldsa_sk)
    cert = attach_signatures(payload, sigs)
    tbs = build_tbs(payload)
    return {
        "id": "F%02d" % idx,
        "certificate": cert,
        "tbs_hex": tbs.hex(),
        "tbs_len": len(tbs),
    }


def main():
    vectors = [make_cert(i) for i in range(25)]
    corpus = {
        "version": "3A.6-FUZZ-CORPUS-1",
        "amendment": "WIRE-FORMAT-0.2-AMENDMENT-2",
        "positive": vectors,
    }
    out = ROOT / "tests/vomega/b-plus/corpus_v2.json"
    out.write_text(json.dumps(corpus, indent=2, sort_keys=True))
    print("OK corpus_v2 written: %s" % out)
    print("   positive vectors: %d" % len(vectors))
    for v in vectors[:3]:
        print("   %s: tbs_len=%d" % (v['id'], v['tbs_len']))


if __name__ == "__main__":
    main()
