mod runtime;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            runtime::environment,
            runtime::bridge,
            runtime::run_pace,
        ])
        .run(tauri::generate_context!())
        .expect("error while running PACE");
}
