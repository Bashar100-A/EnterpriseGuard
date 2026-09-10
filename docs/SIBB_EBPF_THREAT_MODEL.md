# SIBB eBPF Protection — Threat Model (STRIDE)

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB eBPF Protection Layer  
**Version:** 1.1  
**Date:** 2026-09-08  
**Reference:** Security Requirements Document v1.1

---

## 1. Introduction

This threat model analyzes potential threats against the eBPF-based protection layer using STRIDE. It builds on the previous version and incorporates advanced attack scenarios, including BPF map tampering, verifier exploits, audit log tampering, and service disablement. The model is aligned with SRD v1.1 and includes specific mitigations for each threat.

---

## 2. Assets

| Asset ID | Asset |
|----------|-------|
| A1 | SIBB Data Files |
| A2 | SIBB Metadata Files |
| A3 | HMAC Keys |
| A4 | Chain State Files |
| A5 | Protected Paths |
| A6 | eBPF Program |
| A7 | eBPF Configuration |
| A8 | Audit Logs |

---

## 3. Threat Actors

| Actor ID | Actor |
|----------|-------|
| T1 | Privileged User (root) |
| T2 | Malicious Process |
| T3 | Kernel-Level Attacker |
| T4 | Insider Threat |
| T5 | Natural Failure |

---

## 4. STRIDE Analysis

### 4.1 Spoofing (S)

| Threat | Asset | Scenario | Controls (FR/SR) | Status |
|--------|-------|----------|------------------|--------|
| S-1: Spoofed eBPF program | A6 | Attacker replaces the eBPF object file with a malicious version before loading | SR-9 (signature and hash verification) | Must sign eBPF binary and verify before load |
| S-2: Spoofed configuration file | A7 | Attacker modifies the protected path list to exclude target files | SR-10 (signed/HMAC config) | Config must be integrity-protected |
| S-3: Spoofed user-space agent | A6 | Attacker replaces the loader with a malicious one that disables protection | SR-10, systemd sandboxing | Restrict loader privileges |
| S-4: Spoofed audit events | A8 | Attacker injects fake tamper events or suppresses real ones | SR-13 (audit log protection) | Protect audit log with HMAC and secure transport |

### 4.2 Tampering (T)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| T-1: Write to protected file via write/pwrite | A1, A2 | Process opens file for write and modifies content | FR-3, FR-1, SR-3 | LSM hook on file_open/write |
| T-2: Modify via mmap/mprotect | A1 | Attacker uses mmap(PROT_WRITE) to alter file without write syscall | FR-1, SR-8 | Block mmap with write intent |
| T-3: Truncate or ftruncate | A1 | Attacker truncates file | FR-1 | Block truncate/ftruncate |
| T-4: Delete protected file (unlink) | A1 | Attacker removes file | FR-4 | Block unlink |
| T-5: Rename over protected file | A1 | Attacker renames temp file over protected ring | FR-4 | Block rename if target is protected |
| T-6: Create hard link to protected file | A1 | Attacker creates hard link and modifies via alternate path | FR-4, SR-12 | Block link syscall for protected inodes |
| T-7: Change permissions/ownership | A1 | chmod/chown to weaken protection | FR-1 | Block chmod/chown |
| T-8: Modify extended attributes | A1 | setxattr to hide data or alter integrity | FR-1 | Block setxattr/removexattr |
| T-9: Modify chain state files | A4 | Tamper with chain head state | FR-3, FR-4 | Protected as data files |
| T-10: Tamper with eBPF program after load | A6 | Attempt to modify program maps or code | SR-3, kernel lockdown | BPF verifier, map freeze |
| T-11: Modify BPF maps to change protected paths | A6 | Attacker updates map to remove paths from protected list | SR-12 (map freeze), SR-11 | Freeze maps after load; restrict access to /sys/fs/bpf/ |
| T-12: Exploit verifier vulnerability | A6 | Attacker uses kernel exploit to bypass eBPF verifier | SR-4, keep kernel updated | Use latest stable kernel, minimize complexity |
| T-13: Tamper with audit log in user space | A8 | Root modifies or deletes audit logs to hide attacks | SR-13 | Protect audit log with HMAC and store in secure location |

### 4.3 Repudiation (R)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| R-1: Deny tamper attempt | A6 | Attacker denies attempting to modify protected file | FR-8, SR-6 | Ring buffer events include PID, UID, path, timestamp |
| R-2: Deny unloading eBPF | A6 | Root user unloads program and denies | FR-10, SR-11 | Lockdown + SELinux prevent unauthorized unload; audit log |
| R-3: Deny configuration change | A7 | Attacker changes protected paths and denies | SR-10 | Signed config; changes require explicit reload |

