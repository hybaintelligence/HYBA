// Salamander Blastema Seed: ultra-portable manifest bootstrap stub.
// It intentionally has no third-party dependencies so it can compile in a bare
// Rust runtime and hand a canonical manifest to a runtime-specific rehydrator.

use std::env;
use std::fs;
use std::process;

fn main() {
    let path = env::args().nth(1).unwrap_or_else(|| {
        eprintln!("usage: salamander_blastema_seed <manifest.json>");
        process::exit(2);
    });
    let manifest = fs::read_to_string(&path).unwrap_or_else(|err| {
        eprintln!("failed to read manifest {}: {}", path, err);
        process::exit(3);
    });
    if !manifest.contains("salamander.frontier.replay.v1") || !manifest.contains("replay_digest") {
        eprintln!("manifest is not a Salamander replay v1 manifest");
        process::exit(4);
    }
    println!("SALAMANDER_BLASTEMA_READY:{}:{}", path, manifest.len());
}
