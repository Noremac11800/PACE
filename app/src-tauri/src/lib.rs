// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/

/// Get the app version from git describe (e.g., "v0.1.0-5-gabc1234")
#[tauri::command]
fn get_app_version() -> String {
    // VERGEN_GIT_DESCRIBE is set at compile time by build.rs + vergen
    let version = env!("VERGEN_GIT_DESCRIBE");
    // Strip the 'v' prefix if present for cleaner display
    version.strip_prefix('v').unwrap_or(version).to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_fs::init());

    // Desktop only
    #[cfg(not(any(target_os = "android", target_os = "ios")))]
    {
        builder = builder.plugin(tauri_plugin_window_state::Builder::new().build());
    }

    builder
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![get_app_version])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
