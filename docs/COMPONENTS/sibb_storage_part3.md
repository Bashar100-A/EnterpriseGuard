# Component: sibb_storage.py — Part 3/3 (Operations & Public API)

**Continues from:** sibb_storage_part2.md (part 2/3)

---

## Public API

### Constructor

    WORMStorage(
        base_path: Path,
        encrypt: bool = False,
        master_password: Optional[str] = None,
        hmac_key_path: Optional[Path] = None,
        use_os_immutable: bool = True,
        access_key: Optional[str] = None,
        hmac_key_encrypt: bool = False,
        handle_orphans: bool = False
    )

### Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| write(data, filename, metadata) | Write new file (WORM) | SHA-256 hash |
| read(filename) | Read + verify integrity | (data, metadata) |
| verify_integrity(filename=None) | Verify one or all files | dict |
| list_files() | List all stored files | list |
| get_metadata(filename) | Get metadata for one file | dict or None |
| get_status() | Storage status | dict |

## Operations Flow

### write(data, filename)

1. Validate filename via _sanitize_path (no traversal, no symlink)
2. Acquire metadata lock (fcntl/msvcrt)
3. Reload metadata from disk (fresh)
4. Check: file must not exist (WORM)
5. Open with O_CREAT | O_EXCL | O_NOFOLLOW
6. If encrypted: generate 16-byte salt, derive file key via HKDF
7. Write full I/O loop + fsync
8. chmod 0444, then _make_immutable (chattr +i on Linux)
9. Update metadata + HMAC + backup (atomic write)
10. Release lock

### read(filename)

1. Validate filename
2. Acquire metadata lock
3. Reload metadata from disk
4. Find metadata entry; raise if missing
5. Open with O_RDONLY | O_NOFOLLOW
6. Full I/O loop
7. If encrypted: derive file key from stored salt, decrypt via Fernet
8. Verify SHA-256 hash matches metadata
9. Return (data, metadata)

### verify_integrity(filename=None)

1. Reload metadata
2. For each stored file: check existence + hash
3. Scan for unexpected files (not in metadata)
4. Return: {verified, failed, unexpected, total, valid}

## Error Handling

All errors raise WORMStorageError.

| Scenario | Behavior |
|----------|----------|
| File exists | Raise: "File already exists (WORM)" |
| Hash mismatch | Raise: "Hash mismatch for X" |
| Metadata HMAC fail | Fallback to backup; if backup fails, raise |
| File missing | Raise: "File not found" |

## Concurrency

- Cross-process: fcntl.flock (Linux/macOS) or msvcrt.locking (Windows)
- Cross-thread: threading.RLock
- Each thread gets its own file descriptor via threading.local()

## Helper Function

    create_worm_storage(base_path, encrypt=False, password=None,
                        hmac_key_path=None, use_os_immutable=True,
                        access_key=None, hmac_key_encrypt=False,
                        handle_orphans=False) -> WORMStorage

## Integration

Used by:
- sibb_distributed.py (each node is a WORMStorage)
- sibb_cli.py (user-facing CLI)
- sibb_innocence_integration.py (stores ring envelopes)

**End of Part 3/3**