### 4.4 Information Disclosure (I)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| I-1: Reading protected files is allowed (not a threat) | A1 | Read-only access is legitimate | FR-2 | Ensure no blocking of reads |
| I-2: Leak HMAC keys via eBPF maps | A3 | Malicious eBPF program reads sensitive keys | SR-4, verifier | BPF maps not shared with untrusted programs |
| I-3: Expose file paths via audit events | A5 | Events reveal directory structure | SR-6, SR-13 | Log paths are necessary but protected from unauthorized read |
| I-4: Raw disk access bypasses eBPF | A1 | Root reads/writes /dev/sda directly | SR-11, kernel lockdown | Lockdown prevents raw disk access |

### 4.5 Denial of Service (DoS)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| D-1: Unload eBPF program | A6 | Root detaches program to disable protection | FR-10, SR-11 | Lockdown, SELinux |
| D-2: Disable eBPF sysctls | A6 | Root sets `kernel.unprivileged_bpf_disabled` or `kptr_restrict` | SR-11 | Lockdown, secure boot |
| D-3: Kill user-space agent | A6 | Attacker stops event forwarding | SR-6, FR-11 | systemd restarts agent; ring buffer persists |
| D-4: Exhaust kernel memory with many events | A6 | Flood of tamper attempts fills ring buffer | SR-6, SR-7 | Rate limiting, appropriate buffer size |
| D-5: Cause kernel panic via bug in eBPF | A6 | Malformed eBPF code crashes kernel | SR-4, verifier | Thorough testing, verifier ensures safety |
| D-6: Performance degradation | A1 | eBPF hooks slow down all file operations | SR-7 | Measure overhead, keep <5% |
| D-7: Disable systemd service responsible for loading eBPF | A6 | Attacker disables the service so protection won't load on boot | SR-10, chattr +i | Protect systemd unit file and associated scripts |

### 4.6 Elevation of Privilege (E)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| E-1: Root disables lockdown | A6 | Root tries to disable kernel lockdown to unload eBPF | SR-11, secure boot | Secure Boot with signed kernel; lockdown cannot be disabled at runtime |
| E-2: Root loads malicious kernel module | A6 | Attacker loads module to bypass eBPF | SR-11, module signing | module.sig_enforce=1 |
| E-3: Exploit in another kernel module | A6 | Kernel-level attacker uses kernel exploit to disable eBPF | SR-11, TPM/HSM | Hardware root of trust |
| E-4: Abuse CAP_SYS_ADMIN | A6 | Root uses CAP_SYS_ADMIN to alter eBPF maps | SR-3, SR-11 | Freeze maps after load; lockdown |
| E-5: Compromise loading process | A6 | Attacker gains control of root-owned loader | SR-10, systemd sandboxing | Drop privileges after load |
| E-6: File descriptor inherited before eBPF load | A1 | Process opened protected file before eBPF load and retains write fd | SR-3, SR-8 | LSM hook at file_open/read/write will still intercept; consider fd check on first use |

---

## 5. Mapping Threats to Requirements

| Threat ID | Mitigated by FR/SR | Priority |
|-----------|-------------------|----------|
| S-1 | SR-9 | High |
| S-2 | SR-10 | High |
| S-3 | SR-10, systemd sandbox | High |
| S-4 | SR-13 | High |
| T-1 | FR-3, FR-1, SR-3 | High |
| T-2 | FR-1, SR-8 | High |
| T-3 | FR-1 | High |
| T-4 | FR-4 | High |
| T-5 | FR-4 | High |
| T-6 | FR-4, SR-12 | High |
| T-7 | FR-1 | High |
| T-8 | FR-1 | High |
| T-9 | FR-3, FR-4 | High |
| T-10 | SR-3, lockdown | High |
| T-11 | SR-12, SR-11 | High |
| T-12 | SR-4 | High |
| T-13 | SR-13 | High |
| R-1 | FR-8, SR-6 | High |
| R-2 | FR-10, SR-11 | High |
| R-3 | SR-10 | High |
| I-1 | FR-2 | Medium |
| I-2 | SR-4 | High |
| I-3 | SR-6, SR-13 | Medium |
| I-4 | SR-11 | High |
| D-1 | FR-10, SR-11 | High |
| D-2 | SR-11 | High |
| D-3 | FR-11, SR-6 | High |
| D-4 | SR-6, SR-7 | Medium |
| D-5 | SR-4 | High |
| D-6 | SR-7 | Medium |
| D-7 | SR-10, chattr +i | High |
| E-1 | SR-11 | High |
| E-2 | SR-11 | High |
| E-3 | SR-11, TPM/HSM | High |
| E-4 | SR-3, SR-11 | High |
| E-5 | SR-10 | High |
| E-6 | SR-3, SR-8 | Medium |

---

## 6. Next Steps

1. **Test Plan** – Define tests for loading, blocking, logging, and advanced attack scenarios.
2. **Prototype Implementation** – Write a minimal eBPF program using LSM hooks.
3. **Integration** – Create a user-space agent to manage the eBPF program and forward events.
4. **Documentation** – Record decision (e.g., DC-127).

---

**End of Threat Model v1.1**
