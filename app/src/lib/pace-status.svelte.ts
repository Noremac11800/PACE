import { Command } from "@tauri-apps/plugin-shell";

export const paceStatus: { installed: boolean | undefined } = $state({
  installed: undefined,
});

export function setPaceInstalledStatus(value: boolean) {
  paceStatus.installed = value;
}

export async function checkPaceInstalled(): Promise<boolean> {
  try {
    const result = await Command.create("pace", ["--version"]).execute();
    paceStatus.installed = result.code === 0;
  } catch {
    paceStatus.installed = false;
  }
  return paceStatus.installed;
}
