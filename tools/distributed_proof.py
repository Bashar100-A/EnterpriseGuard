#!/usr/bin/env python3
"""EnterpriseGuard Distributed Proof Generator.

Generates participatory proof shards from:

    proof_digest = sha256(identity_key + genesis_hash + last_relational_node)

The digest is split into three shards:

- local    -> tools/proof_shard_local.json      (chmod 600)
- external -> EXTERNAL_DIR/proof_shard_external.json (chmod 600)
- physical -> tools/proof_shard_physical.json   (chmod 400)

EXTERNAL_DIR defaults to /var/lib/enterpriseguard/proof_external when
running as root, otherwise falls back to a local external directory
outside the tools folder. In production this must be a separate
physical/private Git location.

Missing any shard means proof reconstruction fails.
"""

from __future__ import annotations

import sys

# Must be set before any other imports.
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IDENTITY_PATH = ROOT / "tools" / "hardware_identity.json"
GENESIS_PATH = ROOT / "tools" / "genesis_baseline.json"
RELATIONAL_PATH = ROOT / "tools" / "relational_memory.json"

LOCAL_SHARD_PATH = ROOT / "tools" / "proof_shard_local.json"
PHYSICAL_SHARD_PATH = ROOT / "tools" / "proof_shard_physical.json"

DEFAULT_EXTERNAL_DIR = (
    Path("/var/lib/enterpriseguard/proof_external")
    if os.geteuid() == 0
    else ROOT.parent / "enterpriseguard_external_proof"
)


def utc_now_iso() -> str:
    """Return current UTC timestamp using project's canonical time util."""
    from tools.time_utils import utc_now

    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json_file(path: Path) -> dict:
    """Read and return JSON content from a file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_identity_key() -> str:
    data = read_json_file(IDENTITY_PATH)
    key = data.get("identity_key")
    if not key:
        raise ValueError("hardware_identity.json missing identity_key")
    return key


def get_genesis_hash() -> str:
    data = read_json_file(GENESIS_PATH)
    genesis_hash = data.get("genesis_hash")
    if not genesis_hash:
        raise ValueError("genesis_baseline.json missing genesis_hash")
    return genesis_hash


def get_last_relational_node_id() -> str:
    """Return last relational event ID, or 'none' if no memory exists."""
    if not RELATIONAL_PATH.exists():
        return "none"
    data = read_json_file(RELATIONAL_PATH)
    nodes = data.get("nodes", []) if isinstance(data, dict) else data
    if not nodes:
        return "none"
    return nodes[-1].get("event_id", "none")


def generate_proof_digest(identity_key: str, genesis_hash: str, last_node_id: str) -> str:
    """Return sha256 of identity + genesis + last relational node."""
    combined = f"{identity_key}:{genesis_hash}:{last_node_id}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def split_digest(digest: str) -> dict:
    """Split a 64-char hex digest into three shards."""
    if len(digest) != 64:
        raise ValueError("Invalid digest length; expected 64 hex characters")
    return {
        "local": digest[:21],
        "external": digest[21:43],
        "physical": digest[43:64],
    }


def write_shard_file(path: Path, shard_name: str, shard_value: str, digest: str, mode: int) -> None:
    """Atomically write one shard file with the given permissions."""
    payload = {
        "schema_version": "1.0",
        "shard_name": shard_name,
        "shard_value": shard_value,
        "proof_digest": digest,
        "created_at": utc_now_iso(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=f".proof_shard_{shard_name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def log_proof_event(digest: str) -> None:
    """Append proof generation event to activity log."""
    try:
        from tools.audit_chain import append_activity
        from tools.time_utils import utc_now

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "distributed_proof",
                "status": "success",
                "details": f"proof_shards_generated digest={digest[:16]}...",
            },
            ROOT / "tools" / "activity_log.json",
        )
    except Exception as exc:
        print(f"WARNING: failed to log proof event: {exc}", file=sys.stderr)


def verify_shards(external_dir: Path) -> bool:
    """Verify that the three shards reconstruct the same digest."""
    try:
        external_path = external_dir / "proof_shard_external.json"
        local = read_json_file(LOCAL_SHARD_PATH)["shard_value"]
        external = read_json_file(external_path)["shard_value"]
        physical = read_json_file(PHYSICAL_SHARD_PATH)["shard_value"]
        reconstructed = local + external + physical
        expected_digest = read_json_file(LOCAL_SHARD_PATH)["proof_digest"]
        return reconstructed == expected_digest
    except Exception as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Distributed Proof")
    parser.add_argument("--generate", action="store_true", help="Generate proof shards")
    parser.add_argument("--verify", action="store_true", help="Verify existing shards")
    parser.add_argument(
        "--external-dir",
        type=Path,
        default=DEFAULT_EXTERNAL_DIR,
        help="Directory for the external proof shard (must be outside tools/)",
    )
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing shards")
    args = parser.parse_args()

    external_dir = args.external_dir
    external_path = external_dir / "proof_shard_external.json"

    # Safety: external dir must not be inside tools/
    if "tools" in external_path.parts:
        print("ERROR: external-dir must not be inside tools/", file=sys.stderr)
        return 1

    if args.generate:
        existing_paths = [
            LOCAL_SHARD_PATH,
            external_path,
            PHYSICAL_SHARD_PATH,
        ]
        if any(path.exists() for path in existing_paths) and not args.force:
            print(
                "ERROR: proof shards already exist. Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1

        try:
            identity_key = get_identity_key()
            genesis_hash = get_genesis_hash()
            last_node_id = get_last_relational_node_id()
            digest = generate_proof_digest(identity_key, genesis_hash, last_node_id)
            shards = split_digest(digest)
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        write_shard_file(LOCAL_SHARD_PATH, "local", shards["local"], digest, 0o600)
        write_shard_file(external_path, "external", shards["external"], digest, 0o600)
        write_shard_file(PHYSICAL_SHARD_PATH, "physical", shards["physical"], digest, 0o400)

        log_proof_event(digest)

        print(f"proof_digest: {digest}")
        print("shards:")
        print(f"  local: {LOCAL_SHARD_PATH}")
        print(f"  external: {external_path}")
        print(f"  physical: {PHYSICAL_SHARD_PATH}")
        return 0

    if args.verify:
        if verify_shards(external_dir):
            print("VERIFIED_OK")
            return 0
        else:
            print("VERIFICATION_FAILED")
            return 1

    parser.print_usage(sys.stderr)
    print("error: one of --generate or --verify is required", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
