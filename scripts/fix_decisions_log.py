#!/usr/bin/env python3
"""Rebuild tools/DECISIONS_LOG.md cleanly.

Fixes:
- Duplicated sections from old pollution
- Wrong DC-064 (GPG) replaced with correct DC-064 (Dimensional Engine)
- Adds DC-130 (GPG Key Loss retrospective) at the end
- Sorts entries by DC number ascending
- Restores header and file permissions (644)
"""

import re
import shutil
from pathlib import Path
from datetime import datetime, timezone

SRC = Path("tools/DECISIONS_LOG.md")
BACKUP = Path(f"tools/DECISIONS_LOG.md.corrupted_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
TMP = Path("tools/DECISIONS_LOG.md.new")

DC_LINE = re.compile(r"^\|\s*(DC-(\d+))")


def dc_num(line: str) -> int:
    m = DC_LINE.match(line)
    return int(m.group(2)) if m else -1


def get_key(line: str) -> str:
    m = DC_LINE.match(line)
    return m.group(1) if m else ""


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: {SRC} not found")
        return 1

    # 1. Read polluted file
    raw_lines = SRC.read_text(encoding="utf-8").splitlines()
    print(f"Read {len(raw_lines)} lines from {SRC}")

    # 2. Collect first unique occurrence of each DC, skip wrong DC-064
    unique: dict[str, str] = {}
    skipped_wrong_064 = False
    for line in raw_lines:
        if not line.startswith("| DC-"):
            continue
        # Skip wrong DC-064 (GPG, dated 2026-09-12)
        if line.startswith("| DC-064 | 2026-09-12"):
            skipped_wrong_064 = True
            continue
        key = get_key(line)
        if not key:
            continue
        if key in unique:
            continue
        unique[key] = line

    print(f"Collected {len(unique)} unique DC entries")
    print(f"Skipped wrong DC-064 (GPG): {skipped_wrong_064}")

    # 3. Verify DC-064 original is present
    if "DC-064" not in unique:
        print("ERROR: DC-064 (original Dimensional Engine) missing")
        return 1

    # 4. Sort by DC number
    sorted_entries = sorted(unique.values(), key=dc_num)

    # 5. Add DC-130 (GPG Key Loss)
    dc_130 = (
        "| DC-130 | 2026-09-12T16:30:00Z | GPG Key Loss — DC-041 Retrospective | "
        "The GPG signing key created in DC-041 (RSA 4096, UID: EnterpriseGuard ADIE "
        "<adie@enterpriseguard.local>, Key ID: 9188569AD7F609C869730CFB20AB83C64E6B50CB) "
        "was lost due to a prior OS reformat that destroyed /home/bashar/.gnupg/. "
        "No backup existed and the full fingerprint was never recorded. "
        "All six .asc files have been archived under "
        "archive/signatures-2026-09-01-lost-key/ for audit trail purposes. "
        "A new Ed25519 key will be generated with proper passphrase, "
        "dual external backups, and documented fingerprint. "
        "| Three systematic failures recorded: fingerprint undocumented, "
        "no private key backup, no public key export. | Complete |"
    )

    # 6. Build final content
    header = (
        "# Decision Ledger\n\n"
        "| Decision ID | Timestamp | Context | Architectural Decision | Rationale | Status |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
    )
    footer = (
        "\n\n---\n\n"
        "## Notes\n"
        "- This ledger is the canonical governance record for the EnterpriseGuard project.\n"
        "- Format: `| Decision ID | Timestamp | Context | Architectural Decision | Rationale | Status |`\n"
        "- `SUPERSEDED` entries are historical and kept for audit trail.\n"
        "- Never delete entries; mark superseded if needed.\n"
    )

    final_content = (
        header
        + "\n".join(sorted_entries)
        + "\n"
        + dc_130
        + "\n"
        + footer
    )

    # 7. Write to temp file
    TMP.write_text(final_content, encoding="utf-8")
    print(f"Wrote {len(sorted_entries) + 1} entries to {TMP}")

    # 8. Backup corrupted file, then replace
    shutil.copy2(SRC, BACKUP)
    print(f"Backup: {BACKUP}")

    shutil.move(str(TMP), str(SRC))
    print(f"Replaced {SRC}")

    # 9. Fix permissions (no execute bit)
    SRC.chmod(0o644)
    print("Permissions set to 644")

    # 10. Final stats
    final_lines = SRC.read_text(encoding="utf-8").splitlines()
    print(f"Final file: {len(final_lines)} lines")
    print("DONE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
