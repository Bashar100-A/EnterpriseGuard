import os
import sys
import json
import getpass
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import sibb_cli
from tools.sibb_cli import validate_filename, load_config, save_config, get_password_from_env_or_prompt

# ==================== Fixtures ====================

@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    """Create a temporary config file."""
    config_path = tmp_path / "config.json"
    config = {"storage_path": str(tmp_path / "storage")}
    with open(config_path, 'w') as f:
        json.dump(config, f)
    monkeypatch.setenv("SIBB_CONFIG_PATH", str(config_path))
    return config_path

# ==================== Basic Validation ====================

def test_validate_filename_valid():
    assert validate_filename("test.txt") == "test.txt"

def test_validate_filename_invalid_chars():
    invalid = [';', '|', '$', '&', '<', '>', '\\', '\n', '\r', '\x00', '\x1b', '\x7f']
    for char in invalid:
        with pytest.raises(ValueError):
            validate_filename(f"bad{char}name")

def test_validate_filename_path_traversal():
    with pytest.raises(ValueError):
        validate_filename("../evil.txt")
    with pytest.raises(ValueError):
        validate_filename("/abs/path.txt")
    with pytest.raises(ValueError):
        validate_filename("~user/file.txt")

def test_validate_filename_leading_dash():
    with pytest.raises(ValueError):
        validate_filename("-file.txt")

# ==================== Password Handling ====================

def test_get_password_from_env(monkeypatch):
    monkeypatch.setenv("SIBB_PASSWORD", "StrongPass123!")
    password = get_password_from_env_or_prompt()
    assert password == "StrongPass123!"
    # Check that env var was removed
    assert "SIBB_PASSWORD" not in os.environ

def test_get_password_from_prompt(monkeypatch):
    monkeypatch.delenv("SIBB_PASSWORD", raising=False)
    with patch('getpass.getpass', return_value="StrongPass123!"):
        password = get_password_from_env_or_prompt()
        assert password == "StrongPass123!"

def test_get_password_too_short(monkeypatch):
    monkeypatch.delenv("SIBB_PASSWORD", raising=False)
    with patch('getpass.getpass', return_value="short"):
        with pytest.raises(ValueError):
            get_password_from_env_or_prompt()

# ==================== Config Handling ====================

def test_load_config_missing(temp_config):
    config = load_config()
    assert config["storage_path"] == str(Path(temp_config).parent / "storage")

def test_load_config_invalid_json(tmp_path, monkeypatch):
    bad_config = tmp_path / "bad_config.json"
    bad_config.write_text("{invalid json")
    monkeypatch.setenv("SIBB_CONFIG_PATH", str(bad_config))
    config = load_config()
    assert config == {}

