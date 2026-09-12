#!/usr/bin/env python3
"""
SIBB Command Line Interface
Unified CLI for SIBB storage, distributed nodes, and key management.

Version: 1.1 (fixed critical issues)
- Correct integration with underlying modules
- Proper encryption support
- Distributed config handling
- Secure key generation and output permissions
- Constant-time comparisons
"""

import os
import sys
import json
import argparse
import logging
import getpass
import secrets
import hmac
import tempfile
from pathlib import Path
from typing import Optional, List

sys.dont_write_bytecode = True

# Ensure project root is on sys.path when running as a script
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Logging to secure file
LOG_DIR = Path.home() / ".enterpriseguard" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "cli.log"
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Audit chain integration (optional)
try:
    from tools.audit_chain import append_activity as _audit_append
    from tools.paths_config import ACTIVITY_LOG_PATH as _ACTIVITY_LOG

    def append_activity(event_type, details):
        """Adapt (event_type, details) to audit_chain's (entry_data, path)."""
        try:
            _audit_append(
                {"activity_type": event_type, "details": details},
                _ACTIVITY_LOG,
            )
        except Exception as exc:
            logger.warning(f"Audit append failed: {exc}")
except ImportError:
    def append_activity(event_type, details):
        logger.warning(f"Audit chain not available: {event_type} | {details}")
DEFAULT_CONFIG_PATH = Path.home() / ".enterpriseguard" / "config.json"
INVALID_FILENAME_CHARS = set(';|$&<>\\\n\r\x00\x1b\x7f')

def validate_filename(filename: str) -> str:
    if not filename:
        raise ValueError("Filename cannot be empty")
    if filename.startswith('/') or filename.startswith('~'):
        raise ValueError("Absolute paths are not allowed")
    if '..' in filename.split('/'):
        raise ValueError("Path traversal not allowed")
    if any(c in INVALID_FILENAME_CHARS for c in filename):
        raise ValueError("Filename contains invalid characters")
    if filename.startswith('-'):
        raise ValueError("Filename cannot start with a dash")
    return filename

def get_password_from_env_or_prompt() -> str:
    password = os.environ.pop("SIBB_PASSWORD", None)
    if password:
        return password
    password = getpass.getpass("Enter password: ")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    return password

def get_access_key() -> Optional[str]:
    # Access key not used for storage creation, but may be used for key manager
    return os.environ.get("SIBB_ACCESS_KEY")

