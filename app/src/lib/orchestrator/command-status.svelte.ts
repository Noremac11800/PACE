// Shared state for tracking running commands across orchestrator tabs
export const commandStatus: {
  isBuilding: boolean;
  isPublishing: boolean;
  isUploading: boolean;
} = $state({
  isBuilding: false,
  isPublishing: false,
  isUploading: false,
});

export function setBuildingStatus(status: boolean): void {
  commandStatus.isBuilding = status;
}

export function setPublishingStatus(status: boolean): void {
  commandStatus.isPublishing = status;
}

export function setUploadingStatus(status: boolean): void {
  commandStatus.isUploading = status;
}

export function isAnyCommandRunning(): boolean {
  return commandStatus.isBuilding || commandStatus.isPublishing || commandStatus.isUploading;
}
