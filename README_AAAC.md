# AAAC — Agentic Accountability & Audit Core

AAAC is a proof layer that attaches verifiable, tamper-evident records to AI agent traces from LangSmith or Langfuse.

## Components

- `tools/native_connectors.py` — Fetches traces from LangSmith/Langfuse.
- `tools/aaac_cli.py` — Unified CLI: fetch → store → generate ring → verify.
- `tools/innocence_chain.py` — Hash chain with digital signatures and RFC3161 timestamps.
- `tools/sovereign_http_server.py` — HTTP API with `/events`, `/agents`, `/verify-chain`, `/dashboard`, `/compliance-report`.
- `tools/open_verifier.py` — Public verifier (MIT) that checks chain integrity.

## Quick Start

1. Clone the repository.
2. Install dependencies: `pip install -r tools/requirements.lock.txt`
3. Configure environment variables:
   - For Langfuse: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`
   - For LangSmith: `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`
   - Set `AAAC_TRACE_SOURCE` to `auto`, `langfuse`, or `langsmith`.
4. Run the pipeline:
   ```bash
   set -a; source .env; set +a
   python3 tools/aaac_cli.py
