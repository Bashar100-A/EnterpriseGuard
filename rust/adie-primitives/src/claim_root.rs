//! ADIE vOmega — ClaimRoot Merkle construction.
use crate::h_a::h_a;
use crate::jcs::canonical_bytes;
use serde_json::Value;

const FIELD_ORDER_14: [&str; 14] = [
    "issuer", "subject", "request", "context", "policy", "model", "data",
    "runtime", "output", "binding", "temporal", "evidence", "authoring",
    "proof-set",
];

const STATUS_ABSENT: u8 = 0x00;
const STATUS_PRESENT: u8 = 0x01;
const STATUS_NULL: u8 = 0x02;

fn leaf(fid: u16, status: u8, canonical: &[u8]) -> [u8; 32] {
    let mut body = Vec::with_capacity(7 + canonical.len());
    body.extend_from_slice(&fid.to_be_bytes());
    body.push(status);
    body.extend_from_slice(&(canonical.len() as u32).to_be_bytes());
    body.extend_from_slice(canonical);
    h_a("leaf", &body)
}

fn padding_leaf() -> [u8; 32] { h_a("padding", &[]) }

fn parent(l: &[u8; 32], r: &[u8; 32]) -> [u8; 32] {
    let mut body = Vec::with_capacity(64);
    body.extend_from_slice(l);
    body.extend_from_slice(r);
    h_a("node", &body)
}

pub fn compute_claim_root(fields: &Value) -> Result<[u8; 32], String> {
    let obj = fields.as_object().ok_or("fields must be object")?;
    let mut leaves: Vec<[u8; 32]> = Vec::with_capacity(16);
    for (i, name) in FIELD_ORDER_14.iter().enumerate() {
        let fid = (i + 1) as u16;
        if !obj.contains_key(*name) {
            leaves.push(leaf(fid, STATUS_ABSENT, &[]));
            continue;
        }
        let v = &obj[*name];
        if v.is_null() {
            leaves.push(leaf(fid, STATUS_NULL, &[]));
            continue;
        }
        let canonical = canonical_bytes(v)?;
        leaves.push(leaf(fid, STATUS_PRESENT, &canonical));
    }
    let mut n = 1usize;
    while n < leaves.len() { n *= 2; }
    let pad = padding_leaf();
    while leaves.len() < n { leaves.push(pad); }
    while leaves.len() > 1 {
        let mut nxt = Vec::with_capacity(leaves.len() / 2);
        for i in (0..leaves.len()).step_by(2) {
            nxt.push(parent(&leaves[i], &leaves[i + 1]));
        }
        leaves = nxt;
    }
    Ok(leaves[0])
}

pub fn claim_root_hex(fields: &Value) -> Result<String, String> {
    let r = compute_claim_root(fields)?;
    Ok(format!("sha256:{}", crate::hex::encode(&r)))
}
