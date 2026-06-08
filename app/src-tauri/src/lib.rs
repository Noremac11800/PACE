// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/

const GIT_BRANCH: &str = env!("GIT_BRANCH");
const GIT_COMMIT_COUNT: &str = env!("GIT_COMMIT_COUNT");

#[tauri::command]
fn get_app_version(app_handle: tauri::AppHandle) -> String {
    let base_version = app_handle
        .config()
        .version
        .clone()
        .map(|v| v.to_string())
        .unwrap_or_else(|| "0.1.0".to_string());

    format!("{}-{}.{}", base_version, GIT_BRANCH, GIT_COMMIT_COUNT)
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
