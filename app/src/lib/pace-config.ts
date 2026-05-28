import { Command } from "@tauri-apps/plugin-shell";
import { readTextFile } from "@tauri-apps/plugin-fs";
import * as TOML from "js-toml";

export interface PaceProject {
  name: string;
  csproj_path: string;
  repo_url?: string;
  sln_group?: string;
  explicit_frameworks: string[];
  depends_on: string[];
}

export interface PaceConfig {
  repodir: string;
  projects: PaceProject[];
}

export async function getPaceConfigPath(): Promise<string | null> {
  try {
    const cmd = Command.create("pace", ["--print-config-path"]);
    const result = await cmd.execute();

    if (result.code === 0 && result.stdout) {
      return result.stdout.trim();
    }
    return null;
  } catch (error) {
    console.error("Failed to get pace config path:", error);
    return null;
  }
}

export function parseToml(tomlContent: string): PaceConfig {
  return TOML.load(tomlContent) as unknown as PaceConfig;
}

export async function loadPaceConfig(): Promise<PaceConfig | null> {
  const configPath = await getPaceConfigPath();
  if (!configPath) {
    return null;
  }

  try {
    const content = await readTextFile(configPath);
    return parseToml(content);
  } catch (error) {
    console.error("Failed to load pace config:", error);
    return null;
  }
}

export interface ProjectGitStatus {
  cloned: boolean;
  upToDate: boolean;
  branch: string;
  aheadBehind?: string;
}

export async function checkProjectGitStatus(
  project: PaceProject,
  repodir: string,
): Promise<ProjectGitStatus> {
  const projectPath = `${repodir}/${project.name}`;

  try {
    // Check if directory exists
    const checkCmd = Command.create("ls", ["-d", projectPath]);
    const checkResult = await checkCmd.execute();

    if (checkResult.code !== 0) {
      return {
        cloned: false,
        upToDate: false,
        branch: "N/A",
      };
    }

    // Check if it's a git repo
    const gitCheckCmd = Command.create("ls", ["-d", `${projectPath}/.git`]);
    const gitCheckResult = await gitCheckCmd.execute();

    if (gitCheckResult.code !== 0) {
      return {
        cloned: true,
        upToDate: false,
        branch: "Not a git repo",
      };
    }

    // Get current branch
    const branchCmd = Command.create("git", [
      "-C",
      projectPath,
      "branch",
      "--show-current",
    ]);
    const branchResult = await branchCmd.execute();
    const branch =
      branchResult.code === 0 ? branchResult.stdout.trim() : "unknown";

    // Check status (ahead/behind)
    const statusCmd = Command.create("git", [
      "-C",
      projectPath,
      "status",
      "-sb",
    ]);
    const statusResult = await statusCmd.execute();
    const statusOutput = statusResult.stdout || "";

    // Parse ahead/behind from status
    let aheadBehind = "";
    let upToDate = true;

    const aheadBehindMatch = statusOutput.match(/\[([^\]]+)\]/);
    if (aheadBehindMatch) {
      aheadBehind = aheadBehindMatch[1];
      upToDate = false;
    }

    // Check for uncommitted changes
    const hasChanges = statusOutput
      .split("\n")
      .some((line) => line.match(/^\s*[MADRC?]/));

    if (hasChanges) {
      upToDate = false;
      aheadBehind = aheadBehind ? `${aheadBehind}, uncommitted` : "uncommitted";
    }

    return {
      cloned: true,
      upToDate,
      branch,
      aheadBehind: aheadBehind || undefined,
    };
  } catch (error) {
    console.error(`Failed to check git status for ${project.name}:`, error);
    return {
      cloned: false,
      upToDate: false,
      branch: "Error",
    };
  }
}
