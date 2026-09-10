# Component: sibb_cli.py

**Path:** `tools/sibb_cli.py`
**Version:** 1.1
**Purpose:** Unified CLI for SIBB storage and key management.
**Status:** Working (17/17 tests passed)

---

## What It Does

Single-command interface for storage, distributed nodes, and key management.
Secure input handling (getpass, env vars), strict filename validation,
no shell command execution, audit logging.

## Commands

| Command | Purpose |
|---------|---------|
| init | Initialize local or distributed SIBB |
| write | Write data to storage |
| read | Read data from storage |
| list | List stored files |
| verify | Verify integrity |
| status | Show storage status |
| generate-master-key | Generate 32-byte master key |
| split-key | Split into Shamir shares |
| reconstruct-key | Reconstruct from shares |
| list-shares | List share files |
| delete-share | Delete a share |
| verify-share | Verify a share |

## Inputs

- Command-line arguments via argparse
- Password via SIBB_PASSWORD env or getpass
- Access key via SIBB_ACCESS_KEY env

## Outputs

- Depends on command: printed output, files, or status JSON

## Key Functions

| Function | Purpose |
|----------|---------|
| validate_filename() | Reject path traversal, special chars |
| get_password_from_env_or_prompt() | Secure password input |
| load_config() | Read ~/.enterpriseguard/config.json |
| save_config() | Atomic config write with 0600 |
| run_init() | Initialize storage |
| run_write() | Write command handler |
| run_read() | Read command handler |
| run_verify() | Verify chain |
| run_status() | Status command |
| run_split_key() | Key splitting |
| run_reconstruct_key() | Key reconstruction |

## Security

- Passwords: env var (preferred) or getpass (no echo)
- Filenames: reject `..`, `/`, `~`, control chars, shell metacharacters
- Config: chmod 0600
- No shell execution (subprocess with fixed args only)
- Audit logging on all mutating operations
- Secrets scrubbed from error messages

## Config File

- Path: ~/.enterpriseguard/config.json (chmod 0600)
- Contents: storage_path, distributed, paths, quorum, encrypt, shares_dir

## Exit Codes

- 0: success
- 1: error
- 130: keyboard interrupt

## Tests

- tests/test_sibb_cli.py (17 tests, passing)

## Used By

- End users via terminal
- Scripts and automation

**End of Component Doc**
