import { Command } from "@tauri-apps/plugin-shell";

export const paceStatus: {
  installed: boolean | undefined;
  version: string;
} = $state({
  installed: undefined,
  version: "",
});

export function setPaceInstalledStatus(value: boolean) {
  paceStatus.installed = value;
}

export function setPaceVersion(value: string) {
  paceStatus.version = value;
}

export async function checkPaceInstalled(): Promise<boolean> {
  try {
    const result = await Command.create("pace", ["--version"]).execute();
    paceStatus.installed = result.code === 0;
    if (paceStatus.installed) {
      paceStatus.version = result.stdout.trim();
    } else {
      paceStatus.version = "";
    }
  } catch {
    paceStatus.installed = false;
    paceStatus.version = "";
  }
  return paceStatus.installed;
}
