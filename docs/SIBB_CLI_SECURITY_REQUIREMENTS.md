# SIBB Command Line Interface — Security Requirements Document (SRD)

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB CLI (`tools/sibb_cli.py`)  
**Version:** 1.1  
**Status:** Revised after security review  
**Date:** 2026-09-08  
**Methodology:** OWASP ASVS 4.0, NIST SP 800-218, STRIDE

---

## 1. Introduction

This document defines the security requirements for the SIBB Command Line Interface (CLI). The CLI is the primary user-facing tool for managing SIBB storage, distributed nodes, and key management operations. It must provide a secure, consistent, and auditable interface to all SIBB components while preventing misuse, data leaks, and unauthorized actions.

This version incorporates improvements based on a deep security review, including stricter password handling, input validation, error management, audit logging, and mandatory encryption for sensitive data.

---

## 2. Assets to Protect

| Asset | Description | Criticality |
|-------|-------------|-------------|
| **Stored Data** | Files and shares managed via CLI | High |
| **Credentials** | Passwords, access keys, HMAC keys entered or used by CLI | Critical |
| **Configuration** | Paths, node locations, encryption settings | Medium |
| **Audit Logs** | Records of CLI operations | Medium |
| **SIBB Components** | Underlying modules (`sibb_storage`, `sibb_distributed`, `sibb_keys`) | High |

---

## 3. Threat Actors

| Actor | Description | Capabilities |
|-------|-------------|--------------|
| **Local User** | Authorized user executing CLI commands | May make mistakes or attempt unauthorized actions |
| **Malicious User** | Unauthorized user with shell access | Attempt to read/write/delete sensitive data, exploit command injection |
| **Compromised Process** | Malicious code running under same user | Interfere with CLI arguments, environment variables, or output |
| **Remote Attacker** | Not applicable (CLI is local), but if used over SSH, network attacks | Intercept keystrokes, manipulate terminal |

---

## 4. Security Properties (CIA + Non-Repudiation)

- **Confidentiality:** Sensitive inputs (passwords, keys) must not be echoed, logged, or stored insecurely.
- **Integrity:** CLI commands must not alter data without proper validation and authorization.
- **Availability:** The CLI must operate reliably and not cause data loss or corruption.
- **Non-Repudiation:** All mutating CLI actions must be logged to the audit chain with sufficient detail (excluding secrets).

---

## 5. Functional Requirements (FR)

- **FR-1:** The CLI shall support the following commands:
  - `init` – Initialize a local SIBB storage or distributed nodes.
  - `write` – Write data to SIBB storage.
  - `read` – Read data from SIBB storage.
  - `list` – List stored files.
  - `verify` – Verify integrity of storage.
  - `status` – Show storage status.
  - `generate-master-key` – Generate a new random master key (32 bytes) and print it securely (or store it encrypted).
  - `split-key` – Split a provided master key into encrypted shares.
  - `reconstruct-key` – Reconstruct a master key from shares.
  - `list-shares` – List share files.
  - `delete-share` – Delete a share securely.
  - `verify-share` – Verify integrity of a share.
