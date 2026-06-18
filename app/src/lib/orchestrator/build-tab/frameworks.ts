export const FRAMEWORKS = [
  { id: "net10.0-android", label: "Android" },
  { id: "net10.0-ios", label: "iOS" },
  { id: "net10.0-maccatalyst", label: "macOS Catalyst" },
  { id: "net10.0-windows10.0.20348.0", label: "Windows" },
] as const;

export type Framework = (typeof FRAMEWORKS)[number]["id"];