def test_save_config_permissions(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("SIBB_CONFIG_PATH", str(config_path))
    save_config({"storage_path": "/tmp/storage"})
    assert config_path.exists()
    assert config_path.stat().st_mode & 0o777 == 0o600

# ==================== Command Execution (Integration) ====================

def test_init_local_storage(temp_config, tmp_path, monkeypatch):
    from tools.sibb_cli import run_init
    args = argparse.Namespace(distributed=False, path=None, immutable=False, quorum=2)
    with patch('tools.sibb_cli.append_activity') as mock_audit:
        ret = run_init(args)
    assert ret == 0
    storage_path = Path(load_config()["storage_path"])
    assert storage_path.exists()
    mock_audit.assert_called()

def test_write_and_read(temp_config, tmp_path, monkeypatch):
    from tools.sibb_cli import run_init, run_write, run_read
    args_init = argparse.Namespace(distributed=False, path=None, immutable=False, quorum=2)
    with patch('tools.sibb_cli.append_activity'):
        assert run_init(args_init) == 0

    args_write = argparse.Namespace(
        filename="test.txt", data="hello", file=None, source="test", encrypt=False,
        distributed=False, quorum=2, immutable=False
    )
    with patch('tools.sibb_cli.append_activity'):
        ret = run_write(args_write)
    assert ret == 0

    args_read = argparse.Namespace(filename="test.txt", output=None, distributed=False, quorum=2)
    with patch('tools.sibb_cli.append_activity'):
        ret = run_read(args_read)
    assert ret == 0

def test_write_rejects_invalid_filename(temp_config):
    from tools.sibb_cli import run_write
    args = argparse.Namespace(
        filename="../evil.txt", data="x", file=None, source=None, encrypt=False,
        distributed=False, quorum=2, immutable=False
    )
    with patch('tools.sibb_cli.append_activity'):
        ret = run_write(args)
    assert ret == 1

def test_encrypt_write_requires_password(temp_config, monkeypatch):
    from tools.sibb_cli import run_write
    args = argparse.Namespace(
        filename="test.txt", data="secret", file=None, source=None, encrypt=True,
        distributed=False, quorum=2, immutable=False
    )
    # Patch get_password_from_env_or_prompt to avoid interactive prompt
    with patch('tools.sibb_cli.get_password_from_env_or_prompt', return_value="StrongPass123!"):
        # Patch the storage creation function to verify arguments
        with patch('tools.sibb_storage.create_worm_storage') as mock_create:
            mock_storage = MagicMock()
            mock_create.return_value = mock_storage
            with patch('tools.sibb_cli.append_activity'):
                ret = run_write(args)
            assert ret == 0
            # Verify that create_worm_storage was called with encrypt=True and master_password
            mock_create.assert_called_once_with(
    Path(load_config()["storage_path"]),
    encrypt=True,
    password="StrongPass123!",
    use_os_immutable=False
)

def test_generate_master_key_output_file(tmp_path):
    from tools.sibb_cli import run_generate_master_key
    output_file = tmp_path / "key.bin"
    args = argparse.Namespace(output=str(output_file))
    with patch('tools.sibb_cli.append_activity'):
        ret = run_generate_master_key(args)
    assert ret == 0
    assert output_file.exists()
    assert output_file.stat().st_mode & 0o777 == 0o600
    assert len(output_file.read_bytes()) == 32

def test_split_and_reconstruct_key(temp_config, tmp_path, monkeypatch):
    from tools.sibb_cli import run_split_key, run_reconstruct_key
    shares_dir = tmp_path / "shares"
    shares_dir.mkdir()
    config = load_config()
    config["shares_dir"] = str(shares_dir)
    save_config(config)

    # Split key
    args_split = argparse.Namespace(
        master_key_hex=None, master_key_file=None, n=5, k=3
    )
    with patch('tools.sibb_cli.get_password_from_env_or_prompt', return_value="StrongPass123!"):
        with patch('tools.sibb_cli.append_activity'):
            ret = run_split_key(args_split)
    assert ret == 0

    share_files = [f.name for f in shares_dir.glob("*.share")]
    assert len(share_files) == 5

    # Reconstruct key
    args_recon = argparse.Namespace(
        shares=share_files[:3], output=None
    )
    with patch('tools.sibb_cli.get_password_from_env_or_prompt', return_value="StrongPass123!"):
        with patch('tools.sibb_cli.append_activity'):
            ret = run_reconstruct_key(args_recon)
    assert ret == 0

def test_verify_share(temp_config, tmp_path):
    from tools.sibb_cli import run_split_key, run_verify_share
    shares_dir = tmp_path / "shares"
    shares_dir.mkdir()
    config = load_config()
    config["shares_dir"] = str(shares_dir)
    save_config(config)

    args_split = argparse.Namespace(master_key_hex=None, master_key_file=None, n=5, k=3)
    with patch('tools.sibb_cli.get_password_from_env_or_prompt', return_value="StrongPass123!"):
        with patch('tools.sibb_cli.append_activity'):
            run_split_key(args_split)

    share_file = list(shares_dir.glob("*.share"))[0].name
    args_verify = argparse.Namespace(share_name=share_file)
    with patch('tools.sibb_cli.append_activity'):
        ret = run_verify_share(args_verify)
    assert ret == 0

# ==================== Run tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
