//! ADIE RSA verification wrapper (Phase 3, Gate 0).
//!
//! Only module allowed to depend on the `rsa` crate. Verifier code
//! calls `verify_rs256_pkcs1v15(pub_pem, tbs, sig_bytes)` and gets
//! a bool.
//!
//! RISK-3.1 (updated): using mainline `rsa 0.9.6` (RustCrypto) which
//! has RUSTSEC-2023-0071 (Marvin attack) open on PKCS#1 v1.5
//! DECRYPTION. ADIE's usage is VERIFICATION only, offline. The
//! Marvin attack requires an interactive decryption oracle and
//! targets the private key; it does not apply to public-key
//! verification. Documented in docs/vomega/DEFECTS-LOG.md.
//!
//! RISK-3.2 (updated): dependency surface ~30 crates.
//! Replaces the sad-rsa attempt (DEFECT-015: sad-rsa 0.10.2 fails
//! to build against pkcs1 0.8.0-rc.5).
//!
//! Isolated by design: replacing `rsa` with a different crate
//! requires changing only this file.

use rsa::{
    pkcs1v15::{Signature, VerifyingKey},
    pkcs8::DecodePublicKey,
    signature::Verifier,
    sha2::Sha256,
    RsaPublicKey,
};

pub const RSA2048_SIGNATURE_BYTES: usize = 256;

/// Verify an RS256 (RSASSA-PKCS1-v1_5 with SHA-256) signature.
///
/// Returns:
///   Ok(true)   -- signature is valid.
///   Ok(false)  -- signature is invalid (bad length, bad padding,
///                 wrong key, tampered message).
///   Err(...)   -- the public key itself could not be parsed.
///
/// Invalid signatures do NOT return Err. They return Ok(false),
/// matching Python's behavior and the ML-DSA path (DEFECT-012).
pub fn verify_rs256_pkcs1v15(
    pub_pem: &[u8],
    tbs: &[u8],
    sig_bytes: &[u8],
) -> Result<bool, String> {
    // Parse the public key from PEM.
    let pubkey = RsaPublicKey::from_public_key_pem(
        std::str::from_utf8(pub_pem)
            .map_err(|e| format!("pem not utf8: {}", e))?,
    )
    .map_err(|e| format!("pem parse: {}", e))?;

    // Build a SHA-256 verifying key.
    let vk: VerifyingKey<Sha256> = VerifyingKey::new(pubkey);

    // Convert signature bytes. Wrong length -> invalid.
    let sig_arr: [u8; RSA2048_SIGNATURE_BYTES] = match sig_bytes.try_into() {
        Ok(a) => a,
        Err(_) => return Ok(false),
    };
    let sig = match Signature::try_from(&sig_arr[..]) {
        Ok(s) => s,
        Err(_) => return Ok(false),
    };

    // Verify. Failure -> Ok(false).
    match vk.verify(tbs, &sig) {
        Ok(()) => Ok(true),
        Err(_) => Ok(false),
    }
}
