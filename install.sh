#!/usr/bin/env bash
set -eu

# EnterpriseGuard ADIE - Sovereign Installer (Final Hardened)
# Usage: sudo bash install.sh --install [--prefix /path]
#        sudo bash install.sh --check  [--prefix /path]
#        sudo bash install.sh --uninstall [--prefix /path]

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_PREFIX="/opt/enterpriseguard"
PREFIX="${PREFIX:-$DEFAULT_PREFIX}"
ACTION="${1:-}"

ETC_DIR="/etc/enterpriseguard"
VAR_LIB_DIR="/var/lib/enterpriseguard"
VAR_LOG_DIR="/var/log/enterpriseguard"
BACKUP_DIR="$VAR_LIB_DIR/backups"
SERVICE_NAME="enterpriseguard"
BIN_PATH="/usr/local/bin/enterpriseguard"
MARKER=".enterpriseguard_install_marker"

export PYTHONDONTWRITEBYTECODE=1

die() {
    echo "ERROR: $*" >&2
    exit 1
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "This installer must be run as root (use sudo)."
    fi
}

is_safe_prefix() {
    case "$PREFIX" in
        /|/usr|/etc|/home|/var|/bin|/sbin|/lib|/lib64) return 1 ;;
        *) return 0 ;;
    esac
}

create_dirs() {
    mkdir -p "$PREFIX"
    mkdir -p "$PREFIX/tools"
    mkdir -p "$PREFIX/backups"
    mkdir -p "$ETC_DIR"
    mkdir -p "$VAR_LIB_DIR"
    mkdir -p "$VAR_LOG_DIR"
    mkdir -p "$BACKUP_DIR"
}

set_permissions() {
    chmod 0755 "$PREFIX"
    chmod 0755 "$PREFIX/tools"
    chmod 0755 "$PREFIX/backups"
    chmod 0755 "$ETC_DIR"
    chmod 0700 "$VAR_LIB_DIR"
    chmod 0755 "$VAR_LOG_DIR"
    chmod 0700 "$BACKUP_DIR"
}

atomic_write() {
    local file_path="$1"
    local content="$2"
    local tmp_file="${file_path}.tmp_$$"
    printf '%s' "$content" > "$tmp_file"
    chmod --reference="$file_path" "$tmp_file" 2>/dev/null || chmod 0644 "$tmp_file"
    mv "$tmp_file" "$file_path"
}

copy_with_excludes() {
    local src="$1"
    local dst="$2"
    mkdir -p "$dst"
    tar -C "$src" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.tmp' \
        --exclude='backups' \
        --exclude='quarantine' \
        --exclude='adie' \
        --exclude='intelligence' \
        --exclude='src' \
        -cf - . | tar -C "$dst" -xf -
}

copy_project_files() {
    copy_with_excludes "$ROOT_DIR" "$PREFIX"
}

install_service_unit() {
    local service_content
    service_content="[Unit]
Description=EnterpriseGuard ADIE Sovereign Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 -B $PREFIX/tools/checklist.py
StandardOutput=journal
StandardError=journal

# Security hardening
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true
InaccessiblePaths=/root/.enterpriseguard

[Install]
WantedBy=multi-user.target"

    atomic_write "/etc/systemd/system/${SERVICE_NAME}.service" "$service_content"

    systemctl daemon-reload
    systemctl disable ${SERVICE_NAME}.service >/dev/null 2>&1 || true
}

