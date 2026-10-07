"""Bridge: canonical ADIE governance -> 3A wire/crypto artifacts.

Direction: enterpriseguard.adie -> protocol  (one way, mandatory).

protocol/ MUST NOT import enterpriseguard.adie.
"""
from __future__ import annotations

from typing import Any


class WireBridgeError(Exception):
    pass


def envelope_from_certificate(cert: dict) -> bytes:
    """Wrap a DCP 2.1 certificate (semantic JSON) into a B+ envelope.

    Uses the frozen 3A reference path via protocol/wire/bin/... binary
    subprocess (Python endpoint). This is a thin, explicit bridge.
    """
    import json
    import subprocess
    from pathlib import Path

    here = Path(__file__).resolve()
    repo_root = here.parents[4]  # src/enterpriseguard/adie/canonical/wire_bridge.py -> repo
    bin_ = repo_root / "protocol" / "wire" / "bin" / "adie-cbor-envelope.py"
    if not bin_.exists():
        raise WireBridgeError(f"missing bridge binary: {bin_}")
    p = subprocess.run(
        [str(repo_root / ".venv" / "bin" / "python"), str(bin_)],
        input=json.dumps({"op": "build", "certificate_json": json.dumps(cert)}),
        capture_output=True, text=True, timeout=30, cwd=str(repo_root),
    )
    try:
        out = json.loads(p.stdout.strip())
    except Exception as e:
        raise WireBridgeError(f"bridge parse: {e}; stdout={p.stdout[:200]}") from e
    if "envelope_hex" not in out:
        raise WireBridgeError(f"bridge build failed: {out}")
    return bytes.fromhex(out["envelope_hex"])


def parse_envelope_to_certificate(envelope: bytes) -> dict:
    import json
    import subprocess
    from pathlib import Path

    here = Path(__file__).resolve()
    repo_root = here.parents[4]
    bin_ = repo_root / "protocol" / "wire" / "bin" / "adie-cbor-envelope.py"
    p = subprocess.run(
        [str(repo_root / ".venv" / "bin" / "python"), str(bin_)],
        input=json.dumps({"op": "parse", "envelope_hex": envelope.hex()}),
        capture_output=True, text=True, timeout=30, cwd=str(repo_root),
    )
    try:
        out = json.loads(p.stdout.strip())
    except Exception as e:
        raise WireBridgeError(f"bridge parse: {e}") from e
    if "certificate_json" not in out:
        raise WireBridgeError(f"bridge parse failed: {out}")
    return json.loads(out["certificate_json"])


__all__ = ["WireBridgeError", "envelope_from_certificate", "parse_envelope_to_certificate"]
