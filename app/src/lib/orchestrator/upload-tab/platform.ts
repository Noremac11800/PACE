import type { Component } from "svelte";
import { Apple, Smartphone, Monitor } from "@lucide/svelte";
import type { Platform } from "./types";

export function getPlatformIcon(platform: Platform): Component {
  switch (platform) {
    case "ios":
      return Apple;
    case "android":
      return Smartphone;
    case "windows":
      return Monitor;
  }
}

export function getApiPlatform(platform: Platform): string {
  switch (platform) {
    case "ios":
      return "iOS";
    case "android":
      return "Android";
    case "windows":
      return "Windows";
  }
}
