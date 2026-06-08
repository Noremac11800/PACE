import { paceStatus } from "./pace-status.svelte";

export interface VersionInfo {
  currentVersion: string;
  latestVersion: string;
  updateAvailable: boolean;
  changelog: string;
}

function getCliVersion(): string {
  // Extract version number from paceStatus.version (e.g., "pace 0.1.5" -> "0.1.5")
  const version = paceStatus.version;
  if (!version) return "0.1.0";
  const match = version.match(/(\d+\.\d+\.\d+)/);
  return match ? match[1] : "0.1.0";
}

export const updateStatus: {
  cli: VersionInfo;
  app: VersionInfo;
} = $state({
  cli: {
    get currentVersion() {
      return getCliVersion();
    },
    latestVersion: "0.1.0",
    updateAvailable: false,
    changelog: "",
  },
  app: {
    currentVersion: "0.1.0-alpha",
    latestVersion: "0.1.0-alpha",
    updateAvailable: false,
    changelog: "",
  },
});

export function setCliUpdate(latest: string, changelog: string) {
  updateStatus.cli.latestVersion = latest;
  updateStatus.cli.changelog = changelog;
  updateStatus.cli.updateAvailable = latest !== updateStatus.cli.currentVersion;
}

export function setAppUpdate(latest: string, changelog: string) {
  updateStatus.app.latestVersion = latest;
  updateStatus.app.changelog = changelog;
  updateStatus.app.updateAvailable = latest !== updateStatus.app.currentVersion;
}

export function hasAnyUpdate(): boolean {
  return updateStatus.cli.updateAvailable || updateStatus.app.updateAvailable;
}

/**
 * Check PyPI for the latest pace-dotnet version and update status.
 * Call this after installation or when refreshing update status.
 */
export async function checkPypiForCliUpdate(): Promise<void> {
  try {
    const response = await fetch("https://pypi.org/pypi/pace-dotnet/json");
    if (!response.ok) {
      console.warn("Failed to fetch PyPI info:", response.statusText);
      return;
    }

    const data = await response.json();
    const latestVersion = data.info?.version;

    if (latestVersion) {
      // Get changelog from release notes if available
      const releaseNotes = data.info?.project_urls?.["Release notes"] || "";
      setCliUpdate(latestVersion, releaseNotes);
      console.log(`Latest pace-dotnet version on PyPI: ${latestVersion}`);
    }
  } catch (error) {
    console.error("Failed to check PyPI for CLI updates:", error);
  }
}
