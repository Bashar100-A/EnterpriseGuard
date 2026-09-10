#!/usr/bin/env python3
"""EnterpriseGuard Genesis Seed Generator.

Generates the inherited-proof genesis hash from an external seed,
bound to the hardware identity key.

Formula:
    genesis_hash = sha256(external_seed + identity_key)

The hash is intentionally time-independent so that it can be
independently verified by a third party. The generation timestamp
is stored separately in the output JSON.

Priority for external_seed:
    1. genesis_seed.txt
    2. git rev-parse HEAD
    3. manual --seed

Requires tools/hardware_identity.json to exist.
"""

from __future__ import annotations

import sys

# Must be set before any other imports.
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "genesis_seed.txt"
IDENTITY_PATH = ROOT / "tools" / "hardware_identity.json"
OUTPUT_PATH = ROOT / "tools" / "genesis_baseline.json"


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 Z format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_seed_from_file(seed_file: Path) -> str | None:
    """Read the first non-empty line from the seed file."""
    if not seed_file.exists():
        return None
    try:
        for line in seed_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    except OSError:
        return None
    return None


def get_seed_from_git(repo_root: Path) -> str | None:
    """Get the current Git commit hash if available."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def read_identity_key(identity_path: Path) -> str:
    """Read the hardware identity key from the identity JSON."""
    if not identity_path.exists():
        raise FileNotFoundError(
            "hardware_identity.json not found. Run hardware_identity.py --generate first."
        )
    data = json.loads(identity_path.read_text(encoding="utf-8"))
    key = data.get("identity_key")
    if not key:
        raise ValueError("hardware_identity.json missing identity_key")
    return key


def generate_genesis_hash(external_seed: str, identity_key: str) -> str:
    """Return sha256(external_seed + identity_key).

    Deliberately time-independent so the hash can be independently
    verified by any party with the same seed and identity key.
    """
    combined = f"{external_seed}:{identity_key}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def write_genesis_baseline(
    genesis_hash: str,
    source: str,
    identity_key: str,
    output_path: Path,
) -> None:
    """Atomically write genesis_baseline.json with chmod 444."""
    payload = {
        "schema_version": "1.0",
        "genesis_hash": genesis_hash,
        "source": source,
        "identity_key": identity_key,
        "generated_at": utc_now_iso(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".genesis_baseline.",
        suffix=".tmp",
        dir=str(output_path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(tmp, 0o444)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def log_genesis_event(genesis_hash: str, source: str) -> None:
    """Append genesis event to activity log, warning on failure."""
    try:
        sys.path.insert(0, str(ROOT))
        from tools.audit_chain import append_activity
        from tools.time_utils import utc_now

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "genesis_seed",
                "status": "success",
                "details": f"genesis_generated source={source} hash={genesis_hash[:16]}...",
            },
            ROOT / "tools" / "activity_log.json",
        )
    except Exception as exc:
        print(f"WARNING: failed to log genesis event: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Genesis Seed Generator")
    parser.add_argument(
        "--seed",
        type=str,
        default=None,
        help="Manually provide an external seed (overrides file and Git)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting an existing genesis_baseline.json",
    )
    args = parser.parse_args()

    if not IDENTITY_PATH.exists():
        print(
            "ERROR: hardware_identity.json not found. "
            "Run hardware_identity.py --generate first.",
            file=sys.stderr,
        )
        return 1

    if OUTPUT_PATH.exists() and not args.force:
        print(
            "ERROR: genesis_baseline.json already exists. "
            "Use --force to override.",
            file=sys.stderr,
        )
        return 1

    try:
        identity_key = read_identity_key(IDENTITY_PATH)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.seed:
        seed = args.seed.strip()
        source = "manual_cli"
    else:
        file_seed = get_seed_from_file(SEED_FILE)
        if file_seed:
            seed = file_seed
            source = "genesis_seed.txt"
        else:
            git_seed = get_seed_from_git(ROOT)
            if git_seed:
                seed = git_seed
                source = "git_rev_parse_HEAD"
            else:
                print(
                    "ERROR: no seed available. Create genesis_seed.txt or pass --seed.",
                    file=sys.stderr,
                )
                return 1

    if not seed:
        print("ERROR: seed is empty.", file=sys.stderr)
        return 1

    genesis_hash = generate_genesis_hash(seed, identity_key)
    write_genesis_baseline(genesis_hash, source, identity_key, OUTPUT_PATH)
    log_genesis_event(genesis_hash, source)

    print(f"genesis_hash: {genesis_hash}")
    print(f"source: {source}")
    print(f"output: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
