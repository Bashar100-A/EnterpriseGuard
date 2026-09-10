# Component: sibb_storage.py — Part 2/3 (Encryption & Key Management)

**Continues from:** sibb_storage.md (part 1/3)

---

## Encryption Architecture

### Optional (disabled by default)

- Activated by: `encrypt=True, master_password=<12+ chars>`
- Algorithm: AES via Fernet (AES-128-CBC + HMAC-SHA256)
- Per-file keys: derived via HKDF from master key + random 16-byte salt

### Key Derivation Chain

user_password (>=12 chars)
|
v PBKDF2-HMAC-SHA256 (480,000 iterations)
v salt = .worm_salt.bin (32 bytes, chmod 0600)
|
v
master_key (32 bytes)
|
+------> HKDF(salt=file_salt, info="SIBB_FILE_ENCRYPTION_KEY")
| |
| v
| per-file key (32 bytes)
| |
| v
| Fernet (encrypt/decrypt file)
|
+------> HKDF(salt=worm_salt, info="SIBB_HMAC_KEY_ENCRYPTION")
|
v
hmac_key_encryption_key (32 bytes)
|
v
encrypts/decrypts .worm_hmac_key.bin
text


## Files Managed

| File | Purpose | Permissions |
|------|---------|-------------|
| .worm_salt.bin | PBKDF2 salt | 0600 |
| .worm_hmac_key.bin | HMAC key (independent) | 0600 |
| <data file> | Encrypted or plaintext data | 0444 |
| .worm_metadata.json | File index | 0600 |
| .worm_metadata.hmac | Metadata HMAC | 0600 |
| .worm_metadata.backup.json | Backup | 0600 |
| .worm_metadata.hmac.backup | Backup HMAC | 0600 |

## Key Rotation

- Salt: fixed after creation. Corruption raises error (no silent regeneration).
- HMAC key: independent of password. Can be rotated via re-initialization.
- Master key: derived per session. Not stored on disk.

## Failure Modes (Fail-Secure)

| Failure | Behavior |
|---------|----------|
| Wrong password | Read operations fail with WORMStorageError |
| Corrupted salt | Initialization fails (no silent regeneration) |
| Missing HMAC key | Fail (no regeneration without explicit re-init) |
| Corrupted metadata HMAC | Fail, fallback to backup |
| Both primary+backup corrupted | Refuse to operate |

## Tests

Covered in tests/test_sibb_storage.py:
- test_encryption_roundtrip
- test_encryption_wrong_password
- test_encryption_short_password_rejected
- test_salt_tampering_detected_on_new_instance
- test_hmac_key_permissions

**End of Part 2/3**
