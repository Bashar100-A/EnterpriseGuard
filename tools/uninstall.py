#!/usr/bin/env python3
"""EnterpriseGuard Uninstaller."""
from __future__ import annotations
import argparse, shutil, sys
from pathlib import Path
sys.dont_write_bytecode = True
PROTECTED_DIRS = {"adie", "intelligence"}
def is_protected(path: Path) -> bool:
    return any(part in PROTECTED_DIRS for part in path.parts)
def uninstall(target: Path) -> int:
    if is_protected(target):
        print(f"ERROR: refusing to uninstall protected path {target}", file=sys.stderr)
        return 1
    if not target.exists():
        print(f"Target {target} does not exist.")
        return 0
    if not target.is_dir():
        print(f"ERROR: target {target} is not a directory.", file=sys.stderr)
        return 1
    shutil.rmtree(target)
    print(f"EnterpriseGuard uninstalled from {target}")
    return 0
def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Uninstaller")
    parser.add_argument("--target", type=Path, required=True, help="Installation directory to remove")
    args = parser.parse_args()
    return uninstall(args.target)
if __name__ == "__main__":
    raise SystemExit(main())
