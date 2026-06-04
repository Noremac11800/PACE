<script lang="ts">
  import {
    GitBranch,
    RefreshCw,
    FolderOpen,
    ChevronDown,
    ChevronRight,
  } from "@lucide/svelte";
  import { revealItemInDir } from "@tauri-apps/plugin-opener";
  import { untrack } from "svelte";
  import { configStore } from "$lib/config-store.svelte";
  import {
    loadGitStatuses,
    gitStatusStore,
    getGitStatus,
    isLoadingGit,
  } from "$lib/git-status.svelte";
  import ProjectGitStatusRow from "$lib/orchestrator/ProjectGitStatusRow.svelte";
  import type { PaceProject } from "$lib/pace-config";

  let refreshing = $state(false);
  let expandedGroups = $state<Set<string>>(new Set());
  let hasLoaded = $state(false);

  const GROUP_ORDER = ["Toolkits", "AppModules", "Apps"];

  $effect(() => {
    if (configStore.activeConfig) {
      // Prevent infinite loops by using untrack
      const config = untrack(() => configStore.activeConfig);
      const loaded = untrack(() => hasLoaded);

      if (!loaded && config) {
        hasLoaded = true;
        loadGitStatuses(config);
        // Expand all groups by default in Git tab
        const allGroups = getOrderedGroups();
        expandedGroups = new Set(allGroups);
      }
    }
  });

  function getOrderedGroups(): string[] {
    if (!configStore.activeConfig) return [];
    const availableGroups = new Set(
      configStore.activeConfig.projects
        .map((p) => p.sln_group)
        .filter(Boolean) as string[],
    );
    const ordered = GROUP_ORDER.filter((g) => availableGroups.has(g));
    for (const g of availableGroups) {
      if (!GROUP_ORDER.includes(g)) ordered.push(g);
    }
    return ordered;
  }

  function getProjectsByGroup(group: string): PaceProject[] {
    if (!configStore.activeConfig) return [];
    return configStore.activeConfig.projects.filter(
      (p) => p.sln_group === group && p.repo_url,
    );
  }

  function toggleGroup(group: string) {
    const newSet = new Set(expandedGroups);
    if (newSet.has(group)) {
      newSet.delete(group);
    } else {
      newSet.add(group);
    }
    expandedGroups = newSet;
  }

  function isGroupExpanded(group: string): boolean {
    return expandedGroups.has(group);
  }

  async function refreshAll() {
    if (!configStore.activeConfig || refreshing) return;
    refreshing = true;
    await loadGitStatuses(configStore.activeConfig);
    refreshing = false;
  }

  async function openRepoFolder(project: PaceProject) {
    if (!configStore.activeConfig) return;
    const path = `${configStore.activeConfig.repodir}/${project.name}`;
    await revealItemInDir(path);
  }

  function getAllProjectsWithRepo(): PaceProject[] {
    if (!configStore.activeConfig) return [];
    return configStore.activeConfig.projects.filter((p) => p.repo_url);
  }

  function getProjectStatusSummary() {
    const projects = getAllProjectsWithRepo();
    const cloned = projects.filter((p) => getGitStatus(p)?.cloned).length;
    const upToDate = projects.filter((p) => {
      const status = getGitStatus(p);
      return status?.cloned && status?.upToDate;
    }).length;
    const loading = projects.filter((p) => isLoadingGit(p)).length;
    return { total: projects.length, cloned, upToDate, loading };
  }
</script>

<div class="h-full flex flex-col overflow-hidden">
  <!-- Header with actions -->
  <div
    class="flex items-center justify-between gap-4 p-4 border-b border-surface-200-800 bg-surface-50-950 shrink-0"
  >
    <div class="flex items-center gap-3">
      <GitBranch size={20} class="text-primary-500" />
      <h3 class="font-semibold text-surface-900-100">Git Status</h3>
      {#if configStore.activeConfig}
        {@const summary = getProjectStatusSummary()}
        <div class="flex items-center gap-2 text-xs">
          <span
            class="px-2 py-0.5 rounded bg-surface-200-800 text-surface-700-300"
          >
            {summary.total} repos
          </span>
          {#if summary.loading > 0}
            <span
              class="px-2 py-0.5 rounded bg-primary-500/10 text-primary-500"
            >
              {summary.loading} checking...
            </span>
          {:else}
            <span
              class="px-2 py-0.5 rounded bg-success-500/10 text-success-500"
            >
              {summary.cloned} cloned
            </span>
            <span
              class="px-2 py-0.5 rounded {summary.upToDate === summary.cloned
                ? 'bg-success-500/10 text-success-500'
                : 'bg-warning-500/10 text-warning-500'}"
            >
              {summary.upToDate} up to date
            </span>
          {/if}
        </div>
      {/if}
    </div>
    <button
      class="btn preset-tonal p-2 hover:preset-filled-primary-500 transition-colors"
      onclick={refreshAll}
      disabled={refreshing || !configStore.activeConfig}
      title="Refresh all git statuses"
    >
      <RefreshCw size={16} class={refreshing ? "animate-spin" : ""} />
    </button>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-auto p-4">
    {#if !configStore.activeConfig}
      <div class="flex items-center justify-center h-full text-surface-500-400">
        No config loaded
      </div>
    {:else if getAllProjectsWithRepo().length === 0}
      <div class="flex items-center justify-center h-full text-surface-500-400">
        No projects with repositories configured
      </div>
    {:else}
      <div class="flex flex-col gap-3">
        {#each getOrderedGroups() as group}
          {@const groupProjects = getProjectsByGroup(group)}
          {#if groupProjects.length > 0}
            {@const clonedCount = groupProjects.filter(
              (p) => getGitStatus(p)?.cloned,
            ).length}
            {@const upToDateCount = groupProjects.filter((p) => {
              const status = getGitStatus(p);
              return status?.cloned && status?.upToDate;
            }).length}
            <div class="card bg-surface-50-950 overflow-hidden">
              <!-- Group header -->
              <button
                class="w-full flex items-center justify-between p-3 text-left hover:bg-surface-100-900/30 transition-colors"
                onclick={() => toggleGroup(group)}
              >
                <div class="flex items-center gap-2">
                  {#if isGroupExpanded(group)}
                    <ChevronDown size={16} class="text-primary-500" />
                  {:else}
                    <ChevronRight size={16} class="text-surface-500-400" />
                  {/if}
                  <span class="font-semibold text-surface-900-100">{group}</span
                  >
                  <span class="text-xs text-surface-500-400"
                    >({groupProjects.length})</span
                  >
                </div>
                <span
                  class="text-xs {upToDateCount === clonedCount &&
                  clonedCount > 0
                    ? 'text-success-500'
                    : 'text-warning-500'}"
                >
                  {upToDateCount}/{clonedCount} up to date
                </span>
              </button>

              {#if isGroupExpanded(group)}
                <div class="border-t border-surface-200-800">
                  {#each groupProjects as project}
                    <div class="flex items-center">
                      <div class="flex-1 min-w-0">
                        <ProjectGitStatusRow
                          {project}
                          gitStatus={getGitStatus(project)}
                          loading={isLoadingGit(project)}
                          compact={true}
                        />
                      </div>
                      <button
                        class="btn preset-tonal p-2 mx-2 hover:preset-filled-primary-500 transition-colors shrink-0"
                        onclick={() => openRepoFolder(project)}
                        title="Open repository folder"
                      >
                        <FolderOpen size={14} />
                      </button>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    {/if}
  </div>
</div>
