import { Command } from "@tauri-apps/plugin-shell";

export async function isPythonInstalled(min_version: string): Promise<boolean> {
  try {
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
  } catch (error) {
    console.error("Error checking Python version:", error);
    return false;
  }
}

export async function getPythonVersion(): Promise<string> {
  if (await isPythonInstalled("3.0.0")) {
    try {
      let result = await Command.create("python", ["--version"]).execute();
      if (result.code != 0) {
        return `Error getting Python version: ${result.stderr}`;
      }

      return result.stdout;
    } catch (error) {
      return `Error getting Python version: ${error instanceof Error ? error.message : String(error)}`;
    }
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
    // Install pipx using pip with --user and --break-system-packages if needed
    const installResult = await Command.create("python", [
      "-m",
      "pip",
      "install",
      "--user",
      "pipx",
    ]).execute();

    if (installResult.code !== 0) {
      // Try with --break-system-packages flag (for PEP 668 systems)
      const retryResult = await Command.create("python", [
        "-m",
        "pip",
        "install",
        "--user",
        "--break-system-packages",
        "pipx",
      ]).execute();
      if (retryResult.code !== 0) {
        return `Failed to install pipx: ${retryResult.stderr}`;
      }
    }

    // Ensure pipx is on PATH
    await Command.create("python", ["-m", "pipx", "ensurepath"]).execute();

    return "Pipx installed successfully";
  } catch (error) {
    return `Error installing pipx: ${error instanceof Error ? error.message : String(error)}`;
  }
}

export async function installPace(): Promise<string> {
  try {
    // First try to upgrade if already installed
    const upgradeResult = await Command.create("pipx", [
      "upgrade",
      "pace-dotnet",
    ]).execute();

    if (upgradeResult.code === 0) {
      // Ensure PATH is set up
      await Command.create("pipx", ["ensurepath"]).execute();
      return "PACE upgraded successfully";
    }

    // If upgrade failed (not installed), try fresh install with force
    const installResult = await Command.create("pipx", [
      "install",
      "--force",
      "pace-dotnet",
    ]).execute();

    if (installResult.code !== 0) {
      console.log(installResult);
      return `Failed to install pace: ${installResult.stderr}`;
    }

    // Ensure PATH is set up
    await Command.create("pipx", ["ensurepath"]).execute();

    return "PACE installed successfully. You may need to restart your terminal for 'pace' to be available on PATH.";
  } catch (error) {
    return `Error installing PACE: ${error instanceof Error ? error.message : String(error)}`;
  }
}
