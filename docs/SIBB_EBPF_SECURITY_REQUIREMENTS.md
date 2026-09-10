# SIBB eBPF Protection — Security Requirements Document (SRD)

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB eBPF Protection Layer  
**Version:** 1.1  
**Status:** Revised after security review  
**Date:** 2026-09-08  
**Methodology:** OWASP ASVS, NIST SP 800-218, STRIDE

---

## 1. Introduction

This document defines the security requirements for an eBPF-based protection layer that enforces WORM (Write Once, Read Many) semantics on SIBB storage files at the kernel level. The program will intercept file modification, deletion, renaming, and other state-changing operations, and prevent unauthorized changes even from privileged users (root). Because root can potentially disable eBPF or bypass it, the design must rely on multiple layers of defense, including kernel lockdown, mandatory access control, and hardware roots of trust.

---

## 2. Assets to Protect

| Asset | Description | Criticality |
|-------|-------------|-------------|
| **SIBB Data Files** | Stored rings, shares, and other immutable files | Critical |
| **SIBB Metadata Files** | `.worm_metadata.json` and its HMAC/backup files | Critical |
| **HMAC Keys** | Keys used for integrity verification | Critical |
| **Chain State Files** | Files tracking the current chain head | High |
| **Protected Paths** | The directories where SIBB files reside | Critical |
| **eBPF Program Itself** | The kernel code enforcing protection | Critical |
| **eBPF Configuration** | List of protected paths and rules | High |

---

## 3. Threat Actors

| Actor | Description | Capabilities |
|-------|-------------|--------------|
| **Privileged User (root)** | Administrator attempting to tamper with SIBB files | Can bypass file permissions, load/unload kernel modules, disable eBPF, access raw disk |
| **Malicious Process** | Compromised application running with any privileges | Attempt to open, write, delete, rename protected files, use mmap/hard links |
| **Kernel-Level Attacker** | Exploit in another kernel module | Attempt to disable eBPF or modify memory |
| **Insider Threat** | Person with legitimate access to the system | Attempt to alter chain history or stored data |

---

## 4. Security Properties (CIA + Non-Repudiation)

- **Integrity:** Protected files cannot be modified, deleted, renamed, or altered through any syscall, including mmap and hard links, by any user-space process, including root.
- **Availability:** The eBPF program must not prevent legitimate SIBB operations (reads, new file creation). The system must remain stable.
- **Confidentiality:** The eBPF program must not expose sensitive data; it only acts as a gatekeeper.
- **Non-Repudiation:** Attempts to tamper with protected files should be logged (via ring buffer) for audit, and these events must be reliably forwarded.

---

## 5. Functional Requirements (FR)

- **FR-1:** The eBPF program shall monitor all file system operations that can modify protected files, including: `open` (with write intent), `write`, `pwrite`, `mmap` (with `PROT_WRITE`), `mprotect`, `truncate`, `ftruncate`, `unlink`, `rename`, `link`, `chmod`, `chown`, `setxattr`, `removexattr`, `utimes`.
- **FR-2:** It shall allow read-only operations on protected files.
- **FR-3:** It shall block any attempt to write to or modify an existing protected file through any supported syscall.
- **FR-4:** It shall block any attempt to delete, rename, or create a hard link to a protected file. Renaming a file onto a protected file (overwrite) must also be blocked.
- **FR-5:** It shall allow creation of new files in SIBB directories if they do not already exist, but must prevent overwrite of existing files.
- **FR-6:** It shall enforce protections atomically and consistently across all processes, including root, unless the system is in kernel lockdown or a hardware-enforced secure state.
- **FR-7:** The set of protected paths must be configurable and loaded at runtime from a signed configuration file or via a secured user-space agent. After loading, the configuration must be immutable until the program is unloaded with explicit authorization.
- **FR-8:** The eBPF program shall generate an event (ring buffer) when a tamper attempt is detected, including process ID, user ID, file path, and timestamp. The user-space agent must forward these events to the AAAC audit chain.
- **FR-9:** The protection must survive process restarts and continue to be active until explicitly unloaded by an authorized process (e.g., via systemd service with strict permissions).
- **FR-10:** The eBPF program itself must be protected from unauthorized unload. Only a dedicated root-owned process with a specific capability and valid signature may detach the program.
- **FR-11:** The system must ensure that the eBPF program is automatically reloaded on boot, and this mechanism is protected from tampering (e.g., systemd unit with `ProtectSystem=strict`).
- **FR-12:** The eBPF program and its configuration must be protected by additional layers: kernel lockdown (integrity/confidentiality), SELinux/AppArmor policies, and file immutability (`chattr +i`) where applicable.

