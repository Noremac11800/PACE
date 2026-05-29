export interface Settings {
  general: {
    theme: "light" | "dark" | "system";
    language: string;
    autoCheckUpdates: boolean;
  };
  cliPaths: {
    paceCliPath: string;
    gitPath: string;
    dotnetPath: string;
  };
  projectDefaults: {
    defaultSolutionDirectory: string;
    defaultBranch: string;
  };
  appearance: {
    fontSize: "small" | "medium" | "large";
    compactMode: boolean;
  };
}

export const DEFAULT_SETTINGS: Settings = {
  general: {
    theme: "light",
    language: "en",
    autoCheckUpdates: true,
  },
  cliPaths: {
    paceCliPath: "",
    gitPath: "",
    dotnetPath: "",
  },
  projectDefaults: {
    defaultSolutionDirectory: "",
    defaultBranch: "main",
  },
  appearance: {
    fontSize: "medium",
    compactMode: false,
  },
};

export const settings: Settings = $state(DEFAULT_SETTINGS);

export function getSettingsJSON(): string {
  return JSON.stringify(settings, null, 2);
}

export function setSettingsFromJSON(json: string): void {
  try {
    const parsed = JSON.parse(json);
    Object.assign(settings, parsed);
  } catch (e) {
    console.error("Failed to parse settings JSON:", e);
  }
}
