# SIBB eBPF Protection — Test Plan

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB eBPF Protection Layer  
**Version:** 1.1  
**Date:** 2026-09-08  
**Reference:** SRD v1.1, Threat Model v1.1

---

## 1. Introduction

This test plan defines the unit and integration tests required to validate the eBPF protection layer. It covers functional correctness, blocking capabilities, resilience against advanced attacks (including openat2, io_uring, mmap, hard links, rename exchange, mount namespaces), and performance impact. All tests must be run in a controlled VM or dedicated test machine.

---

## 2. Test Environment

- Linux kernel 5.8+ with eBPF LSM support enabled
- `clang`, `libbpf`, `bpftool`
- Root privileges for loading/unloading programs
- Isolated test directories with sample SIBB files
- A test user account (non-root) and root account
- Systemd service for automatic loading
- `sysbench` or similar for performance benchmarking
- Tools for advanced attacks: `io_uring` test program, `renameat2`, `mount`, `chroot`

---

## 3. Test Cases

### 3.1 Program Loading and Verification

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| LOAD-01 | Compile eBPF program | Run `clang -target bpf` on source | No compilation errors |
| LOAD-02 | Load eBPF program | Use `bpftool prog load` or loader agent | Program loads successfully |
| LOAD-03 | Pass kernel verifier | Check `bpftool prog show` | Program is attached and marked as `loaded` |
| LOAD-04 | Sign and verify eBPF binary | Attempt to load unsigned binary | Unsigned load fails |
| LOAD-05 | Protect eBPF object file | Set `chattr +i` on `.o` file; try to modify as root | Modification denied |
| LOAD-06 | Modify signed binary or signature and load | Replace eBPF binary or signature with altered version | Load fails due to signature mismatch |
| LOAD-07 | Verify BPF maps are frozen | After load, run `bpftool map show` | Maps show `frozen` status; update attempts fail |

### 3.2 Basic Blocking

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| BLOCK-01 | Write to protected file | Try `echo "x" > protected_file` | Operation denied |
| BLOCK-02 | Delete protected file | Try `rm protected_file` | Operation denied |
| BLOCK-03 | Rename over protected file | `mv temp protected_file` | Rename denied |
| BLOCK-04 | Create hard link to protected file | `ln protected_file /tmp/alias` | Link creation denied |
| BLOCK-05 | `mmap` with write intent | Open file O_RDONLY, mmap with PROT_WRITE | mmap denied |
| BLOCK-06 | `truncate` protected file | `truncate -s 0 protected_file` | Truncate denied |
| BLOCK-07 | `chmod/chown` protected file | Change permissions/owner | Operation denied |
| BLOCK-08 | `setxattr` | Try to set extended attribute | Operation denied |
| BLOCK-09 | `openat2` with various flags | Try `openat2` with `RESOLVE_NO_SYMLINKS` and write intent | Write open denied |
| BLOCK-10 | `io_uring` write | Submit write request via io_uring | Write request rejected |
| BLOCK-11 | `sendfile` / `copy_file_range` | Try copying data into protected file | Copy operation denied |
| BLOCK-12 | Write via `/proc/self/fd` | Open protected file read-only, then attempt write via fd | Write denied |
| BLOCK-13 | `renameat2` with `RENAME_EXCHANGE` | Exchange protected file with temp file | Exchange denied |
| BLOCK-14 | Symlink on protected directory | Create symlink inside protected dir or to protected dir | Symlink creation denied |

### 3.3 Allow Legitimate Operations

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| ALLOW-01 | Read protected file | `cat protected_file` | Content displayed |
| ALLOW-02 | Create new file in protected dir | `touch newfile` | File created successfully |
| ALLOW-03 | Write to new file | `echo "data" > newfile` | Write succeeds |
| ALLOW-04 | Read via mmap PROT_READ | Open file O_RDONLY, mmap PROT_READ | mmap succeeds |
| ALLOW-05 | SIBB Python modules operate normally | Run `sibb_cli.py write` to create new ring | Success |

