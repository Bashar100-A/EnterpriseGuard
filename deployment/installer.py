#!/usr/bin/env python3
"""EnterpriseGuard Installer (DC-040).

Installs EnterpriseGuard to a target directory, creates the required
system user and log directory, hardens protected directories, generates
systemd service, timer, and config units based on the actual install path,
and validates the installation without ever reading protected directory contents.
"""

from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Must be set before any other import or heavy operation.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROTECTED_DIRS = {
    "adie",
    "intelligence",
    "src/enterpriseguard/adie",
    "src/enterpriseguard/intelligence",
}
REQUIRED_FILES = [
    "requirements.txt",
    "tools/checklist.py",
    "CONTRACTS.md",
]
DEFAULT_INSTALL_ROOT = Path("/opt/enterpriseguard")
DEFAULT_LOG_DIR = Path("/var/log/enterpriseguard")
DEFAULT_USER = "enterpriseguard"
DEFAULT_GROUP = "enterpriseguard"
DEFAULT_CHECKLIST_INTERVAL = 60  # minutes

ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_within_root(path: Path) -> bool:
    """Return True if path is inside ROOT."""
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def is_protected_path(path: Path) -> bool:
    """Return True if the path is under any protected directory.

    Only meaningful for paths inside ROOT. For paths outside ROOT,
    this function returns False because they are not part of the
    repository's protected structure.
    """
    if not is_within_root(path):
        return False
    rel = path.resolve().relative_to(ROOT.resolve())
    return any(part in PROTECTED_DIRS for part in rel.parts)


