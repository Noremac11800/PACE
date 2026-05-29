import {
  BaseDirectory,
  readTextFile,
  writeTextFile,
  mkdir,
  exists,
} from "@tauri-apps/plugin-fs";
import {
  DEFAULT_SETTINGS,
  setSettingsFromJSON,
  getSettingsJSON,
  settings,
} from "./settings.svelte";
import { theme } from "./theme";

export async function initializeApp(): Promise<void> {
  try {
    // Ensure .pace directory exists
    await mkdir(".pace", {
      baseDir: BaseDirectory.Home,
      recursive: true,
    });

    // Try to read existing settings
    const settingsExist = await exists(".pace/settings.json", {
      baseDir: BaseDirectory.Home,
    });

    if (settingsExist) {
      // Load existing settings
      const existingSettings = await readTextFile(".pace/settings.json", {
        baseDir: BaseDirectory.Home,
      });
      setSettingsFromJSON(existingSettings);
    } else {
      // Create default settings file
      const defaultJson = JSON.stringify(DEFAULT_SETTINGS, null, 2);
      await writeTextFile(".pace/settings.json", defaultJson, {
        baseDir: BaseDirectory.Home,
      });

      // Load default settings into the reactive state
      setSettingsFromJSON(defaultJson);
    }

    applyTheme(settings.general.theme);
  } catch (error) {
    console.error("Failed to initialize app settings:", error);

    // Fallback to default settings if something goes wrong
    const defaultJson = JSON.stringify(DEFAULT_SETTINGS, null, 2);
    setSettingsFromJSON(defaultJson);
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
