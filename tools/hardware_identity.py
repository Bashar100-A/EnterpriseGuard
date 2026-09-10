#!/usr/bin/env python3
"""EnterpriseGuard Hardware Identity Generator.

Generates a tissue identity key from multiple hardware fingerprints
without ever reading protected directories.

IMPORTANT:
    uuid.getnode() may return the MAC address, which can change when
    the network interface changes or in virtualized environments.
    If the generated identity_key changes unexpectedly, the owner
    must explicitly authorize regeneration using:

        python3 tools/hardware_identity.py --regenerate --confirm REGEN

    and record the event in DECISIONS_LOG.md.
"""

from __future__ import annotations

import sys

# Must be set before any other imports.
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import platform
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDENTITY_PATH = ROOT / "tools" / "hardware_identity.json"


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 Z format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_machine_id() -> str:
    """Return systemd machine-id if available, otherwise empty string.

    Only reads system paths, never protected directories.
    """
    candidates = [
        Path("/etc/machine-id"),
        Path("/var/lib/dbus/machine-id"),
    ]
    for path in candidates:
        try:
            if path.exists():
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    return text
        except OSError:
            continue
    return ""


def generate_identity_key() -> str:
    """Return sha256 of multiple hardware fingerprints."""
    parts = [
        str(uuid.getnode()),
        platform.processor() or "",
        platform.machine() or "",
        str(os.cpu_count() or 0),
        get_machine_id(),
    ]
    combined = "|".join(parts).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def write_identity_file(identity_key: str, regenerated: bool = False) -> None:
    """Atomically write identity JSON with chmod 600."""
    payload = {
        "schema_version": "1.0",
        "identity_key": identity_key,
        "generated_at": utc_now_iso(),
        "regenerated": regenerated,
    }
    IDENTITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".hardware_identity.",
        suffix=".tmp",
        dir=str(IDENTITY_PATH.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, IDENTITY_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def log_identity_event(identity_key: str, action: str) -> None:
    """Append identity event to activity log, warning on failure."""
    try:
        sys.path.insert(0, str(ROOT))
        from tools.audit_chain import append_activity
        from tools.time_utils import utc_now

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "hardware_identity",
                "status": "success",
                "details": f"{action}: {identity_key[:16]}...",
            },
            ROOT / "tools" / "activity_log.json",
        )
    except Exception as exc:
        print(f"WARNING: failed to log identity event: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Hardware Identity Generator")
    parser.add_argument("--generate", action="store_true", help="Generate identity key (fails if already exists)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --generate to overwrite an existing identity key",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate identity key (requires --confirm REGEN)",
    )
    parser.add_argument(
        "--confirm",
        type=str,
        default=None,
        help="Confirmation string 'REGEN' to explicitly allow regeneration",
    )
    args = parser.parse_args()

    if args.generate:
        if IDENTITY_PATH.exists() and not args.force:
            print(
                "ERROR: hardware_identity.json already exists. "
                "Use --regenerate --confirm REGEN to replace it, or --generate --force to override.",
                file=sys.stderr,
            )
            return 1
        identity_key = generate_identity_key()
        write_identity_file(identity_key, regenerated=False)
        log_identity_event(identity_key, "identity_generated")
        print(f"identity_key: {identity_key}")
        print(f"output: {IDENTITY_PATH}")
        return 0

    if args.regenerate:
        if args.confirm != "REGEN":
            print("ERROR: --regenerate requires --confirm REGEN", file=sys.stderr)
            return 1
        identity_key = generate_identity_key()
        write_identity_file(identity_key, regenerated=True)
        log_identity_event(identity_key, "identity_regenerated")
        print(f"identity_key: {identity_key}")
        print(f"output: {IDENTITY_PATH}")
        return 0

    parser.print_usage(sys.stderr)
    print("error: one of --generate or --regenerate is required", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())