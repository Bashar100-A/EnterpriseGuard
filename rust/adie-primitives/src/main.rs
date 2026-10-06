//! adie-h-a — CLI wrapper for H_A.
use std::env;
use std::process;
use adie_primitives::h_a::h_a;
use adie_primitives::hex;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("usage: adie-h-a <tag> <hex-input>");
        process::exit(2);
    }
    let tag = &args[1];
    let input = match hex::decode(&args[2]) {
        Ok(v) => v,
        Err(e) => { eprintln!("E-INPUT: {}", e); process::exit(2); }
    };
    let digest = h_a(tag, &input);
    println!("sha256:{}", hex::encode(&digest));
}
