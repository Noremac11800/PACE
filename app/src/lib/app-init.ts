import {
  BaseDirectory,
  readTextFile,
  writeTextFile,
  mkdir,
  exists,
  copyFile,
} from "@tauri-apps/plugin-fs";
import { Command } from "@tauri-apps/plugin-shell";
import {
  DEFAULT_SETTINGS,
  setSettingsFromJSON,
  getSettingsJSON,
  settings,
} from "./settings.svelte";
import { theme } from "./theme";

export async function initializeApp(): Promise<void> {
  await ensurePaceDir();
  await loadSettings();
  applyTheme(settings.general.theme);
  await syncPaceConfig();
}

async function ensurePaceDir(): Promise<void> {
  try {
    await mkdir(".pace", {
      baseDir: BaseDirectory.Home,
      recursive: true,
    });
  } catch (error) {
    console.error("Failed to create .pace directory:", error);
  }
}

async function loadSettings(): Promise<void> {
  try {
    const settingsExist = await exists(".pace/settings.json", {
      baseDir: BaseDirectory.Home,
    });

    if (settingsExist) {
      const existingSettings = await readTextFile(".pace/settings.json", {
        baseDir: BaseDirectory.Home,
      });
      setSettingsFromJSON(existingSettings);
    } else {
      const defaultJson = JSON.stringify(DEFAULT_SETTINGS, null, 2);
      await writeTextFile(".pace/settings.json", defaultJson, {
        baseDir: BaseDirectory.Home,
      });
      setSettingsFromJSON(defaultJson);
    }
  } catch (error) {
    console.error("Failed to load settings:", error);
    setSettingsFromJSON(JSON.stringify(DEFAULT_SETTINGS, null, 2));
  }
}

export function applyTheme(themeValue: "light" | "dark" | "system"): void {
  if (themeValue === "system") {
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches;
    theme.set(prefersDark ? "dark" : "light");
  } else {
    theme.set(themeValue);
  }
}

async function syncPaceConfig(): Promise<void> {
  try {
    // Get the config file path from the pace CLI
    const result = await Command.create("pace", [
      "--print-config-path",
    ]).execute();
    if (result.code !== 0 || !result.stdout.trim()) {
      console.warn("pace --print-config-path did not return a valid path");
      return;
    }

    const configPath = result.stdout.trim();

    // Ensure .pace/configs directory exists
    await mkdir(".pace/configs", {
      baseDir: BaseDirectory.Home,
      recursive: true,
    });

    // Copy the config file into .pace/configs/default.toml, overwriting if present
    await copyFile(configPath, ".pace/configs/default.toml", {
      toPathBaseDir: BaseDirectory.Home,
    });
  } catch (error) {
    console.error("Failed to sync pace config:", error);
  }
}

export async function saveSettings(): Promise<void> {
  try {
    const settingsJson = getSettingsJSON();
    await writeTextFile(".pace/settings.json", settingsJson, {
      baseDir: BaseDirectory.Home,
    });
  } catch (error) {
    console.error("Failed to save settings:", error);
    throw error;
  }
}