def run_command(command: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=ENV,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def validate_repository(root: Path) -> dict:
    """Validate required repository files before installation."""
    missing = [f for f in REQUIRED_FILES if not (root / f).exists()]
    if missing:
        return {"status": "FAIL", "errors": [f"Missing required file: {m}" for m in missing]}

    protected_status = {}
    for rel in PROTECTED_DIRS:
        protected_status[rel] = (root / rel).exists()

    if not any(protected_status.values()):
        return {
            "status": "WARN",
            "errors": [],
            "warnings": ["No protected directories found. This is acceptable for a minimal install."],
            "protected_status": protected_status,
        }

    return {
        "status": "PASS",
        "errors": [],
        "warnings": [],
        "protected_status": protected_status,
    }


def run_checklist(root: Path) -> bool:
    checklist_path = root / "tools" / "checklist.py"
    if not checklist_path.exists():
        print("checklist.py not found", file=sys.stderr)
        return False
    code, stdout, stderr = run_command(["python3", str(checklist_path)], timeout=120)
    print(stdout)
    if code != 0 or "FAILURE" in stdout:
        print(stderr, file=sys.stderr)
        return False
    return True


def ensure_user_and_group(user: str, group: str) -> None:
    """Create system user and group if they do not already exist. Raise on failure."""
    try:
        grp.getgrnam(group)
    except KeyError:
        code, _, stderr = run_command(["groupadd", "--system", group])
        if code != 0:
            raise RuntimeError(f"Failed to create group {group}: {stderr}")

    try:
        pwd.getpwnam(user)
    except KeyError:
        code, _, stderr = run_command([
            "useradd",
            "--system",
            "--gid", group,
            "--home-dir", "/nonexistent",
            "--shell", "/usr/sbin/nologin",
            user,
        ])
        if code != 0:
            raise RuntimeError(f"Failed to create user {user}: {stderr}")


def ensure_log_dir(log_dir: Path, user: str, group: str) -> None:
    """Create log directory and set ownership. Raise on failure."""
    log_dir.mkdir(parents=True, exist_ok=True)
    code, _, stderr = run_command(["chown", f"{user}:{group}", str(log_dir)])
    if code != 0:
        raise RuntimeError(f"Failed to chown {log_dir}: {stderr}")
    code, _, stderr = run_command(["chmod", "750", str(log_dir)])
    if code != 0:
        raise RuntimeError(f"Failed to chmod {log_dir}: {stderr}")


def harden_protected_dirs(root: Path) -> list[str]:
    """Set protected directories to root-only. Return list of errors."""
    errors = []
    for rel in PROTECTED_DIRS:
        path = root / rel
        if path.exists():
            code, _, stderr = run_command(["chmod", "700", str(path)])
            if code != 0:
                errors.append(f"Failed to chmod {rel}: {stderr}")
    return errors


def read_conf_interval(conf_path: Path) -> int:
    """Read checklist_interval_minutes from enterpriseguard.conf."""
    interval = DEFAULT_CHECKLIST_INTERVAL
    if not conf_path.exists():
        return interval
    for line in conf_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("checklist_interval_minutes"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                try:
                    interval = int(parts[1].strip())
                except ValueError:
                    pass
    return interval


def generate_timer_file(interval_minutes: int, output_path: Path) -> None:
    """Generate the systemd timer unit atomically."""
    content = f"""[Unit]
Description=EnterpriseGuard Periodic Governance Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec={interval_minutes}min
Unit=enterpriseguard.service
Persistent=true

# Randomize start time to distribute load across multiple systems
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(output_path.parent), prefix=".timer.", suffix=".tmp", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    output_path.chmod(0o644)


def generate_service_file(install_root: Path, output_path: Path) -> None:
    """Generate the systemd service unit with the actual install root."""
    protected_paths = " ".join(
        str(install_root / rel) for rel in PROTECTED_DIRS
    )
    content = f"""[Unit]
Description=EnterpriseGuard Governance Check Service
After=network.target

[Service]
Type=oneshot
User=enterpriseguard
Group=enterpriseguard
WorkingDirectory={install_root}
ExecStart={install_root}/.venv/bin/python3 {install_root}/tools/checklist.py
StandardOutput=append:/var/log/enterpriseguard/checklist.log
StandardError=append:/var/log/enterpriseguard/checklist.log
Environment=PYTHONDONTWRITEBYTECODE=1

# Prevent hanging indefinitely
TimeoutStartSec=300

# Do not restart automatically
Restart=no

# Hardening
ProtectSystem=full
ProtectHome=true
PrivateTmp=true
NoNewPrivileges=true
ReadOnlyPaths={install_root}/tools

# Block access to protected directories even if filesystem permissions are misconfigured
InaccessiblePaths={protected_paths}

[Install]
WantedBy=multi-user.target
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(output_path.parent), prefix=".service.", suffix=".tmp", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    output_path.chmod(0o644)


def generate_conf_file(install_root: Path, output_path: Path, interval_minutes: int = DEFAULT_CHECKLIST_INTERVAL) -> None:
    """Generate enterpriseguard.conf with the actual install root and interval."""
    content = f"""[enterpriseguard]
install_root = {install_root}
tools_dir = {install_root}/tools

protected_dirs = adie,intelligence,src/enterpriseguard/adie,src/enterpriseguard/intelligence

activity_log = {install_root}/tools/activity_log.json
errors_log = {install_root}/tools/errors.log
decisions_log = {install_root}/tools/DECISIONS_LOG.md

integrity_baseline = {install_root}/tools/integrity_baseline.json
integrity_sentinel = {install_root}/integrity_baseline_sentinel.json

trusted_baseline = {install_root}/tools/TRUSTED_BASELINE.json
trusted_sentinel = {install_root}/TRUSTED_BASELINE_SENTINEL.json

checklist_interval_minutes = {interval_minutes}
timezone = UTC
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(output_path.parent), prefix=".conf.", suffix=".tmp", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    output_path.chmod(0o644)


def copy_tree_excluding_protected(src: Path, dst: Path) -> None:
    """Copy tree recursively but skip any protected path."""
    def ignore_func(directory: str, names: list[str]) -> set[str]:
        dir_path = Path(directory)
        ignored = set()
        for name in names:
            path = dir_path / name
            if is_protected_path(path):
                ignored.add(name)
        return ignored

    shutil.copytree(src, dst, ignore=ignore_func, dirs_exist_ok=True)


def copy_tools_excluding_backups_and_quarantine(src: Path, dst: Path) -> None:
    """Copy tools/ but skip backups and quarantine subdirectories."""
    def ignore_func(directory: str, names: list[str]) -> set[str]:
        dir_path = Path(directory)
        ignored = set()
        for name in names:
            if name in {"backups", "quarantine"}:
                ignored.add(name)
        return ignored

    shutil.copytree(src, dst, ignore=ignore_func, dirs_exist_ok=True)


def install_files(root: Path, target: Path, skip_checklist: bool = False) -> int:
    """Copy repository files to the target directory, excluding protected dirs."""
    if is_within_root(target):
        if is_protected_path(target):
            print(f"ERROR: target {target} is inside a protected directory.", file=sys.stderr)
            return 1

    if not skip_checklist:
        validation = validate_repository(root)
        if validation["status"] == "FAIL":
            print("Repository validation failed.", file=sys.stderr)
            for err in validation["errors"]:
                print(f"  - {err}", file=sys.stderr)
            return 1
        if not run_checklist(root):
            print("Checklist failed. Installation aborted.", file=sys.stderr)
            return 1

    target.mkdir(parents=True, exist_ok=True)

    for item in root.iterdir():
        if item.name.startswith(".") and item.name != ".claude":
            continue
        if item.name in {"adie", "intelligence"}:
            continue
        if item.name in {"__pycache__", "node_modules", ".venv", "venv"}:
            continue
        dest = target / item.name
        if item.is_dir():
            if item.name == "src":
                copy_tree_excluding_protected(item, dest)
            elif item.name == "tools":
                copy_tools_excluding_backups_and_quarantine(item, dest)
            else:
                shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    venv_path = target / ".venv"
    if not venv_path.exists():
        code, _, stderr = run_command(["python3", "-m", "venv", str(venv_path)], timeout=300)
        if code != 0:
            raise RuntimeError(f"Failed to create venv: {stderr}")

    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        raise RuntimeError("pip not found in venv after creation")

    code, _, stderr = run_command([str(pip_path), "install", "-r", str(target / "requirements.txt")], timeout=300)
    if code != 0:
        raise RuntimeError(f"Failed to install requirements: {stderr}")

    print(f"EnterpriseGuard installed to {target}")
    print(f"Timestamp: {utc_now()}")
    return 0


def post_install_checks(
    root: Path,
    log_dir: Path,
    user: str,
    group: str,
    timer_enabled: bool = False,
) -> dict:
    """Run post-installation verification."""
    errors = []
    warnings = []

    # Check protected directories are root-only
    for rel in PROTECTED_DIRS:
        path = root / rel
        if path.exists():
            mode = path.stat().st_mode & 0o777
            if mode != 0o700:
                warnings.append(f"Protected dir {rel} mode is {oct(mode)}, expected 700")
        else:
            warnings.append(f"Protected dir {rel} missing during post-install check")

    # Check log dir writable by user
    code, _, stderr = run_command(["runuser", "-u", user, "--", "test", "-w", str(log_dir)])
    if code != 0:
        errors.append(f"Log dir {log_dir} not writable by {user}: {stderr}")

    # Check timer is disabled (unless explicitly enabled)
    if not timer_enabled:
        code, _, _ = run_command(["systemctl", "is-enabled", "enterpriseguard-timer.service"])
        if code == 0:
            warnings.append("Timer is enabled, but default is disabled.")

    # Check that backup/quarantine directories were not copied
    for forbidden in ["backups", "quarantine"]:
        forbidden_path = root / "tools" / forbidden
        if forbidden_path.exists():
            warnings.append(f"Found unexpected {forbidden} directory in target tools/")

    # Optional: check timer is not active
    code, _, _ = run_command(["systemctl", "is-active", "enterpriseguard-timer.service"])
    if code == 0:
        warnings.append("Timer is active, but default is inactive.")

    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return {"status": status, "errors": errors, "warnings": warnings}


def main() -> int:
    # Root check must happen before anything else
    if os.geteuid() != 0:
        print("ERROR: This installer must be run as root.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="EnterpriseGuard Installer")
    parser.add_argument(
        "--install",
        type=Path,
        default=None,
        help=f"Install to directory (default: {DEFAULT_INSTALL_ROOT})",
    )
    parser.add_argument(
        "--user",
        default=DEFAULT_USER,
        help=f"System user for the service (default: {DEFAULT_USER})",
    )
    parser.add_argument(
        "--group",
        default=DEFAULT_GROUP,
        help=f"System group for the service (default: {DEFAULT_GROUP})",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help=f"Log directory (default: {DEFAULT_LOG_DIR})",
    )
    parser.add_argument("--check", action="store_true", help="Dry-run validation only")
    parser.add_argument("--skip-checklist", action="store_true", help="Skip checklist during install")
    args = parser.parse_args()

    target = args.install or DEFAULT_INSTALL_ROOT

    if args.check:
        validation = validate_repository(ROOT)
        print(json.dumps(validation, indent=2))
        return 0 if validation["status"] == "PASS" else 1

    if args.install:
        validation = validate_repository(ROOT)
        if validation["status"] == "FAIL":
            print("Repository validation failed.", file=sys.stderr)
            for err in validation["errors"]:
                print(f"  - {err}", file=sys.stderr)
            return 1

        if not args.skip_checklist:
            if not run_checklist(ROOT):
                print("Checklist failed. Installation aborted.", file=sys.stderr)
                return 1

        try:
            result = install_files(ROOT, target, skip_checklist=True)
            if result != 0:
                return result

            ensure_user_and_group(args.user, args.group)
            ensure_log_dir(args.log_dir, args.user, args.group)

            chmod_errors = harden_protected_dirs(target)
            if chmod_errors:
                for e in chmod_errors:
                    print(f"ERROR: {e}", file=sys.stderr)
                raise RuntimeError("Failed to harden one or more protected directories")

            # Generate deployment files with actual paths
            deploy_dir = target / "deploy"
            deploy_dir.mkdir(parents=True, exist_ok=True)

            conf_path = deploy_dir / "enterpriseguard.conf"
            generate_conf_file(target, conf_path, interval_minutes=DEFAULT_CHECKLIST_INTERVAL)

            interval = read_conf_interval(conf_path)

            timer_path = deploy_dir / "enterpriseguard-timer.service"
            generate_timer_file(interval, timer_path)

            service_path = deploy_dir / "enterpriseguard.service"
            generate_service_file(target, service_path)

            print(f"Generated config, service, and timer for {target}")

            result = post_install_checks(target, args.log_dir, args.user, args.group)
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "PASS" else 1

        except Exception as exc:
            print(f"Installation failed: {exc}", file=sys.stderr)
            if target.exists() and target != ROOT:
                shutil.rmtree(target, ignore_errors=True)
            return 1

    parser.print_usage(sys.stderr)
    print("error: one of --install or --check is required", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())