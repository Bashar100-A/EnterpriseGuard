//! ADIE ML-DSA-65 wrapper (Phase 2, Block D.2).
//!
//! FIPS 204 deterministic (Sign_deterministic mode).
//! ctx is a caller-supplied context string per FIPS 204 §5.2.
//! For ADIE protocol signing, the caller passes ctx = b"" and
//! includes "ADIE-SIG-V2\0" as a prefix of M.
//!
//! RISK-2.1: ml-dsa 0.1.1 (RustCrypto) is pre-1.0 and self-declared
//! unaudited. This wrapper is a thin boundary only.

use ml_dsa::{
    MlDsa65, Keypair, Signature, SigningKey, VerifyingKey, Seed,
    EncodedVerifyingKey, EncodedSignature,
};

pub const MLDSA65_PUBKEY_BYTES: usize = 1952;
pub const MLDSA65_SECSEED_BYTES: usize = 32;
pub const MLDSA65_SECKEY_BYTES: usize = 4032;
pub const MLDSA65_SIGNATURE_BYTES: usize = 3309;

pub fn keygen_from_seed(
    seed: &[u8; MLDSA65_SECSEED_BYTES],
) -> Result<[u8; MLDSA65_PUBKEY_BYTES], String> {
    let s = Seed::try_from(&seed[..]).map_err(|e| format!("seed: {:?}", e))?;
    let sk = SigningKey::<MlDsa65>::from_seed(&s);
    let vk = sk.verifying_key();
    let pk_enc: EncodedVerifyingKey<MlDsa65> = vk.encode();
    let pk_slice = pk_enc.as_slice();
    if pk_slice.len() != MLDSA65_PUBKEY_BYTES {
        return Err(format!("pk len {} != {}", pk_slice.len(), MLDSA65_PUBKEY_BYTES));
    }
    let mut out = [0u8; MLDSA65_PUBKEY_BYTES];
    out.copy_from_slice(pk_slice);
    Ok(out)
}

pub fn sign_deterministic_ctx(
    seed: &[u8; MLDSA65_SECSEED_BYTES],
    msg: &[u8],
    ctx: &[u8],
) -> Result<Vec<u8>, String> {
    let s = Seed::try_from(&seed[..]).map_err(|e| format!("seed: {:?}", e))?;
    let sk = SigningKey::<MlDsa65>::from_seed(&s);
    let expanded = sk.expanded_key();
    let sig: Signature<MlDsa65> = expanded
        .sign_deterministic(msg, ctx)
        .map_err(|e| format!("sign: {:?}", e))?;
    Ok(sig.encode().as_slice().to_vec())
}

pub fn verify_with_ctx(
    pk_bytes: &[u8],
    msg: &[u8],
    ctx: &[u8],
    sig_bytes: &[u8],
) -> Result<bool, String> {
    let pk_enc = EncodedVerifyingKey::<MlDsa65>::try_from(pk_bytes)
        .map_err(|_| format!("pk len: expected {}, got {}", MLDSA65_PUBKEY_BYTES, pk_bytes.len()))?;
    let vk = VerifyingKey::<MlDsa65>::decode(&pk_enc);

    // Per FIPS 204 ML-DSA.Verify: if signature decoding fails, the
    // signature is REJECTED (verification returns false). Do not
    // propagate as Err — that would confuse the verify semantics.
    let sig_enc = match EncodedSignature::<MlDsa65>::try_from(sig_bytes) {
        Ok(e) => e,
        Err(_) => return Ok(false),  // wrong length → invalid
    };
    let sig = match Signature::<MlDsa65>::decode(&sig_enc) {
        Some(s) => s,
        None => return Ok(false),  // out-of-range z → invalid
    };

    Ok(vk.verify_with_context(msg, ctx, &sig))
}

// Legacy convenience for ADIE protocol (ctx = b"").
pub fn sign_deterministic(
    seed: &[u8; MLDSA65_SECSEED_BYTES],
    tbs: &[u8],
) -> Result<Vec<u8>, String> {
    sign_deterministic_ctx(seed, tbs, b"")
}

pub fn verify(pk_bytes: &[u8], tbs: &[u8], sig_bytes: &[u8]) -> Result<bool, String> {
    verify_with_ctx(pk_bytes, tbs, b"", sig_bytes)
}
