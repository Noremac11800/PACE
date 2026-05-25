import { Command } from "@tauri-apps/plugin-shell";

export async function isPythonInstalled(min_version: string): Promise<boolean> {
  let result = await Command.create("python", ["--version"]).execute();
  if (result.code != 0) {
    return false;
  } else {
    const version = result.stdout.trim().split(" ")[1];
    const versionParts = version.split(".").map(Number);
    const minParts = min_version.split(".").map(Number);

    for (let i = 0; i < minParts.length; i++) {
      if ((versionParts[i] || 0) < minParts[i]) return false;
      if ((versionParts[i] || 0) > minParts[i]) return true;
    }
    return true;
  }
}

export async function getPythonVersion(): Promise<string> {
  if (await isPythonInstalled("3.0.0")) {
    let result = await Command.create("python", ["--version"]).execute();
    if (result.code != 0) {
      return `Error getting Python version: ${result.stderr}`;
    }

    return result.stdout;
  } else {
    return "Error getting Python version: Unknown error";
  }
}

export async function isGitInstalled(): Promise<boolean> {
  try {
    let result = await Command.create("git", ["--version"]).execute();
    return result.code == 0;
  } catch {
    return false;
  }
}

export async function isPipxInstalled(): Promise<boolean> {
  try {
    let result = await Command.create("pipx", ["--version"]).execute();
    return result.code == 0;
  } catch {
    return false;
  }
}

export async function installPipx(): Promise<string> {
  try {
    // First check if pipx is installed, if not install it
    if (!(await isPipxInstalled())) {
      const pipxInstallResult = await Command.create("python", [
        "-m",
        "pip",
        "install",
        "pipx",
      ]).execute();
      if (pipxInstallResult.code !== 0) {
        return `Failed to install pipx: ${pipxInstallResult.stderr}`;
      }
    }
  } catch (error) {
    return `Error installing pipx: ${error instanceof Error ? error.message : String(error)}`;
  }
  return "Unable to install pipx: Reason unknown";
}

export async function installPace(repodir: string): Promise<string> {
  try {
    // Install pace using pipx from the specified repository directory
    console.log(repodir);
    const installResult = await Command.create("pipx", [
      "install",
      "--editable",
      repodir,
    ]).execute();

    if (installResult.code !== 0) {
      console.log(installResult);
      return `Failed to install pace: ${installResult.stderr}`;
    }

    return "PACE installed successfully";
  } catch (error) {
    return `Error installing PACE: ${error instanceof Error ? error.message : String(error)}`;
  }
}