### 3.4 Privilege Escalation and Bypass Attempts

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| PRIV-01 | Root tries to unload eBPF | `bpftool prog detach` as root | Detach fails due to lockdown/SELinux |
| PRIV-02 | Root tries to disable eBPF sysctls | `sysctl kernel.unprivileged_bpf_disabled=0` | Change denied or ineffective |
| PRIV-03 | Root tries raw disk access | `dd if=/dev/sda of=...` | Access blocked by lockdown |
| PRIV-04 | Root tries to modify eBPF maps | `bpftool map update` on protected map | Map is frozen; update denied |
| PRIV-05 | Root tries to disable systemd service | `systemctl disable sibb-ebpf` | Service file protected; disable fails |
| PRIV-06 | Root tries to kill user-space agent | `kill -9 <agent_pid>` | systemd restarts agent; eBPF remains active |
| PRIV-07 | Root tries to modify audit log | Edit or delete audit log file | Log is HMAC-protected; modification detected |
| PRIV-08 | Root tries to remove `chattr +i` | `chattr -i protected_file` | eBPF still prevents modification |
| PRIV-09 | Root uses mount namespace | `mount --bind /tmp/evil /path/to/sibb` | Modification via bind mount denied |
| PRIV-10 | Root uses chroot | `chroot /tmp/evil /bin/sh` then modify protected path | Protected path inaccessible; modification denied |

### 3.5 Attack Detection and Logging

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| LOG-01 | Tamper attempt logged | Attempt to write protected file | Ring buffer event contains PID, UID, path, timestamp |
| LOG-02 | Event forwarded to user space | Wait for agent to read event | Event appears in AAAC audit log |
| LOG-03 | Multiple attempts | Try many tamper operations rapidly | No event loss; rate limiting may apply |
| LOG-04 | Audit log integrity | Tamper with audit log after events stored | HMAC verification fails, alert generated |
| LOG-05 | Agent killed, events not lost | Kill agent, generate several tamper attempts, restart agent | Events are preserved and forwarded after agent restart |

### 3.6 Performance Impact

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| PERF-01 | File open/read overhead | Benchmark 10,000 file reads with eBPF active vs inactive; compute average, stddev | Overhead < 5% |
| PERF-02 | File creation overhead | Benchmark 10,000 file creations | Overhead < 5% |
| PERF-03 | System stability | Run stress tests | No kernel panics or hangs |
| PERF-04 | Memory usage | Monitor kernel memory with eBPF active | No significant leak |

### 3.7 Filesystem Support

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| FS-01 | ext4 | Run basic block/allow tests on ext4 | Pass |
| FS-02 | xfs | Run basic block/allow tests on xfs | Pass |
| FS-03 | btrfs | Run basic block/allow tests on btrfs (if supported) | Pass or document limitation |

### 3.8 Environment Verification

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| ENV-01 | Check kernel lockdown | Read `/sys/kernel/security/lockdown` | Mode is `integrity` or `confidentiality` |
| ENV-02 | Verify secure boot | Check `mokutil --sb-state` | SecureBoot enabled |

---

## 4. Acceptance Criteria

- All tests pass.
- No High/Medium findings in static analysis of eBPF C code (using `smatch`, `sparse`, `bpftool prog dump xlated`).
- The program blocks all unauthorized modification attempts, including by root and advanced syscalls.
- Legitimate operations are not affected.
- Audit events are reliable and protected from tampering.
- Performance overhead is within defined limits (<5% for file operations).
- The program survives reboot and service restart.
- Environment hardening (lockdown, secure boot) is verified.

---

## 5. Next Steps

1. **Prototype Implementation** – Write minimal eBPF program using LSM hooks.
2. **Run Tests** – Execute the test suite in a VM.
3. **Static Analysis** – Use `smatch` or `sparse` on C code.
4. **Documentation** – Record decision (e.g., DC-127).

---

**End of Test Plan v1.1**