install_config() {
    local conf_content
    conf_content="install_root = $PREFIX
tools_dir = $PREFIX/tools
etc_dir = $ETC_DIR
var_lib_dir = $VAR_LIB_DIR
var_log_dir = $VAR_LOG_DIR"
    atomic_write "$ETC_DIR/enterpriseguard.conf" "$conf_content"

    # Copy Genesis public key if available
    if [ -f "$ROOT_DIR/tools/genesis_public_key.pem" ]; then
        cp "$ROOT_DIR/tools/genesis_public_key.pem" "$ETC_DIR/genesis_public_key.pem"
        chmod 0444 "$ETC_DIR/genesis_public_key.pem"
    fi

    # Copy regular ring public key to system config (so root can verify)
    local regular_pub_key=""
    if [ -f "$HOME/.enterpriseguard/keys/public_key.pem" ]; then
        regular_pub_key="$HOME/.enterpriseguard/keys/public_key.pem"
    else
        # Search common user home directories
        for h in /home/*/.enterpriseguard/keys/public_key.pem /root/.enterpriseguard/keys/public_key.pem; do
            if [ -f "$h" ]; then
                regular_pub_key="$h"
                break
            fi
        done
    fi

    if [ -n "$regular_pub_key" ]; then
        cp "$regular_pub_key" "$ETC_DIR/public_key.pem"
        chmod 0444 "$ETC_DIR/public_key.pem"
        echo "Regular ring public key copied to $ETC_DIR/public_key.pem"
    else
        echo "WARNING: regular ring public key not found; verify-chain may fail as root."
    fi
}

create_wrapper_script() {
    local wrapper_content
    wrapper_content="#!/usr/bin/env bash
export PYTHONDONTWRITEBYTECODE=1
PREFIX=\"$PREFIX\"
case \"\${1:-}\" in
    status)
        echo \"EnterpriseGuard installed at $PREFIX\"
        ;;
    check)
        cd \"$PREFIX\" && python3 -B tools/checklist.py
        ;;
    collect)
        cd \"$PREFIX\" && python3 -B tools/dimensional_collector.py
        ;;
    decide)
        cd \"$PREFIX\" && python3 -B tools/dimensional_decision_engine.py
        ;;
    verify-chain)
        cd \"$PREFIX\" && python3 -B tools/innocence_chain.py --verify
        ;;
    generate-ring)
        cd \"$PREFIX\" && python3 -B tools/innocence_chain.py --generate
        ;;
    install|uninstall)
        echo \"Use install.sh script for install/uninstall operations.\"
        ;;
    *)
        echo \"Usage: enterpriseguard {status|check|collect|decide|verify-chain|generate-ring}\"
        exit 1
        ;;
esac"
    atomic_write "$BIN_PATH" "$wrapper_content"
    chmod 0755 "$BIN_PATH"
}

do_install() {
    require_root
    is_safe_prefix || die "Unsafe prefix: $PREFIX"
    echo "Installing EnterpriseGuard to $PREFIX ..."
    create_dirs
    copy_project_files
    set_permissions
    install_config
    install_service_unit
    create_wrapper_script

    touch "$PREFIX/$MARKER"

    echo "EnterpriseGuard installed successfully to $PREFIX"
    echo "Service is disabled by default. To enable: sudo systemctl enable --now enterpriseguard"
}

do_check() {
    echo "Checking EnterpriseGuard installation at $PREFIX ..."
    is_safe_prefix || die "Unsafe prefix: $PREFIX"
    [ -d "$PREFIX/tools" ] || die "Missing $PREFIX/tools"
    [ -f "$ETC_DIR/enterpriseguard.conf" ] || die "Missing config"
    [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ] || die "Missing service unit"
    [ -f "$BIN_PATH" ] || die "Missing CLI wrapper"
    [ -f "$PREFIX/$MARKER" ] || die "Installation marker missing (wrong prefix?)"
    echo "Check passed."
}

do_uninstall() {
    require_root
    is_safe_prefix || die "Unsafe prefix: $PREFIX"
    [ -f "$PREFIX/$MARKER" ] || die "Refusing to delete: installation marker not found at $PREFIX"

    echo "Uninstalling EnterpriseGuard from $PREFIX ..."
    systemctl disable ${SERVICE_NAME}.service >/dev/null 2>&1 || true
    rm -f /etc/systemd/system/${SERVICE_NAME}.service
    systemctl daemon-reload
    rm -f "$BIN_PATH"
    rm -rf "$PREFIX"
    rm -rf "$ETC_DIR"
    rm -rf "$VAR_LIB_DIR"
    rm -rf "$VAR_LOG_DIR"
    echo "Uninstalled."
}

# Main logic
if [ -z "$ACTION" ]; then
    echo "Usage: $0 [--install|--check|--uninstall] [--prefix /path]"
    exit 1
fi

shift || true
while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)
            PREFIX="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

case "$ACTION" in
    --install) do_install ;;
    --check)   do_check ;;
    --uninstall) do_uninstall ;;
    *) die "Unknown action: $ACTION" ;;
esac
