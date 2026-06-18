import { Command } from "@tauri-apps/plugin-shell";

export interface PaceBuildProp {
  name: string;
  datatype: "boolean" | "string" | "path";
  default: string | boolean;
}

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
  build_props: PaceBuildProp[];
  nuget_cache_path?: string;
}

export interface ProjectGitStatus {
  cloned: boolean;
  upToDate: boolean;
  branch: string;
  aheadBehind?: string;
  behindRemote?: boolean;
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

    // Fetch latest remote refs without pulling
    const fetchCmd = Command.create("git", [
      "-C",
      projectPath,
      "fetch",
      "--quiet",
    ]);
    await fetchCmd.execute();

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

    let behindRemote = false;
    const aheadBehindMatch = statusOutput.match(/\[([^\]]+)\]/);
    if (aheadBehindMatch) {
      aheadBehind = aheadBehindMatch[1];
      upToDate = false;
      if (/behind/.test(aheadBehind)) {
        behindRemote = true;
      }
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
      behindRemote: behindRemote || undefined,
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
