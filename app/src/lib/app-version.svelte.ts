import { invoke } from "@tauri-apps/api/core";

export const appVersion: {
  version: string;
  fetched: boolean;
} = $state({
  version: "0.1.0",
  fetched: false,
});

export async function fetchAppVersion(): Promise<string> {
  if (appVersion.fetched) {
    return appVersion.version;
  }
  try {
    const version = await invoke<string>("get_app_version");
    appVersion.version = version;
    appVersion.fetched = true;
    return version;
  } catch (error) {
    console.error("Failed to fetch app version:", error);
    return appVersion.version;
  }
}

export function getAppVersion(): string {
  if (!appVersion.fetched) {
    fetchAppVersion();
  }
  return appVersion.version;
}
