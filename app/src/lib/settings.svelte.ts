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

export interface PublishTabSettings {
  selectedProject: string;
  selectedPlatforms: ("ios" | "android" | "windows")[];
  buildConfig: "Debug" | "Release";
  iosBundleId: string;
  windowsKey: string;
  androidKey: string;
  noRestore: boolean;
}

export const DEFAULT_PUBLISH_TAB_SETTINGS: PublishTabSettings = {
  selectedProject: "",
  selectedPlatforms: [],
  buildConfig: "Release",
  iosBundleId: "*",
  windowsKey: "*",
  androidKey: "*",
  noRestore: false,
};

export interface UploadTabSettings {
  selectedProject: string;
  selectedPackages: string[];
  username: string;
  appName: string;
  version: string;
  buildNotes: string;
}

export const DEFAULT_UPLOAD_TAB_SETTINGS: UploadTabSettings = {
  selectedProject: "",
  selectedPackages: [],
  username: "",
  appName: "",
  version: "",
  buildNotes: "",
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
  publishTab: PublishTabSettings;
  uploadTab: UploadTabSettings;
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
  publishTab: { ...DEFAULT_PUBLISH_TAB_SETTINGS },
  uploadTab: { ...DEFAULT_UPLOAD_TAB_SETTINGS },
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
    if (parsed.publishTab) {
      Object.assign(settings.publishTab, parsed.publishTab);
    }
    if (parsed.uploadTab) {
      Object.assign(settings.uploadTab, parsed.uploadTab);
    }
  } catch (e) {
    console.error("Failed to parse settings JSON:", e);
  }
}
