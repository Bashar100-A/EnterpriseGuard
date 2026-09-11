# Recipe 02 — Record a Langfuse Trace

**Scenario:** Pull observations from Langfuse and record them as proof.

## Prerequisites

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

## Steps

```bash
# 1. Initialize identity and SIBB (once per machine)
python3 tools/hardware_identity.py --generate
python3 tools/genesis_seed.py --seed "langfuse-2026"
python3 tools/sibb_cli.py init --path .sibb --immutable

# 2. Fetch observations from Langfuse and store them
python3 tools/aaac_connector.py

# 3. Generate a new innocence ring from the stored events
python3 tools/innocence_chain.py --generate

# 4. Verify the chain
python3 tools/innocence_chain.py --verify
```

**Result:** Every Langfuse observation is normalized into an AAAC event,
stored in WORM storage, and included in the signed innocence chain.
