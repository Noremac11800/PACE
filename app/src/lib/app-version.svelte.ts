import { invoke } from "@tauri-apps/api/core";

// App version fetched from Rust backend (populated by vergen at compile time)
// Not exported directly - use getAppVersion() getter instead
let appVersion = $state<string>("");

// Getter for the current app version value
export function getAppVersion(): string {
  return appVersion;
}

// Fetch the version from the Rust backend
export async function fetchAppVersion(): Promise<string> {
  try {
    const version = await invoke<string>("get_app_version");
    appVersion = version;
    return version;
  } catch (error) {
    console.error("Failed to fetch app version:", error);
    appVersion = "unknown";
    return "unknown";
  }
}

// Initialize version on app start
fetchAppVersion();

// Helper to format version with 'v' prefix
export function getFormattedVersion(): string {
  return appVersion ? `v${appVersion}` : "v...";
}
