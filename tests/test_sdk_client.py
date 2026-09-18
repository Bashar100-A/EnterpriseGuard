"""Tests for src/enterpriseguard/sdk/ (B1.11 — SDK Client).

Scenarios per DC-139 v2 + review fixes (C1, C5, H1-H5, M3, M7).
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from enterpriseguard.sdk import Client, SignedDecision


# ─────────────────────── fixtures ───────────────────────

def _make_rsa_keypair(base):
    """Generate one RSA-2048 keypair under base/keys/."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_dir = base / "keys"
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / "private_key.pem").write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    (key_dir / "public_key.pem").write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return key_dir


@pytest.fixture
def rsa_key_dir(tmp_path):
    return _make_rsa_keypair(tmp_path)


# ─────────── 1. 5-line end-to-end ───────────

def test_decide_and_verify_roundtrip(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    signed = client.decide(target="host-01", intent="isolate")
    assert isinstance(signed, SignedDecision)
    assert client.verify(signed) is True
    assert signed.contract.authorized is True
    assert signed.contract.action.value == "isolate_host"


# ─────────── 2. Reproducibility — same instance ───────────

def test_same_inputs_same_decision_id(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    d1 = client.create_decision(target="host-01", intent="isolate")
    d2 = client.create_decision(target="host-01", intent="isolate")
    assert d1.evaluation_id == d2.evaluation_id
    assert d1.decision_id == d2.decision_id

    d3 = client.create_decision(target="host-02", intent="isolate")
    assert d3.evaluation_id != d1.evaluation_id
    assert d3.decision_id != d1.decision_id


# ─────────── 3. Reproducibility — across processes (C5 fix) ───────────

def test_reproducible_across_subprocesses(rsa_key_dir):
    """Same inputs in two fresh Python processes -> same decision_id."""
    code = (
        "import sys; "
        "from enterpriseguard.sdk import Client; "
        "c = Client(key_dir=sys.argv[1]); "
        "d = c.create_decision(target='host-01', intent='isolate'); "
        "print(d.decision_id)"
    )
    results = []
    for _ in range(2):
        r = subprocess.run(
            [sys.executable, "-c", code, str(rsa_key_dir)],
            capture_output=True, text=True, check=True,
        )
        results.append(r.stdout.strip())
    assert results[0] == results[1]
    assert results[0].startswith("dec-")


# ─────────── 4. Tampered contract ───────────

def test_tampered_contract_returns_false(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    signed = client.decide(target="host-01", intent="isolate")
    assert client.verify(signed) is True

    other = client.create_decision(target="host-99", intent="isolate")
    tampered = replace(signed, contract=other)
    assert client.verify(tampered) is False


# ─────────── 5. Tampered signature ───────────

def test_tampered_signature_returns_false(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    signed = client.decide(target="host-01", intent="isolate")
    sig = signed.signature_hex
    corrupted = ("0" if sig[0] != "0" else "1") + sig[1:]
    tampered = replace(signed, signature_hex=corrupted)
    assert client.verify(tampered) is False


# ─────────── 6. Tampered signed_at (H1 protection) ───────────

def test_tampered_signed_at_returns_false(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    signed = client.decide(target="host-01", intent="isolate")
    later = signed.signed_at + timedelta(hours=1)
    tampered = replace(signed, signed_at=later)
    assert client.verify(tampered) is False


# ─────────── 7. Unknown backend ───────────

def test_unknown_backend_rejected(rsa_key_dir):
    with pytest.raises(ValueError):
        Client(key_dir=rsa_key_dir, backend="does_not_exist")


# ─────────── 8. create + sign separately ───────────

def test_create_then_sign_separately(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    contract = client.create_decision(target="host-01", intent="isolate")
    assert contract.authorized is True
    signed = client.sign(contract)
    assert client.verify(signed) is True


# ─────────── 9. decide() == create + sign, but signed_at differs (C1 fix) ───────────

def test_decide_equals_create_plus_sign(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    c1 = client.create_decision(target="host-01", intent="isolate")
    s1 = client.sign(c1)
    s2 = client.decide(target="host-01", intent="isolate")

    # Same contract (deterministic decision_id at contract level)
    assert s1.contract.decision_id == s2.contract.decision_id

    # signed_at IS protected (H1 fix): two signings occur at
    # different wall-clock instants, so the signed payload differs.
    assert s1.signed_at != s2.signed_at
    assert s1.signed_payload_hash != s2.signed_payload_hash

    # Both are independently valid.
    assert client.verify(s1) is True
    assert client.verify(s2) is True


# ─────────── 10. Explicit evaluation_id override (H1) ───────────

def test_explicit_evaluation_id_is_respected(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    d = client.create_decision(
        target="host-01", intent="isolate",
        evaluation_id="my-fixed-id",
    )
    assert d.evaluation_id == "my-fixed-id"


# ─────────── 11. policy_id affects decision_id (H2) ───────────

def test_policy_id_affects_decision_id(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    d1 = client.create_decision(target="h", intent="isolate", policy_id="A")
    d2 = client.create_decision(target="h", intent="isolate", policy_id="B")
    assert d1.decision_id != d2.decision_id


# ─────────── 12. parameters affect decision_id (H3) ───────────

def test_parameters_affect_decision_id(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    d1 = client.create_decision(target="h", intent="isolate",
                                parameters={"k": 1})
    d2 = client.create_decision(target="h", intent="isolate",
                                parameters={"k": 2})
    assert d1.decision_id != d2.decision_id


# ─────────── 13. Missing private key propagates clearly (H4) ───────────

def test_missing_private_key_raises(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    client = Client(key_dir=empty)
    with pytest.raises(Exception):
        client.decide(target="h", intent="isolate")


# ─────────── 14. verify with wrong key fails (H5) ───────────

def test_verify_with_wrong_key_fails(tmp_path):
    key_a = _make_rsa_keypair(tmp_path / "a")
    key_b = _make_rsa_keypair(tmp_path / "b")
    signer = Client(key_dir=key_a)
    verifier = Client(key_dir=key_b)
    signed = signer.decide(target="h", intent="isolate")
    assert verifier.verify(signed) is False


# ─────────── 15. verify rejects non-SignedDecision (M3) ───────────

def test_verify_rejects_non_signed_decision(rsa_key_dir):
    client = Client(key_dir=rsa_key_dir)
    assert client.verify(None) is False
    assert client.verify("not-a-decision") is False
    assert client.verify(42) is False
