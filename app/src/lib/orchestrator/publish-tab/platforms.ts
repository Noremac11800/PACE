import { Apple, Smartphone, Monitor } from "@lucide/svelte";

export const PLATFORMS = [
  { id: "ios" as const, label: "iOS", icon: Apple },
  { id: "android" as const, label: "Android", icon: Smartphone },
  { id: "windows" as const, label: "Windows", icon: Monitor },
];

export type Platform = (typeof PLATFORMS)[number]["id"];

export type BuildStatus = "pending" | "building" | "success" | "error";

export const platformOrder: Platform[] = ["ios", "android", "windows"];
