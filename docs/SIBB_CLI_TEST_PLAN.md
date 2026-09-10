# SIBB Command Line Interface — Test Plan

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB CLI (`tools/sibb_cli.py`)  
**Version:** 1.0  
**Date:** 2026-09-08  
**Reference:** SRD v1.1, Threat Model v1.1

---

## 1. Introduction

This test plan defines the unit and security tests required to validate the SIBB CLI. It covers functional correctness, input validation, password handling, configuration security, audit logging, and resistance to the threats identified in the STRIDE model. All tests must pass before acceptance.

---

## 2. Test Environment

- Python 3.8+
- `pytest`
- `cryptography` (for encryption tests)
- Temporary directories (`tmp_path`) for isolation
- No network access required

---

## 3. Test Cases

### 3.1 Basic Command Execution

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-01 | `--help` for each command | Execute `sibb_cli.py <command> --help` | Exit code 0, usage text displayed |
| CLI-02 | Unknown command | Execute `sibb_cli.py bogus` | Non-zero exit, error message |
| CLI-03 | Missing required argument | Execute `sibb_cli.py write` without filename | Non-zero exit, usage hint |
| CLI-04 | Valid `status` command | Initialize storage, run `status` | Exit 0, JSON status output |

### 3.2 Input Validation and Path Safety

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-05 | Path traversal in filename | `write --filename ../../evil.txt` | Rejected, non-zero exit |
| CLI-06 | Leading dash in filename | `write --filename -foo` | Rejected |
| CLI-07 | Control characters in filename | `write --filename $'bad\x01name'` | Rejected |
| CLI-08 | Shell metacharacters in filename | `write --filename 'file; rm -rf /'` | Rejected |
| CLI-09 | Symlink in storage path | Create symlink in storage dir pointing outside; attempt write through it | Rejected |
| CLI-10 | Duplicate filename (WORM) | Write same filename twice | Second write fails, non-zero exit |

### 3.3 Password and Secret Handling

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-11 | Password not accepted as argument | Try `--password secret` (should be unsupported) | Argument not defined or rejected |
| CLI-12 | Password from environment variable | Set `SIBB_PASSWORD=StrongPass123!`, run split-key | Works without prompting |
| CLI-13 | Password prompt hides input | Simulate `getpass` with monkeypatch, ensure no echo | No visible characters (hard to test; check code uses `getpass`) |
| CLI-14 | Password not in process list | Run command with password via env, check `/proc/<pid>/cmdline` | Password absent |
| CLI-15 | Password not in audit log | After split-key, inspect activity log | No plaintext password |
| CLI-16 | Password not in error messages | Force wrong password, capture stderr | Error does not contain password |

### 3.4 Configuration File Security

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-17 | Config file permissions | Create config file | Permissions are 0600 |
| CLI-18 | Config file missing | Run CLI without config | Uses defaults or prompts; no crash |
| CLI-19 | Config file invalid JSON | Provide malformed JSON | Error handled gracefully, non-zero exit |
| CLI-20 | Config file tampered (HMAC/fingerprint) | If HMAC protection implemented, modify config | Integrity check fails, warning |

### 3.5 Audit Logging

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-21 | `write` operation logged | Perform successful write | Audit event recorded |
| CLI-22 | `delete-share` logged | Delete a share | Audit event recorded |
| CLI-23 | Failed operation logged | Attempt write with invalid path | Audit event recorded with failure |
| CLI-24 | Audit log does not contain secrets | Inspect log after operations involving passwords | No passwords found |

### 3.6 Access Control and Privilege

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-25 | Access key enforcement | Set `SIBB_ACCESS_KEY=secret`, run `status` | Works |
| CLI-26 | Wrong access key | Set `SIBB_ACCESS_KEY=wrong`, run `status` | Fails with access denied |
| CLI-27 | Running as root (if applicable) | Execute with root privileges (simulate) | Warning or refusal unless `--allow-root` |

### 3.7 Underlying Module Integration

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-28 | `write` calls `sibb_storage.write` correctly | Mock `WORMStorage` and check call | Correct parameters passed |
| CLI-29 | `split-key` calls `sibb_keys.split_master_key` | Mock `SIBBKeyManager` | Correct parameters |
| CLI-30 | `verify` calls `verify_integrity` | Mock storage | Correct call |

### 3.8 Denial of Service Mitigations

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-31 | Large file write attempt | Try writing very large data | Either succeeds with warning or is rejected with size limit (if implemented) |
| CLI-32 | Multiple concurrent CLI instances | Run two instances trying to write same file | One succeeds, other fails gracefully |

### 3.9 Error Handling

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-33 | Stack trace not shown | Force an exception (e.g., permission denied) | No traceback on console; generic error |
| CLI-34 | Error logged to file | Same as above | Detailed error in log file, not on screen |

### 3.10 Output Sanitization (ANSI)

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CLI-35 | Filename with ANSI escape sequences | `write --filename $'\x1b[31mred\x1b[0m'` | Rejected or sanitized, no terminal manipulation |
| CLI-36 | Error message with ANSI | Force error with filename containing escape | Output stripped of escapes |

---

## 4. Acceptance Criteria

- All tests pass.
- No High or Medium findings in Bandit on `tools/sibb_cli.py`.
- All commands work with valid inputs.
- Invalid inputs and security violations are rejected with non-zero exit codes.
- Secrets are not exposed in logs, errors, or process lists.
- Audit logging is functional for all mutating operations.
- Passwords are not visible or stored insecurely.
- Command injection and path traversal attempts are blocked.
- Encryption is enforced for sensitive operations by default (if configured).
- Output is sanitized against ANSI escape sequences.

---

## 5. Next Steps

1. **Code Implementation** – Write `tools/sibb_cli.py` to meet this test plan and SRD v1.1.
2. **Run Tests** – Execute the test suite and fix failures.
3. **Static Analysis** – Run Bandit and address findings.
4. **Documentation** – Record decision (e.g., DC-125) and update continuity files.

---

**End of Test Plan**
