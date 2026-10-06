//! ADIE ML-DSA-65 wrapper (Phase 2, Block D.1).
//!
//! Deterministic per FIPS 204 §3.6.3 (Sign_deterministic mode).
//! The context string (ctx) is empty; the ADIE domain separation tag
//! "ADIE-SIG-V2\0" is part of M per spec/HYBRID-CRYPTO-0.1 §5.
//!
//! RISK-2.1: ml-dsa 0.1.1 (RustCrypto) is pre-1.0 and self-declared
//! unaudited. This wrapper is a thin boundary only; it does not add
//! cryptographic logic.

use ml_dsa::{
    MlDsa65, Keypair, Signature, SigningKey, VerifyingKey, Seed,
    EncodedVerifyingKey, EncodedSignature,
};

pub const MLDSA65_PUBKEY_BYTES: usize = 1952;
pub const MLDSA65_SECSEED_BYTES: usize = 32;
pub const MLDSA65_SIGNATURE_BYTES: usize = 3309;

pub const SIGNING_CONTEXT: &[u8] = b"";

pub fn keygen_from_seed(
    seed: &[u8; MLDSA65_SECSEED_BYTES],
) -> Result<[u8; MLDSA65_PUBKEY_BYTES], String> {
    let s = Seed::try_from(&seed[..]).map_err(|e| format!("seed: {:?}", e))?;
    let sk = SigningKey::<MlDsa65>::from_seed(&s);
    let vk = sk.verifying_key();
    let pk_enc: EncodedVerifyingKey<MlDsa65> = vk.encode();
    let pk_slice = pk_enc.as_slice();
    if pk_slice.len() != MLDSA65_PUBKEY_BYTES {
        return Err(format!(
            "unexpected pk len: {} (expected {})",
            pk_slice.len(),
            MLDSA65_PUBKEY_BYTES
        ));
    }
    let mut out = [0u8; MLDSA65_PUBKEY_BYTES];
    out.copy_from_slice(pk_slice);
    Ok(out)
}

pub fn sign_deterministic(
    seed: &[u8; MLDSA65_SECSEED_BYTES],
    tbs: &[u8],
) -> Result<Vec<u8>, String> {
    let s = Seed::try_from(&seed[..]).map_err(|e| format!("seed: {:?}", e))?;
    let sk = SigningKey::<MlDsa65>::from_seed(&s);
    let expanded = sk.expanded_key();
    let sig: Signature<MlDsa65> = expanded
        .sign_deterministic(tbs, SIGNING_CONTEXT)
        .map_err(|e| format!("sign: {:?}", e))?;
    Ok(sig.encode().as_slice().to_vec())
}

pub fn verify(pk_bytes: &[u8], tbs: &[u8], sig_bytes: &[u8]) -> Result<bool, String> {
    let pk_enc = EncodedVerifyingKey::<MlDsa65>::try_from(pk_bytes).map_err(|_| {
        format!(
            "pk len: expected {}, got {}",
            MLDSA65_PUBKEY_BYTES,
            pk_bytes.len()
        )
    })?;
    let vk = VerifyingKey::<MlDsa65>::decode(&pk_enc);

    let sig_enc = EncodedSignature::<MlDsa65>::try_from(sig_bytes).map_err(|_| {
        format!(
            "sig len: expected {}, got {}",
            MLDSA65_SIGNATURE_BYTES,
            sig_bytes.len()
        )
    })?;
    let sig = Signature::<MlDsa65>::decode(&sig_enc)
        .ok_or_else(|| "signature decode failed".to_string())?;

    Ok(vk.verify_with_context(tbs, SIGNING_CONTEXT, &sig))
}
