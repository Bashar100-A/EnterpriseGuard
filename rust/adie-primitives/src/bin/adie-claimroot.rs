//! adie-claimroot — reads JSON object from stdin, prints sha256:<hex>.
use std::io::Read;
use serde_json::Value;
use adie_primitives::claim_root::claim_root_hex;

fn main() {
    let mut buf = String::new();
    if let Err(e) = std::io::stdin().read_to_string(&mut buf) {
        eprintln!("E-INPUT: {}", e);
        std::process::exit(2);
    }
    let v: Value = match serde_json::from_str(&buf) {
        Ok(x) => x,
        Err(e) => { eprintln!("E-JSON: {}", e); std::process::exit(2); }
    };
    match claim_root_hex(&v) {
        Ok(hex) => println!("{}", hex),
        Err(e) => { eprintln!("E-CR: {}", e); std::process::exit(1); }
    }
}
