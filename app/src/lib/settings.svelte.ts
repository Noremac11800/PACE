export interface BuildTabSettings {
  fromProject: string;
  toProject: string;
  buildConfig: "Debug" | "Release";
  selectedFrameworks: string[];
  msbuildProps: Record<string, string>;
}

export const DEFAULT_BUILD_TAB_SETTINGS: BuildTabSettings = {
  fromProject: "",
  toProject: "",
  buildConfig: "Release",
  selectedFrameworks: [],
  msbuildProps: {},
};

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
  buildTab: BuildTabSettings;
  lastActiveConfig: string;
}

export const DEFAULT_SETTINGS: Settings = {
  general: {
    theme: "system",
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
  buildTab: { ...DEFAULT_BUILD_TAB_SETTINGS },
  lastActiveConfig: "",
};

export const settings: Settings = $state(DEFAULT_SETTINGS);

export function getSettingsJSON(): string {
  return JSON.stringify(settings, null, 2);
}

export function setSettingsFromJSON(json: string): void {
  try {
    const parsed = JSON.parse(json);
    Object.assign(settings, parsed);
    if (parsed.buildTab) {
      Object.assign(settings.buildTab, parsed.buildTab);
    }
  } catch (e) {
    console.error("Failed to parse settings JSON:", e);
  }
}
