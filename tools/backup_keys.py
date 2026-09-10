#!/usr/bin/env python3
"""
EnterpriseGuard - Key Backup System using age
Encrypts signing keys with age for secure backup.

Requirements:
    - age installed (https://github.com/FiloSottile/age)
    - age-keygen for key generation

Usage:
    # Generate a new backup key
    age-keygen -o ~/.enterpriseguard/backup_key.txt

    # Backup keys
    python3 tools/backup_keys.py --backup

    # Restore keys
    python3 tools/backup_keys.py --restore --backup-file <file>
"""

import os
import sys
import subprocess
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
KEYS_DIR = Path.home() / ".enterpriseguard" / "keys"
BACKUP_DIR = ROOT / "backups" / "keys_encrypted"

FILES_TO_BACKUP = [
    "private_key.pem",
    "public_key.pem",
    "genesis_private_key.pem",
    "genesis_public_key.pem",
]

# ECDSA keys (if they exist)
ECDSA_FILES = [
    "ecdsa/private_key.pem",
    "ecdsa/public_key.pem",
    "ecdsa/genesis_private_key.pem",
    "ecdsa/genesis_public_key.pem",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(message: str, status: str = "success") -> None:
    """Log backup events to activity_log.json."""
    try:
        sys.path.insert(0, str(ROOT))
        from tools.audit_chain import append_activity

        append_activity(
            {
                "timestamp": utc_now(),
                "activity_type": "key_backup",
                "status": status,
                "details": message,
            },
            ROOT / "tools" / "activity_log.json",
        )
    except Exception as e:
        print(f"WARNING: Failed to log event: {e}", file=sys.stderr)


def check_age_installed() -> bool:
    """Check if age is installed."""
    return shutil.which("age") is not None


def get_backup_recipient() -> str:
    """Get the age public key for encryption."""
    backup_key_file = Path.home() / ".enterpriseguard" / "backup_key.txt"
    if not backup_key_file.exists():
        raise FileNotFoundError(
            f"Backup key not found at {backup_key_file}.\n"
            "Generate one with: age-keygen -o ~/.enterpriseguard/backup_key.txt"
        )

    content = backup_key_file.read_text()
    for line in content.splitlines():
        line = line.strip()
        # البحث عن السطر الذي يحتوي على "public key:"
        if "public key:" in line.lower():
            parts = line.split(":", 1)
            if len(parts) > 1:
                key = parts[1].strip()
                if key.startswith("age1"):
                    return key
        # إذا كان السطر يبدأ بـ age1 مباشرة
        if line.startswith("age1"):
            return line

    raise ValueError("No age public key found in backup_key.txt")


def encrypt_with_age(data: bytes, recipient: str) -> bytes:
    """Encrypt data using age."""
    proc = subprocess.run(
        ["age", "--encrypt", "--recipient", recipient],
        input=data,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def decrypt_with_age(data: bytes) -> bytes:
    """Decrypt data using age (requires identity file)."""
    identity_file = Path.home() / ".enterpriseguard" / "backup_key.txt"
    if not identity_file.exists():
        raise FileNotFoundError(f"Identity file not found: {identity_file}")

    proc = subprocess.run(
        ["age", "--decrypt", "--identity", str(identity_file)],
        input=data,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def backup_keys() -> dict:
    """Encrypt and backup all keys."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now().replace(":", "-").replace("T", "_")[:19]

    recipient = get_backup_recipient()
    results = {"backed_up": [], "missing": [], "failed": []}

    all_files = []
    for f in FILES_TO_BACKUP:
        all_files.append(KEYS_DIR / f)
    for f in ECDSA_FILES:
        all_files.append(KEYS_DIR / f)

    for src in all_files:
        if not src.exists():
            results["missing"].append(str(src))
            continue

        try:
            data = src.read_bytes()
            encrypted = encrypt_with_age(data, recipient)

            rel_path = str(src.relative_to(KEYS_DIR)).replace("/", "_")
            dst = BACKUP_DIR / f"{rel_path}.{timestamp}.age"
            dst.write_bytes(encrypted)
            results["backed_up"].append(str(dst))

        except Exception as e:
            results["failed"].append(f"{src}: {e}")

    manifest = {
        "timestamp": utc_now(),
        "recipient": recipient,
        "files": results,
        "backup_dir": str(BACKUP_DIR),
        "command": "python3 tools/backup_keys.py --backup",
    }
    manifest_path = BACKUP_DIR / f"manifest_{timestamp}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    log_event(f"Key backup completed: {len(results['backed_up'])} files")

    return results


def restore_keys(backup_file: Path) -> dict:
    """Restore keys from an encrypted backup file."""
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    stem = backup_file.stem
    if ".age" in backup_file.suffixes:
        stem = stem.replace(".age", "")

    if "_" in stem and stem.split("_")[-1].replace("-", "").isdigit():
        original_name = "_".join(stem.split("_")[:-1])
    else:
        original_name = stem

    target = KEYS_DIR / original_name
    target.parent.mkdir(parents=True, exist_ok=True)

    data = backup_file.read_bytes()
    decrypted = decrypt_with_age(data)
    target.write_bytes(decrypted)

    log_event(f"Key restored: {target}")

    return {"restored": str(target)}


def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Key Backup")
    parser.add_argument(
        "--backup", action="store_true", help="Backup keys using age"
    )
    parser.add_argument(
        "--restore", metavar="FILE", help="Restore keys from backup file"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available backups"
    )
    args = parser.parse_args()

    if not check_age_installed():
        print("ERROR: age is not installed.", file=sys.stderr)
        print("Install from: https://github.com/FiloSottile/age", file=sys.stderr)
        return 1

    if args.list:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backups = sorted(BACKUP_DIR.glob("*.age"))
        if not backups:
            print("No backups found.")
        else:
            print(f"Backups in {BACKUP_DIR}:")
            for b in backups:
                print(f"  {b.name} ({b.stat().st_size} bytes)")
        return 0

    if args.backup:
        results = backup_keys()
        print(json.dumps(results, indent=2))
        return 1 if results["failed"] else 0

    if args.restore:
        result = restore_keys(Path(args.restore))
        print(json.dumps(result, indent=2))
        return 0

    parser.print_usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
