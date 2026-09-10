#!/usr/bin/env python3
"""Blockchain anchoring for AAAC rings using Web3 (Ganache or Sepolia)."""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version

sys.dont_write_bytecode = True

load_dotenv('.env.blockchain')  # تحميل إعدادات الشبكة

RPC_URL = os.environ.get("AAAC_CHAIN_RPC", "http://127.0.0.1:8545")
CHAIN_ID = int(os.environ.get("AAAC_CHAIN_ID", "1337"))
PRIVATE_KEY = os.environ.get("AAAC_PRIVATE_KEY", "")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise RuntimeError(f"Cannot connect to blockchain at {RPC_URL}")

# إعداد الحساب
if PRIVATE_KEY:
    account = w3.eth.account.from_key(PRIVATE_KEY).address
else:
    if CHAIN_ID == 1337:  # Ganache
        account = w3.eth.accounts[0]
    else:
        raise RuntimeError("PRIVATE_KEY required for non-local networks")

def compile_contract():
    # تثبيت solc إذا لزم
    install_solc('0.8.0')
    set_solc_version('0.8.0')
    source = Path("tools/Anchor.sol").read_text()
    compiled = compile_source(source, output_values=['abi', 'bin'])
    contract_id, contract_interface = compiled.popitem()
    return contract_interface['abi'], contract_interface['bin']

def deploy_contract():
    abi, bytecode = compile_contract()
    Anchor = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Anchor.constructor().build_transaction({
        'from': account,
        'nonce': w3.eth.get_transaction_count(account),
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price,
    })
    if PRIVATE_KEY:
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    else:
        tx_hash = w3.eth.send_transaction(tx)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt.contractAddress, abi

def anchor_ring(contract_address, abi, ring_hash, chain_id):
    Anchor = w3.eth.contract(address=contract_address, abi=abi)
    tx = Anchor.functions.anchorRing(ring_hash, chain_id).build_transaction({
        'from': account,
        'nonce': w3.eth.get_transaction_count(account),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    if PRIVATE_KEY:
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    else:
        tx_hash = w3.eth.send_transaction(tx)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt.transactionHash.hex()

if __name__ == "__main__":
    # تحقق من وجود عقد منشور مسبقًا
    contract_address = os.environ.get("AAAC_CONTRACT_ADDRESS")
    if not contract_address:
        print("نشر العقد الذكي...")
        contract_address, abi = deploy_contract()
        print(f"Contract deployed at: {contract_address}")
        print("احفظ هذا العنوان في .env.blockchain كقيمة AAAC_CONTRACT_ADDRESS")
    else:
        # تحميل ABI من الملف المترجم سابقًا أو إعادة ترجمته
        abi, _ = compile_contract()
        print(f"Using existing contract at {contract_address}")

    # ربط آخر حلقة
    chain_data = json.loads(Path("tools/innocence_chain.json").read_text())
    last_ring = chain_data["rings"][-1]
    ring_hash = last_ring["ring_hash"]
    chain_id = last_ring["chain_id"]

    tx_hash = anchor_ring(contract_address, abi, ring_hash, chain_id)
    print(f"Anchored ring {ring_hash[:16]}... with tx: {tx_hash}")
