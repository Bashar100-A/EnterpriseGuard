# Recipe 01 — Bank Credit Decision

**Scenario:** Record an AI credit decision as a signed, tamper-evident proof.

## Steps

```bash
# 1. Initialize identity and seed (once per machine)
python3 tools/hardware_identity.py --generate
python3 tools/genesis_seed.py --seed "bank-credit-2026"

# 2. Initialize SIBB storage
python3 tools/sibb_cli.py init --path .sibb --immutable

# 3. Record the decision
python3 tools/sibb_cli.py write credit-decision-001.txt --data "applicant=ABC123; score=720; decision=approve; amount=50000"

# 4. Verify integrity
python3 tools/sibb_cli.py verify

# 5. Generate the innocence ring
python3 tools/innocence_chain.py --generate

# 6. Confirm the chain is valid
python3 tools/innocence_chain.py --verify
```

**Result:** The decision is stored in WORM storage and anchored in
the signed innocence chain. Any later modification breaks the chain.
