export interface VersionInfo {
  currentVersion: string;
  latestVersion: string;
  updateAvailable: boolean;
  changelog: string;
}

export const updateStatus: {
  cli: VersionInfo;
  app: VersionInfo;
} = $state({
  cli: {
    currentVersion: "0.1.0",
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
