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
  
  for (const project of projectsWithRepo) {
    gitStatusStore.loading = new Set(gitStatusStore.loading).add(project.name);
    
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
  }
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
