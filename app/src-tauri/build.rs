use std::process::Command;

fn main() {
    // Rerun build script when git state changes
    println!("cargo:rerun-if-changed=.git/HEAD");
    println!("cargo:rerun-if-changed=.git/refs/heads/");

    // Get git branch
    let branch = Command::new("git")
        .args(["rev-parse", "--abbrev-ref", "HEAD"])
        .output()
        .ok()
        .and_then(|output| {
            if output.status.success() {
                String::from_utf8(output.stdout).ok()
            } else {
                None
            }
        })
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|| "unknown".to_string());

    // Get commit count ahead of base branch (main or master)
    let base_branch = Command::new("git")
        .args(["rev-parse", "--abbrev-ref", "origin/HEAD"])
        .output()
        .ok()
        .and_then(|output| {
            if output.status.success() {
                String::from_utf8(output.stdout).ok()
            } else {
                None
            }
        })
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|| "origin/main".to_string());

    let commit_count = Command::new("git")
        .args(["rev-list", "--count", &format!("{}..HEAD", base_branch)])
        .output()
        .ok()
        .and_then(|output| {
            if output.status.success() {
                String::from_utf8(output.stdout).ok()
            } else {
                None
            }
        })
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|| "0".to_string());

    println!("cargo:rustc-env=GIT_BRANCH={}", branch);
    println!("cargo:rustc-env=GIT_COMMIT_COUNT={}", commit_count);

    tauri_build::build()
}
