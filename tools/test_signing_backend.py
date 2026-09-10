#!/usr/bin/env python3
"""Unit tests for signing_backend with mock and local modes."""

import os
import sys
import hashlib

sys.dont_write_bytecode = True

from tools.signing_backend import sign_bytes, verify_signature_hex, sign_genesis_chain_id_hex, verify_genesis_signature_hex


def test_mock_mode():
    os.environ["AAAC_SIGNING_BACKEND"] = "mock"
    data = "test-data"
    sig = sign_bytes(data)
    if not (isinstance(sig, str) and len(sig) == 64):
        raise ValueError("Mock signature must be 64 hex chars")
    if verify_signature_hex(data, sig) != True:
        raise ValueError("Mock verification failed")
    if verify_signature_hex(data, "00" * 64) != False:
        raise ValueError("Wrong signature unexpectedly passed")
    print("Mock mode test passed")


def test_local_mode():
    os.environ.pop("AAAC_SIGNING_BACKEND", None)  # default local
    data = "test-data-local"
    sig = sign_bytes(data)
    if not (isinstance(sig, str) and len(sig) > 0):
        raise ValueError("Local signature invalid")
    if verify_signature_hex(data, sig) != True:
        raise ValueError("Local verification failed")
    print("Local mode test passed")


def test_mock_genesis():
    os.environ["AAAC_SIGNING_BACKEND"] = "mock"
    chain_id = "chain-abc"
    sig = sign_genesis_chain_id_hex(chain_id)
    if not (isinstance(sig, str) and len(sig) == 64):
        raise ValueError("Mock genesis signature invalid")
    if verify_genesis_signature_hex(chain_id, sig) != True:
        raise ValueError("Mock genesis verification failed")
    print("Mock genesis test passed")


if __name__ == "__main__":
    test_mock_mode()
    test_local_mode()
    test_mock_genesis()
    print("All signing backend tests passed")
