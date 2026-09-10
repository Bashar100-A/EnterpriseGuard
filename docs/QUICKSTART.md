# EnterpriseGuard — Quick Start

**Goal:** Record and verify a decision in under 10 steps.

```bash
# 1. Clone
git clone <repo-url> && cd EnterpriseGuard

# 2. Create and activate venv
python3 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate hardware identity
python3 tools/hardware_identity.py --generate

# 5. Generate genesis seed
python3 tools/genesis_seed.py --seed "my-first-seed"

# 6. Initialize SIBB storage
python3 tools/sibb_cli.py init --path .sibb --immutable

# 7. Write a test decision
python3 tools/sibb_cli.py write hello.txt --data "first-decision"

# 8. Read it back
python3 tools/sibb_cli.py read hello.txt

# 9. Verify storage integrity
python3 tools/sibb_cli.py verify

# 10. Show status
python3 tools/sibb_cli.py status
