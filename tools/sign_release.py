#!/usr/bin/env python3
"""EnterpriseGuard Release Signing Tool.

Signs critical project files with GPG and verifies signatures.
Uses detached ASCII armor signatures (.asc) and refuses to touch
protected directories in both signing and verification modes.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

CRITICAL_FILES = [
    "tools/TRUSTED_BASELINE.json",
    "TRUSTED_BASELINE_SENTINEL.json",
    "tools/integrity_baseline.json",
    "integrity_baseline_sentinel.json",
    "VERSION",
    "CHANGELOG.md",
]

PROTECTED_PARTS = {"adie", "intelligence"}


def is_protected(path: Path) -> bool:
    """Return True if the path is under any protected directory."""
    return any(part in PROTECTED_PARTS for part in path.parts)


def run_gpg(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a GPG command and return exit code, stdout, stderr."""
    result = subprocess.run(
        ["gpg", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def ensure_gpg_available() -> bool:
    """Return True if GPG is installed and accessible."""
    return shutil.which("gpg") is not None


def sign_file(file_path: Path) -> None:
    """Sign a file with a detached ASCII armor signature."""
    if is_protected(file_path):
        print(f"REFUSING to sign protected file: {file_path}", file=sys.stderr)
        return
    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return

    sig_path = Path(f"{file_path}.asc")
    code, stdout, stderr = run_gpg([
        "--yes",
        "--batch",
        "--pinentry-mode", "loopback",
        "--armor",
        "--detach-sign",
        "--output", str(sig_path),
        str(file_path),
    ])
    if code != 0:
        print(f"Failed to sign {file_path}: {stderr}", file=sys.stderr)
    else:
        print(f"Signed: {sig_path}")


def verify_file(file_path: Path) -> bool:
    """Verify a detached ASCII armor signature."""
    if is_protected(file_path):
        print(f"REFUSING to verify protected file: {file_path}", file=sys.stderr)
        return False
    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return False

    sig_path = Path(f"{file_path}.asc")
    if not sig_path.exists():
        print(f"Signature not found for {file_path}", file=sys.stderr)
        return False

    code, stdout, stderr = run_gpg([
        "--batch",
        "--verify",
        str(sig_path),
        str(file_path),
    ])
    if code == 0:
        print(f"Verified OK: {file_path}")
        return True
    else:
        print(f"Verification failed for {file_path}: {stderr}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Release Signing Tool")
    parser.add_argument("--sign", action="store_true", help="Sign critical files")
    parser.add_argument("--verify", action="store_true", help="Verify critical file signatures")
    args = parser.parse_args()

    if not (args.sign or args.verify):
        parser.print_usage(sys.stderr)
        print("error: one of --sign or --verify is required", file=sys.stderr)
        return 1

    if not ensure_gpg_available():
        print("ERROR: GPG is not installed or not in PATH.", file=sys.stderr)
        return 1

    if args.sign:
        for rel in CRITICAL_FILES:
            sign_file(ROOT / rel)
        return 0

    if args.verify:
        failed = False
        for rel in CRITICAL_FILES:
            if not verify_file(ROOT / rel):
                failed = True
        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())