---

## 6. Security Requirements (SR)

- **SR-1:** The eBPF program must not rely on user-space memory for critical decisions; all path validation must be done within the eBPF program using in-kernel data structures.
- **SR-2:** The protected path list must be immutable after loading; any changes require unloading and reloading with explicit authorization and a valid signature.
- **SR-3:** The eBPF program must use the BPF LSM hooks (or kprobes on `security_file_open`, `security_inode_unlink`, `security_inode_link`, `security_inode_rename`, etc.) to intercept operations before they occur.
- **SR-4:** The program must not introduce any new attack surface; it should be written in a memory-safe subset of C and pass the kernel verifier.
- **SR-5:** The program must be compatible with secure boot and kernel module signing requirements. On Linux, `module.sig_enforce=1`, `kernel_lockdown=integrity/confidentiality`, and `kexec_load_disabled=1` should be enabled in production.
- **SR-6:** The program must generate audit events that are forwarded to user space and logged in the AAAC audit chain. The ring buffer must be sized appropriately and the user-space agent must be monitored to prevent event loss.
- **SR-7:** The program must be thoroughly tested to ensure it does not cause kernel panics or performance degradation. Overhead should be measured and kept below a defined threshold (e.g., < 5% in file open/read operations).
- **SR-8:** The program must block `mmap` and `mprotect` attempts with write intent on protected files.
- **SR-9:** The eBPF object file must be signed and its hash verified before loading. It must be stored in a protected path with `chattr +i` and owned by root.
- **SR-10:** The configuration file must be signed or HMAC-protected, and its integrity verified at load time. The user-space agent that loads the program must be restricted (e.g., via systemd sandboxing, SELinux).
- **SR-11:** The system must ensure that the eBPF program is not unloaded or disabled by a root user without proper authorization. This may be achieved through kernel lockdown and SELinux policy.
- **SR-12:** The protection must cover inode-level operations to prevent bypass via hard links or path aliasing.

---

## 7. Constraints and Assumptions

- **Kernel version:** Linux 5.8+ (full LSM eBPF support), or 4.18+ for kprobes. LSM BPF requires `CAP_SYS_ADMIN` to load.
- **Language:** C (restricted subset for BPF)
- **Tooling:** `clang`, `libbpf`, `bpftool`, `bpftrace`
- **Environment:** The system must have `CAP_BPF`, `CAP_PERFMON`, and `CAP_SYS_ADMIN` capabilities to load and manage eBPF programs. The loading process should be run as root and then drop unnecessary capabilities.
- **Storage:** SIBB files are located in known directories (e.g., `~/.enterpriseguard/sibb/`, `/var/lib/enterpriseguard/`).
- **Interoperability:** The eBPF layer must not interfere with the existing Python-based SIBB modules; they should continue to work normally for legitimate operations.
- **Supported filesystems:** ext4 and xfs initially; other filesystems may require separate testing.

---

## 8. Acceptance Criteria

- The eBPF program loads successfully and passes the kernel verifier.
- Attempts to modify/delete/rename protected files are blocked and logged, including by root.
- Hard link creation to protected files is blocked.
- mmap/write/mprotect attempts are blocked.
- Legitimate SIBB operations (read, create new files) are unaffected.
- The program remains active after reboot and cannot be unloaded by unauthorized root.
- Audit events are generated and reliably forwarded to user space.
- No significant performance degradation is observed.
- All advanced attack tests pass (root tries to unload eBPF, raw disk access, hard link, mmap, rename overwrite).

---

## 9. Next Steps

1. **Threat Model (STRIDE)** – Analyze threats specific to eBPF-based protection.
2. **Test Plan** – Define tests for loading, blocking, and logging.
3. **Prototype Implementation** – Write a minimal eBPF program using LSM hooks.
4. **Integration** – Create a user-space agent to manage the eBPF program and forward events.
5. **Documentation** – Record decision (e.g., DC-127).

---

**End of Security Requirements Document v1.1**