- **FR-2:** All commands must accept a `--help` option and provide clear usage.
- **FR-3:** Sensitive parameters (password, access key) must be provided via environment variables or interactive prompt; they must not appear in command-line arguments or shell history.
- **FR-4:** The CLI must validate all input paths and filenames to prevent path traversal and command injection. Specifically:
  - Reject any filename containing control characters, leading dash (`-`), or special shell metacharacters (`;`, `|`, `$`, `\`, `&`, `<`, `>`, newline, null).
  - Use `argparse` with `allow_abbrev=False` to avoid ambiguity.
  - Never pass user-supplied filenames to `subprocess` or `os.system`.
- **FR-5:** The CLI must use the underlying components securely (e.g., pass `access_key` correctly, use `use_os_immutable` when needed).
- **FR-6:** The CLI must return non-zero exit codes on errors and zero on success.
- **FR-7:** The CLI must support configuration via a JSON file (default `~/.enterpriseguard/config.json`) and environment variables for common settings (paths, encryption, quorum). Configuration files must have permissions `0600`.
- **FR-8:** The CLI must not expose secrets in error messages or logs.
- **FR-9:** The CLI should require minimum privileges; it should not require root unless absolutely necessary (e.g., `chattr` on Linux). If `chattr` is needed, the user must be informed and asked for explicit consent.
- **FR-10:** All temporary files created by the CLI must be created with permissions `0600`, placed in a secure temporary directory, and deleted after use even in case of error.

---

## 6. Security Requirements (SR)

- **SR-1:** All file paths must be canonicalized and validated before use; symlinks are prohibited in storage directories.
- **SR-2:** Passwords must be read using `getpass.getpass()` (or equivalent) to avoid echoing. Access keys may be read from environment variables (`SIBB_ACCESS_KEY`). Passwords must not be accepted as command-line arguments.
- **SR-3:** The CLI must not log passwords or decrypted data. Error messages and logs must be scrubbed of secrets before output.
- **SR-4:** The CLI must perform access control checks inherited from underlying modules; any failure must result in a generic error message and non-zero exit.
- **SR-5:** The CLI must avoid command injection by:
  - Using `subprocess` only with fixed arguments and `shell=False`.
  - Never calling `os.system` or `shell=True`.
  - Validating all user input before use.
- **SR-6:** All mutating operations (init, write, delete-share, split-key, reconstruct-key, delete-share) must be logged via `append_activity` with relevant details (excluding secrets). If `append_activity` fails, the CLI must continue but emit a warning and still complete the operation.
- **SR-7:** The CLI must handle exceptions gracefully, without printing stack traces to the console. Detailed errors may be written to a log file with permissions `0600` (default `~/.enterpriseguard/logs/cli.log`), but must not contain secrets.
- **SR-8:** The CLI must enforce that `master_key` or shares are not stored in plaintext. Encryption must be enabled by default for key splitting and storage of sensitive data. If encryption is explicitly disabled, the user must receive a warning and confirm.
- **SR-9:** Sensitive data in memory (passwords, keys, decrypted shares) must be zeroized as soon as possible using `bytearray` and overwriting before garbage collection.
- **SR-10:** The CLI must reject duplicate filenames and ensure WORM semantics are preserved (e.g., no overwrite allowed).

---

## 7. Constraints and Assumptions

- **Platform:** Linux/macOS/Windows (cross-platform where possible).
- **Dependencies:** Python 3.8+, `cryptography`, `pytest` (for testing).
- **Environment:** The CLI is intended for local use; remote execution via SSH is possible but not a primary target.
- **Integration:** The CLI will import modules from `tools/` (e.g., `sibb_storage`, `sibb_distributed`, `sibb_keys`). It must not require changes to protected directories.
- **Audit:** `append_activity` must be called; if unavailable, the CLI should degrade gracefully with a warning.
- **Configuration:** Default config file `~/.enterpriseguard/config.json`; supported environment variables: `SIBB_PASSWORD`, `SIBB_ACCESS_KEY`, `SIBB_CONFIG_PATH`.

---

## 8. Acceptance Criteria

- All unit tests pass (to be defined in test plan).
- No High or Medium findings in Bandit.
- All commands function correctly with valid inputs.
- Invalid inputs and security violations are rejected with appropriate errors and non-zero exit codes.
- Secrets are not exposed in logs, error messages, or shell history.
- Audit logging is functional for all mutating operations.
- Passwords are not visible on screen or in process lists.
- Command injection attacks via filenames are blocked.
- Encryption is enforced for sensitive operations by default.

---

## 9. Next Steps

1. **Threat Model (STRIDE)** – Analyze threats specific to the CLI.
2. **Test Plan** – Define unit tests for each command and security scenario.
3. **Code Implementation** – Write `tools/sibb_cli.py` to meet these requirements.
4. **Run Tests and Static Analysis** – Bandit and pytest.
5. **Documentation** – Record decision (e.g., DC-125).

---

**End of Security Requirements Document v1.1**
