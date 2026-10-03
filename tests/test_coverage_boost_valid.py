import pytest
from enterpriseguard.decision.contracts import DecisionContract, ADIEDecision, DecisionStatus
from enterpriseguard.response.contracts import ResponseContract, ADIEResponse, ResponseStatus
from enterpriseguard.signing.backend import sign_bytes, verify_signature_hex, SigningError

def test_decision_contracts_basic():
    engine = ADIEDecision()
    assert engine is not None

def test_response_contracts_basic():
    engine = ADIEResponse()
    assert engine is not None

def test_signing_backend_valid_flow():
    data = "test payload"
    sig = sign_bytes(data)
    assert verify_signature_hex(data, sig) is True
    assert verify_signature_hex("invalid data", sig) is False
