<script lang="ts">
  import { onMount } from "svelte";
  import {
    Cog,
    Folder,
    FileCode,
    GitBranch,
    Package,
    Layers,
    Check,
    X,
    Loader,
    ChevronRight,
    ChevronDown,
  } from "@lucide/svelte";
  import {
    loadPaceConfig,
    checkProjectGitStatus,
    type PaceConfig,
    type PaceProject,
    type ProjectGitStatus,
  } from "$lib/pace-config";

  let config = $state<PaceConfig | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let gitStatuses = $state<Map<string, ProjectGitStatus>>(new Map());
  let loadingGit = $state<Set<string>>(new Set());
  let expandedGroups = $state<Set<string>>(new Set());

  const GROUP_ORDER = ["Toolkits", "AppModules", "Apps"];

  onMount(async () => {
    try {
      const loadedConfig = await loadPaceConfig();
      if (loadedConfig) {
        config = loadedConfig;
        // Load git status for all projects
        await loadAllGitStatuses(loadedConfig);
      } else {
        error = "Failed to load PACE configuration";
      }
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading = false;
    }
  });

  async function loadAllGitStatuses(config: PaceConfig) {
    for (const project of config.projects) {
      if (project.repo_url) {
        loadingGit.add(project.name);
        try {
          const status = await checkProjectGitStatus(project, config.repodir);
          gitStatuses.set(project.name, status);
        } catch (e) {
          console.error(`Failed to check git status for ${project.name}:`, e);
        } finally {
          loadingGit.delete(project.name);
        }
      }
    }
    // Trigger reactivity
    gitStatuses = gitStatuses;
    loadingGit = loadingGit;
  }

  function getOrderedGroups(): string[] {
    if (!config) return [];
    const availableGroups = new Set(
      config.projects.map((p) => p.sln_group).filter(Boolean),
    );
    // Return groups in fixed order, only including those that exist
    return GROUP_ORDER.filter((g) => availableGroups.has(g));
  }

  function getProjectsByGroup(group: string): PaceProject[] {
    if (!config) return [];
    return config.projects.filter((p) => p.sln_group === group);
  }

  function getGitStatus(project: PaceProject): ProjectGitStatus | undefined {
    return gitStatuses.get(project.name);
  }

  function isLoadingGit(project: PaceProject): boolean {
    return loadingGit.has(project.name);
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
</script>

<div class="h-full flex flex-col overflow-auto">
  <!-- Header -->
  <div
    class="flex items-center gap-2 p-4 bg-surface-50-950 border-b border-surface-200-800"
  >
    <Cog size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Orchestrator</h2>
  </div>

  <div class="flex flex-col p-4 gap-4">
    {#if loading}
      <div class="flex-1 flex items-center justify-center min-h-[200px]">
        <div class="text-center">
          <Cog size={48} class="mx-auto mb-4 text-primary-500 animate-spin" />
          <p class="text-surface-700-300">Loading PACE configuration...</p>
        </div>
      </div>
    {:else if error}
      <div class="flex-1 flex items-center justify-center min-h-[200px]">
        <div
          class="card bg-error-500/10 border border-error-500 p-6 text-center max-w-md"
        >
          <p class="text-error-500 font-semibold mb-2">Error</p>
          <p class="text-surface-700-300">{error}</p>
        </div>
      </div>
    {:else if config}
      <!-- Repository Directory -->
      <div class="card bg-surface-50-950 p-4">
        <div class="flex items-center gap-2 mb-2">
          <Folder size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100"
            >Repository Directory</span
          >
        </div>
        <code class="text-sm bg-surface-200-800 px-3 py-2 rounded block"
          >{config.repodir}</code
        >
      </div>

      <!-- Projects Overview -->
      <div class="card bg-surface-50-950 p-4">
        <div class="flex items-center gap-2 mb-4">
          <Package size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100"
            >Projects Overview</span
          >
          <span class="text-sm text-surface-500-400"
            >({config.projects.length} total)</span
          >
        </div>

        <div class="grid grid-cols-3 gap-3">
          {#each getOrderedGroups() as group}
            {@const count = getProjectsByGroup(group).length}
            <div class="bg-surface-100-900/50 p-3 rounded text-center">
              <Layers size={20} class="mx-auto mb-1 text-primary-500" />
              <div class="text-lg font-bold text-surface-900-100">{count}</div>
              <div class="text-xs text-surface-500-400">{group}</div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Projects Table -->
      <div
        class="card bg-surface-50-950 p-4 flex-1 min-h-0 overflow-hidden flex flex-col"
      >
        <div class="flex items-center gap-2 mb-4">
          <FileCode size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100">Projects</span>
        </div>

        <div class="overflow-auto flex-1 space-y-6">
          {#each getOrderedGroups() as group}
            <div>
              <button
                class="w-full flex items-center gap-2 text-sm font-semibold text-surface-500-400 mb-3 uppercase tracking-wide sticky top-0 bg-surface-50-950 py-2 text-left hover:text-primary-500 transition-colors"
                onclick={() => toggleGroup(group)}
              >
                {#if isGroupExpanded(group)}
                  <ChevronDown size={16} class="text-primary-500" />
                {:else}
                  <ChevronRight size={16} />
                {/if}
                {group}
                <span class="text-xs text-surface-400-600 font-normal">
                  ({getProjectsByGroup(group).length} projects)
                </span>
              </button>
              {#if isGroupExpanded(group)}
                <div>
                  <table class="w-full text-sm table-fixed">
                    <thead>
                      <tr class="border-b border-surface-200-800">
                        <th
                          class="text-left py-2 px-3 font-semibold text-surface-700-300"
                          >Project</th
                        >
                        <th
                          class="text-center py-2 px-3 font-semibold text-surface-700-300 w-24"
                          >Cloned</th
                        >
                        <th
                          class="text-center py-2 px-3 font-semibold text-surface-700-300 w-32"
                          >Up to Date</th
                        >
                        <th
                          class="text-left py-2 px-3 font-semibold text-surface-700-300 w-40"
                          >Branch</th
                        >
                      </tr>
                    </thead>
                    <tbody>
                      {#each getProjectsByGroup(group) as project}
                        {@const gitStatus = getGitStatus(project)}
                        <tr
                          class="border-b border-surface-100-900/50 hover:bg-surface-100-900/30"
                        >
                          <td class="py-2 px-3">
                            <div
                              class="font-medium text-surface-900-100 break-words"
                            >
                              {project.name}
                            </div>
                            <div
                              class="text-xs text-surface-500-400 break-words"
                            >
                              {project.csproj_path}
                            </div>
                          </td>
                          <td class="py-2 px-3 text-center">
                            {#if isLoadingGit(project)}
                              <Loader
                                size={16}
                                class="animate-spin mx-auto text-primary-500"
                              />
                            {:else if gitStatus}
                              {#if gitStatus.cloned}
                                <Check
                                  size={18}
                                  class="mx-auto text-success-500"
                                />
                              {:else}
                                <X size={18} class="mx-auto text-error-500" />
                              {/if}
                            {:else}
                              <span class="text-surface-500-400">-</span>
                            {/if}
                          </td>
                          <td class="py-2 px-3 text-center">
                            {#if isLoadingGit(project)}
                              <span class="text-surface-500-400">...</span>
                            {:else if gitStatus?.cloned}
                              {#if gitStatus.upToDate}
                                <span
                                  class="inline-flex items-center gap-1 text-success-500"
                                >
                                  <Check size={14} />
                                  <span class="text-xs">Yes</span>
                                </span>
                              {:else}
                                <span
                                  class="inline-flex items-center gap-1 text-warning-500"
                                  title={gitStatus.aheadBehind}
                                >
                                  <X size={14} />
                                  <span class="text-xs break-all"
                                    >{gitStatus.aheadBehind || "No"}</span
                                  >
                                </span>
                              {/if}
                            {:else}
                              <span class="text-surface-500-400">-</span>
                            {/if}
                          </td>
                          <td class="py-2 px-3">
                            {#if isLoadingGit(project)}
                              <span class="text-surface-500-400">...</span>
                            {:else if gitStatus?.cloned}
                              <span
                                class="inline-flex items-center gap-1 min-w-0"
                              >
                                <GitBranch
                                  size={14}
                                  class="text-primary-500 shrink-0"
                                />
                                <span class="text-surface-700-300 break-all"
                                  >{gitStatus.branch}</span
                                >
                              </span>
                            {:else}
                              <span class="text-surface-500-400">-</span>
                            {/if}
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</div>
