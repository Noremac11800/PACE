<script lang="ts">
  import {
    Folder,
    Package,
    Layers,
    ChevronRight,
    ChevronDown,
    FolderOpen,
  } from "@lucide/svelte";
  import { revealItemInDir } from "@tauri-apps/plugin-opener";
  import type { PaceConfig, PaceProject } from "$lib/pace-config";

  interface Props {
    config: PaceConfig;
  }

  let { config }: Props = $props();

  let expandedGroups = $state<Set<string>>(new Set());

  function getOrderedGroups(): string[] {
    if (!config) return [];
    const groups = config.projects
      .map((p) => p.sln_group)
      .filter(Boolean) as string[];
    return [...new Set(groups)];
  }

  function getProjectsByGroup(group: string): PaceProject[] {
    if (!config) return [];
    return config.projects.filter((p) => p.sln_group === group);
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

  async function openFolder(path: string) {
    if (path) {
      await revealItemInDir(path);
    }
  }

  function getProjectPath(project: PaceProject): string {
    return `${config.repodir}/${project.name}`;
  }
</script>

<div class="flex flex-col gap-4">
  <!-- Repository Directory -->
  <div class="card bg-surface-50-950 p-4">
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-2">
        <Folder size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100"
          >Repository Directory</span
        >
      </div>
      <button
        class="btn preset-tonal p-1.5 hover:preset-filled-primary-500 transition-colors"
        onclick={() => openFolder(config.repodir)}
        disabled={!config.repodir}
        title="Open repository folder"
      >
        <FolderOpen size={14} />
      </button>
    </div>
    <code class="text-sm bg-surface-200-800 px-3 py-2 rounded block"
      >{config.repodir}</code
    >
  </div>

  <!-- NuGet Cache Path -->
  {#if config.nuget_cache_path}
    <div class="card bg-surface-50-950 p-4">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <Package size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100"
            >NuGet Cache Path</span
          >
        </div>
        <button
          class="btn preset-tonal p-1.5 hover:preset-filled-primary-500 transition-colors"
          onclick={() => openFolder(config.nuget_cache_path!)}
          title="Open NuGet cache folder"
        >
          <FolderOpen size={14} />
        </button>
      </div>
      <code class="text-sm bg-surface-200-800 px-3 py-2 rounded block"
        >{config.nuget_cache_path}</code
      >
    </div>
  {/if}

  <!-- Projects Overview -->
  <div class="card bg-surface-50-950 p-4">
    <div class="flex items-center gap-2 mb-4">
      <Package size={18} class="text-primary-500" />
      <span class="font-semibold text-surface-900-100">Projects Overview</span>
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

  <!-- Projects -->
  <div
    class="card bg-surface-50-950 p-4 flex-1 min-h-0 overflow-hidden flex flex-col"
  >
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <Layers size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100">Projects</span>
        <span class="text-xs text-surface-500-400"
          >({config.projects.length})</span
        >
      </div>
    </div>

    <div class="overflow-auto flex-1 space-y-2">
      {#each getOrderedGroups() as group}
        <div class="border border-surface-200-800 rounded-lg overflow-hidden">
          <button
            class="w-full flex items-center justify-between p-2.5 text-left bg-surface-100-900/30 hover:bg-surface-100-900/50 transition-colors"
            onclick={() => toggleGroup(group)}
          >
            <div class="flex items-center gap-2">
              {#if isGroupExpanded(group)}
                <ChevronDown size={16} class="text-primary-500" />
              {:else}
                <ChevronRight size={16} class="text-surface-500-400" />
              {/if}
              <span class="font-medium text-surface-900-100">{group}</span>
              <span class="text-xs text-surface-500-400">
                ({getProjectsByGroup(group).length})
              </span>
            </div>
          </button>

          {#if isGroupExpanded(group)}
            <div class="divide-y divide-surface-200-800">
              {#each getProjectsByGroup(group) as project}
                <div
                  class="flex items-center gap-3 p-2.5 hover:bg-surface-100-900/20"
                >
                  <div class="flex-1 min-w-0">
                    <div
                      class="font-medium text-surface-900-100 text-sm truncate"
                    >
                      {project.name}
                    </div>
                    <div class="text-xs text-surface-500-400 truncate">
                      {project.csproj_path}
                    </div>
                  </div>
                  {#if project.repo_url}
                    <button
                      class="btn preset-tonal p-1.5 hover:preset-filled-primary-500 transition-colors shrink-0"
                      onclick={() => openFolder(getProjectPath(project))}
                      title="Open project folder"
                    >
                      <FolderOpen size={12} />
                    </button>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</div>
