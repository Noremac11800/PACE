export type Platform = "ios" | "android" | "windows";
export type BuildConfig = "Debug" | "Release";
export type UploadStatus = "pending" | "uploading" | "success" | "error";

export interface PackageFile {
  name: string;
  path: string;
  platform: Platform;
  buildConfig: BuildConfig;
}
