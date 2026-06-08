use vergen::EmitBuilder;

fn main() {
    // Emit git version info at compile time
    EmitBuilder::builder()
        .build_date()
        .git_sha(true)
        .git_describe(true, true, None)
        .emit()
        .unwrap();

    tauri_build::build()
}
