#!/usr/bin/env python3
"""Encrypt and decrypt hardware identity data with OpenSSL."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import HARDWARE_IDENTITY_PATH


KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "identity_encryption_key.key"
DEFAULT_OUTPUT_PATH = HARDWARE_IDENTITY_PATH.with_suffix(".enc")
OPENSSL_ARGS = ["enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt"]


def _prepare_key() -> None:
    """Require the configured key and restrict its permissions."""
    if not KEY_PATH.exists():
        raise FileNotFoundError(f"Encryption key not found: {KEY_PATH}")
    os.chmod(KEY_PATH, 0o600)


def _run_openssl(input_path: Path, output_path: Path | None = None, decrypt: bool = False) -> None:
    _prepare_key()
    command = ["openssl", *OPENSSL_ARGS]
    if decrypt:
        command.append("-d")
    command.extend(["-pass", f"file:{KEY_PATH}", "-in", str(input_path)])
    if output_path is not None:
        command.extend(["-out", str(output_path)])
    subprocess.run(command, check=True)


def _temporary_path(directory: Path) -> tuple[Path, tempfile.NamedTemporaryFile]:
    directory.mkdir(parents=True, exist_ok=True)
    temporary_file = tempfile.NamedTemporaryFile(
        mode="wb", dir=directory, prefix=".identity_encryption_", delete=False
    )
    return Path(temporary_file.name), temporary_file


def encrypt_identity(output: Path = DEFAULT_OUTPUT_PATH) -> Path:
    """Encrypt HARDWARE_IDENTITY_PATH into output atomically."""
    output = Path(output)
    temporary_path, temporary_file = _temporary_path(output.parent)
    temporary_file.close()
    try:
        _run_openssl(HARDWARE_IDENTITY_PATH, temporary_path)
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)
    return output


def decrypt_identity(output: Path | None = None) -> None:
    """Decrypt the default encrypted identity to a file or stdout."""
    input_path = DEFAULT_OUTPUT_PATH
    if output is None:
        _run_openssl(input_path)
        return

    output = Path(output)
    temporary_path, temporary_file = _temporary_path(output.parent)
    temporary_file.close()
    try:
        _run_openssl(input_path, temporary_path, decrypt=True)
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--encrypt", action="store_true", help="Encrypt hardware_identity.json")
    mode.add_argument("--decrypt", action="store_true", help="Decrypt hardware_identity.enc")
    parser.add_argument("--output", type=Path, help="Output file; decrypt defaults to stdout")
    args = parser.parse_args()

    try:
        if args.encrypt:
            encrypt_identity(args.output or DEFAULT_OUTPUT_PATH)
        else:
            decrypt_identity(args.output)
    except (FileNotFoundError, OSError, subprocess.CalledProcessError) as exc:
        print(f"identity encryption failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