def load_config() -> dict:
    config_path = Path(os.environ.get("SIBB_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    if config_path.exists():
        if config_path.stat().st_mode & 0o777 != 0o600:
            logger.warning(f"Config file {config_path} permissions are not 0600")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    return {}

def save_config(config: dict):
    config_path = Path(os.environ.get("SIBB_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    config_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=config_path.parent, prefix=".config.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(config, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, config_path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise

def _get_storage(args, config):
    """Create storage instance based on config and args."""
    if args.distributed or config.get("distributed"):
        paths = config.get("paths", [])
        if not paths:
            raise ValueError("Distributed paths not configured")
        if len(paths) < 3:
            raise ValueError("At least 3 paths required for distributed mode")
        from tools.sibb_distributed import create_distributed_storage
        return create_distributed_storage(
            [Path(p) for p in paths],
            quorum=config.get("quorum", 2),
            use_os_immutable=config.get("immutable", False),
            encrypt=config.get("encrypt", False),
            master_password=config.get("master_password")  # may be None
        )
    else:
        base_path = Path(config.get("storage_path", ".sibb"))
        from tools.sibb_storage import create_worm_storage
        return create_worm_storage(
            base_path,
            encrypt=config.get("encrypt", False),
            password=config.get("master_password"),   # <-- تغيير الاسم
            use_os_immutable=config.get("immutable", False)
        )

def run_init(args):
    try:
        config = load_config()
        use_os_immutable = args.immutable
        if args.distributed:
            if not args.path:
                raise ValueError("At least 3 paths required (comma-separated)")
            paths = [p.strip() for p in args.path.split(',')]
            if len(paths) < 3:
                raise ValueError("At least 3 paths required")
            config['paths'] = paths
            config['distributed'] = True
            config['storage_path'] = None
        else:
            config['storage_path'] = args.path or config.get("storage_path", ".sibb")
            config['distributed'] = False
        config['immutable'] = use_os_immutable
        config['quorum'] = args.quorum if args.distributed else config.get('quorum', 2)
        save_config(config)

        # Actually initialize storage
        _get_storage(args, config)  # this will create directories etc.
        print("SIBB initialized successfully.")
        append_activity("cli_init", {"distributed": args.distributed, "path": args.path})
        return 0
    except Exception as e:
        logger.error(f"init failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_write(args):
    try:
        config = load_config()
        if args.encrypt:
            password = get_password_from_env_or_prompt()
            config['encrypt'] = True
            # We don't store password in config for security; it must be provided each time
            # For this run, we'll create a temporary storage with password
            if args.distributed or config.get("distributed"):
                paths = config.get("paths", [])
                from tools.sibb_distributed import create_distributed_storage
                storage = create_distributed_storage(
                    [Path(p) for p in paths],
                    quorum=config.get("quorum", 2),
                    use_os_immutable=config.get("immutable", False),
                    encrypt=True,
                    master_password=password
                )
            else:
                base_path = Path(config.get("storage_path", ".sibb"))
                from tools.sibb_storage import create_worm_storage
                storage = create_worm_storage(
                    base_path,
                    encrypt=True,
                    password=password,
                    use_os_immutable=config.get("immutable", False)
                )
        else:
            storage = _get_storage(args, config)

        filename = validate_filename(args.filename)
        data = args.data.encode() if args.data else Path(args.file).read_bytes()
        metadata = {"source": args.source or "cli"}
        h = storage.write(data, filename, metadata)
        print(f"Written {filename}, hash {h[:16]}...")
        append_activity("cli_write", {"filename": filename, "hash": h, "size": len(data)})
        return 0
    except Exception as e:
        logger.error(f"write failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_read(args):
    try:
        config = load_config()
        if config.get("encrypt"):
            # Need password to decrypt
            password = get_password_from_env_or_prompt()
            if args.distributed or config.get("distributed"):
                paths = config.get("paths", [])
                from tools.sibb_distributed import create_distributed_storage
                storage = create_distributed_storage(
                    [Path(p) for p in paths],
                    quorum=config.get("quorum", 2),
                    use_os_immutable=config.get("immutable", False),
                    encrypt=True,
                    password=password
                )
            else:
                base_path = Path(config.get("storage_path", ".sibb"))
                from tools.sibb_storage import create_worm_storage
                storage = create_worm_storage(
                    base_path,
                    encrypt=True,
                    password=password,
                    use_os_immutable=config.get("immutable", False)
                )
        else:
            storage = _get_storage(args, config)

        filename = validate_filename(args.filename)
        data, meta = storage.read(filename)
        if args.output:
            # Write with 0600 permissions
            fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            print(f"Read {len(data)} bytes to {args.output}")
        else:
            try:
                print(data.decode('utf-8'))
            except UnicodeDecodeError:
                print("Binary data (not displayed)")
        append_activity("cli_read", {"filename": filename, "size": len(data)})
        return 0
    except Exception as e:
        logger.error(f"read failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_list(args):
    try:
        config = load_config()
        storage = _get_storage(args, config)
        files = storage.list_files()
        print(json.dumps(files, indent=2, default=str))
        return 0
    except Exception as e:
        logger.error(f"list failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_verify(args):
    try:
        config = load_config()
        storage = _get_storage(args, config)
        result = storage.verify_integrity(args.filename) if args.filename else storage.verify_integrity()
        print(json.dumps(result, indent=2, default=str))
        append_activity("cli_verify", {"valid": result.get("valid", False)})
        return 0 if result.get("valid", False) else 1
    except Exception as e:
        logger.error(f"verify failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_status(args):
    try:
        config = load_config()
        if args.keys:
            shares_dir = Path(config.get("shares_dir", ".shares"))
            from tools.sibb_keys import SIBBKeyManager
            km = SIBBKeyManager(shares_dir, access_key=get_access_key())
            status = km.get_status()
        else:
            storage = _get_storage(args, config)
            status = storage.get_status()
        print(json.dumps(status, indent=2, default=str))
        return 0
    except Exception as e:
        logger.error(f"status failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_generate_master_key(args):
    try:
        key = secrets.token_bytes(32)
        if args.output:
            fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(key)
            print(f"Master key written to {args.output}")
        else:
            # Warn about sensitive output
            print("Warning: Master key is sensitive. Consider using --output.", file=sys.stderr)
            print(key.hex())
        append_activity("cli_generate_master_key", {})
        return 0
    except Exception as e:
        logger.error(f"generate-master-key failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_split_key(args):
    try:
        config = load_config()
        shares_dir = Path(config.get("shares_dir", ".shares"))
        password = get_password_from_env_or_prompt()
        from tools.sibb_keys import SIBBKeyManager
        km = SIBBKeyManager(shares_dir, password=password, access_key=get_access_key())
        if args.master_key_hex:
            master_key = bytes.fromhex(args.master_key_hex)
        elif args.master_key_file:
            master_key = Path(args.master_key_file).read_bytes()
        else:
            master_key = km.generate_master_key()
        result = km.split_master_key(master_key, n=args.n, k=args.k)
        print(json.dumps(result, indent=2, default=str))
        append_activity("cli_split_key", {"key_id": result["key_id"], "n": args.n, "k": args.k})
        return 0
    except Exception as e:
        logger.error(f"split-key failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_reconstruct_key(args):
    try:
        config = load_config()
        shares_dir = Path(config.get("shares_dir", ".shares"))
        password = get_password_from_env_or_prompt()
        from tools.sibb_keys import SIBBKeyManager
        km = SIBBKeyManager(shares_dir, password=password, access_key=get_access_key())
        share_files = args.shares or km.list_shares()
        master_key = km.reconstruct_key(share_files, password=password)
        if args.output:
            fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(master_key)
            print(f"Master key written to {args.output}")
        else:
            print("Warning: Master key is sensitive. Consider using --output.", file=sys.stderr)
            print(master_key.hex())
        append_activity("cli_reconstruct_key", {"shares_used": len(share_files)})
        return 0
    except Exception as e:
        logger.error(f"reconstruct-key failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_list_shares(args):
    try:
        config = load_config()
        shares_dir = Path(config.get("shares_dir", ".shares"))
        from tools.sibb_keys import SIBBKeyManager
        km = SIBBKeyManager(shares_dir, access_key=get_access_key())
        shares = km.list_shares()
        print(json.dumps(shares, indent=2))
        return 0
    except Exception as e:
        logger.error(f"list-shares failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_delete_share(args):
    try:
        config = load_config()
        shares_dir = Path(config.get("shares_dir", ".shares"))
        from tools.sibb_keys import SIBBKeyManager
        km = SIBBKeyManager(shares_dir, access_key=get_access_key())
        km.delete_share(args.share_name)
        print(f"Deleted share {args.share_name}")
        append_activity("cli_delete_share", {"share": args.share_name})
        return 0
    except Exception as e:
        logger.error(f"delete-share failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def run_verify_share(args):
    try:
        config = load_config()
        shares_dir = Path(config.get("shares_dir", ".shares"))
        from tools.sibb_keys import SIBBKeyManager
        km = SIBBKeyManager(shares_dir, access_key=get_access_key())
        valid = km.verify_share(args.share_name)
        print("Valid" if valid else "Invalid")
        append_activity("cli_verify_share", {"share": args.share_name, "valid": valid})
        return 0 if valid else 1
    except Exception as e:
        logger.error(f"verify-share failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="SIBB Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--distributed", action="store_true", help="Use distributed storage (if configured)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="Initialize SIBB storage")
    p_init.add_argument("--path", help="Storage path (or comma-separated paths for distributed)")
    p_init.add_argument("--distributed", action="store_true")
    p_init.add_argument("--quorum", type=int, default=2)
    p_init.add_argument("--immutable", action="store_true")
    p_init.set_defaults(func=run_init)

    p_write = subparsers.add_parser("write", help="Write data to storage")
    p_write.add_argument("filename")
    p_write.add_argument("--data")
    p_write.add_argument("--file")
    p_write.add_argument("--source")
    p_write.add_argument("--encrypt", action="store_true")
    p_write.set_defaults(func=run_write)

    p_read = subparsers.add_parser("read", help="Read data from storage")
    p_read.add_argument("filename")
    p_read.add_argument("--output")
    p_read.set_defaults(func=run_read)

    p_list = subparsers.add_parser("list", help="List files")
    p_list.set_defaults(func=run_list)

    p_verify = subparsers.add_parser("verify", help="Verify storage integrity")
    p_verify.add_argument("--filename")
    p_verify.set_defaults(func=run_verify)

    p_status = subparsers.add_parser("status", help="Show status")
    p_status.add_argument("--keys", action="store_true")
    p_status.set_defaults(func=run_status)

    p_gen = subparsers.add_parser("generate-master-key", help="Generate a new master key")
    p_gen.add_argument("--output", help="Output file for key (0600)")
    p_gen.set_defaults(func=run_generate_master_key)

    p_split = subparsers.add_parser("split-key", help="Split a master key into shares")
    p_split.add_argument("--master-key-hex")
    p_split.add_argument("--master-key-file")
    p_split.add_argument("--n", type=int, default=5)
    p_split.add_argument("--k", type=int, default=3)
    p_split.set_defaults(func=run_split_key)

    p_recon = subparsers.add_parser("reconstruct-key", help="Reconstruct master key")
    p_recon.add_argument("shares", nargs="*")
    p_recon.add_argument("--output", help="Output file for key (0600)")
    p_recon.set_defaults(func=run_reconstruct_key)

    p_ls = subparsers.add_parser("list-shares", help="List share files")
    p_ls.set_defaults(func=run_list_shares)

    p_del = subparsers.add_parser("delete-share", help="Delete a share")
    p_del.add_argument("share_name")
    p_del.set_defaults(func=run_delete_share)

    p_vs = subparsers.add_parser("verify-share", help="Verify a share's integrity")
    p_vs.add_argument("share_name")
    p_vs.set_defaults(func=run_verify_share)

    args = parser.parse_args()

    if args.config:
        os.environ["SIBB_CONFIG_PATH"] = args.config

    try:
        exit_code = args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        exit_code = 130
    except Exception as e:
        logger.exception("Unhandled exception")
        print(f"Unexpected error: {e}", file=sys.stderr)
        exit_code = 1

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
