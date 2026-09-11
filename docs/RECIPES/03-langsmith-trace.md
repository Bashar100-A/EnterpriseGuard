# Recipe 03 — Record a LangSmith Trace

**Scenario:** Pull runs from LangSmith and record them as proof.

## Prerequisites

```bash
export LANGSMITH_API_KEY="lsv2_pt_..."
export LANGSMITH_PROJECT="my-project"
export AAAC_TRACE_SOURCE="langsmith"
```

## Steps

```bash
# 1. Initialize identity and SIBB (once per machine)
python3 tools/hardware_identity.py --generate
python3 tools/genesis_seed.py --seed "langsmith-2026"
python3 tools/sibb_cli.py init --path .sibb --immutable

# 2. Fetch runs via the unified connector
python3 -c "from tools.native_connectors import unified_fetch; print(unified_fetch(source='langsmith', limit=10))"

# 3. Generate a new innocence ring
python3 tools/innocence_chain.py --generate

# 4. Verify the chain
python3 tools/innocence_chain.py --verify
```

**Result:** LangSmith runs become AAAC events that are stored and signed.
