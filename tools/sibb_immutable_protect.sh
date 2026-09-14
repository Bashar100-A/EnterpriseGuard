#!/bin/bash
#
# sibb_immutable_protect.sh
# Apply chattr +i (immutable) to SIBB storage paths to enforce WORM at kernel level.
#
# Usage:
#   sudo ./sibb_immutable_protect.sh [path1] [path2] ...
#
# If no paths provided, defaults to ~/.enterpriseguard/sibb
#

set -euo pipefail

# ---------- Configuration ----------
DEFAULT_PATH="$HOME/.enterpriseguard/sibb"
LOG_FILE="/tmp/sibb_immutable_protect.log"
# ------------------------------------

# Function to log messages
log() {
    local msg="$1"
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | $msg" | tee -a "$LOG_FILE"
}

# Check root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run as root (use sudo)." >&2
    exit 1
fi

# Determine target paths
if [[ $# -eq 0 ]]; then
    # No args, use default path if exists, else error
    if [[ -e "$DEFAULT_PATH" ]]; then
        TARGETS=("$DEFAULT_PATH")
        log "No path provided, using default: $DEFAULT_PATH"
    else
        echo "ERROR: Default path $DEFAULT_PATH does not exist. Provide paths as arguments." >&2
        exit 1
    fi
else
    TARGETS=("$@")
fi

# Apply chattr +i to each target
for target in "${TARGETS[@]}"; do
    if [[ ! -e "$target" ]]; then
        log "WARNING: $target does not exist, skipping."
        continue
    fi

    log "Applying chattr +i to $target ..."
    if chattr -R +i "$target" 2>>"$LOG_FILE"; then
        log "SUCCESS: $target is now immutable."
    else
        log "ERROR: Failed to set immutable on $target."
        exit 1
    fi
done

# Verify by listing attributes
log "Current immutable attributes:"
for target in "${TARGETS[@]}"; do
    if [[ -e "$target" ]]; then
        lsattr -d "$target" 2>/dev/null | tee -a "$LOG_FILE" || true
        # For files inside directories, show first few
        if [[ -d "$target" ]]; then
            lsattr "$target" 2>/dev/null | head -10 | tee -a "$LOG_FILE" || true
        fi
    fi
done

log "SIBB immutability protection completed."
