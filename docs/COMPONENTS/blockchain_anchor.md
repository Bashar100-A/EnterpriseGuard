# Component: blockchain_anchor.py

**Path:** `tools/blockchain_anchor.py`
**Purpose:** Anchor AAAC ring hashes on Ethereum/Ganache/Sepolia.
**Status:** Working PoC — local Ganache + Sepolia tested.

---

## What It Does
Compiles `Anchor.sol`, deploys it, and writes the latest ring hash.
Provides public, immutable proof-of-existence.

## Inputs
Environment from `.env.blockchain`:
- `AAAC_CHAIN_RPC`
- `AAAC_CHAIN_ID`
- `AAAC_PRIVATE_KEY`
- `AAAC_CONTRACT_ADDRESS`

Chain file:
- `tools/innocence_chain.json`

## Outputs
- Deployed contract address
- Transaction hash for anchored ring

## Key Functions
| Function | Purpose |
|----------|---------|
| `compile_contract()` | Compile `Anchor.sol` |
| `deploy_contract()` | Deploy contract |
| `anchor_ring()` | Anchor `ring_hash` + `chain_id` |

## Security
- Private key read from env, not hardcoded.
- Testnet PoC only; mainnet requires review.
- No key material written to repo.

## Tests
Manual Ganache + Sepolia tests.

## Used By
Optional AAAC anchoring workflow.

**End of Component Doc**
