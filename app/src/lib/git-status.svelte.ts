import { checkProjectGitStatus, type PaceConfig, type PaceProject, type ProjectGitStatus } from "./pace-config";

export interface GitStatusState {
  statuses: Map<string, ProjectGitStatus>;
  loading: Set<string>;
}

export const gitStatusStore: GitStatusState = $state({
  statuses: new Map(),
  loading: new Set(),
});

export async function loadGitStatuses(config: PaceConfig): Promise<void> {
  const projectsWithRepo = config.projects.filter(p => p.repo_url);
  
  // Mark all projects as loading
  gitStatusStore.loading = new Set(projectsWithRepo.map(p => p.name));
  
  // Run all checks in parallel
  const promises = projectsWithRepo.map(async (project) => {
    try {
      const status = await checkProjectGitStatus(project, config.repodir);
      gitStatusStore.statuses = new Map(gitStatusStore.statuses).set(project.name, status);
    } catch (e) {
      console.error(`Failed to check git status for ${project.name}:`, e);
    } finally {
      const next = new Set(gitStatusStore.loading);
      next.delete(project.name);
      gitStatusStore.loading = next;
    }
  });
  
  await Promise.allSettled(promises);
}

export function getGitStatus(project: PaceProject): ProjectGitStatus | undefined {
  return gitStatusStore.statuses.get(project.name);
}

export function isLoadingGit(project: PaceProject): boolean {
  return gitStatusStore.loading.has(project.name);
}

export function clearGitStatuses(): void {
  gitStatusStore.statuses = new Map();
  gitStatusStore.loading = new Set();
}
