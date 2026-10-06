//! H_A domain-separated hashing (ADIE vOmega).
//! H_A(t, x) = SHA256("ADIE/vOmega/2/" || u16(|t|) || t || x)

use crate::sha256::sha256;

const DOMAIN_PREFIX: &[u8] = b"ADIE/vOmega/2/";

pub fn h_a(t: &str, x: &[u8]) -> [u8; 32] {
    let t_bytes = t.as_bytes();
    assert!(t_bytes.len() <= 0xFFFF, "domain tag too long");

    let mut buf: Vec<u8> =
        Vec::with_capacity(DOMAIN_PREFIX.len() + 2 + t_bytes.len() + x.len());
    buf.extend_from_slice(DOMAIN_PREFIX);
    buf.extend_from_slice(&(t_bytes.len() as u16).to_be_bytes());
    buf.extend_from_slice(t_bytes);
    buf.extend_from_slice(x);
    sha256(&buf)
}
