# EnterpriseGuard — Quick Start

**Goal:** Record and verify a decision in under 10 steps.

**Requirements:** Python 3.12+, git, Linux or macOS.

## Steps

**1. Clone the repository**
    git clone https://github.com/Bashar100-A/EnterpriseGuard.git
    cd EnterpriseGuard

**2. Create and activate a virtual environment**
    python3 -m venv .venv
    source .venv/bin/activate

**3. Install dependencies**
    pip install -r requirements.txt

**4. Generate hardware identity**
    python3 tools/hardware_identity.py --generate
    Expected: prints identity_key, writes tools/hardware_identity.json (0600).
    Note: if file exists, use --regenerate --confirm REGEN or --generate --force.

**5. Generate genesis seed**
    python3 tools/genesis_seed.py --seed "my-first-seed"
    Expected: writes tools/genesis_baseline.json (0444).

**6. Initialize SIBB storage**
    python3 tools/sibb_cli.py init --path .sibb
    Expected: storage directory created.

**7. Write a test decision**
    python3 tools/sibb_cli.py write hello.txt --data "first-decision"

**8. Read it back**
    python3 tools/sibb_cli.py read hello.txt
    Expected: prints first-decision.

**9. Verify storage integrity**
    python3 tools/sibb_cli.py verify
    Expected: integrity confirmation.

**10. Show status**
    python3 tools/sibb_cli.py status

## Success

If steps 1-10 complete without errors, the core storage layer is working.
For cryptographic signing and decision verification, see docs/COMPONENTS/.
