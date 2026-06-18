<script lang="ts">
  import { ChevronDown, ChevronRight, FolderOpen } from "@lucide/svelte";
  import { getGitStatus, isLoadingGit } from "$lib/git-status.svelte";
  import ProjectGitStatusRow from "$lib/orchestrator/ProjectGitStatusRow.svelte";
  import type { PaceProject } from "$lib/pace-config";

  let {
    group,
    projects,
    expanded,
    ontoggle,
    onopenFolder,
  }: {
    group: string;
    projects: PaceProject[];
    expanded: boolean;
    ontoggle: () => void;
    onopenFolder: (project: PaceProject) => void;
  } = $props();

  let clonedCount = $derived(
    projects.filter((p) => getGitStatus(p)?.cloned).length,
  );
  let upToDateCount = $derived(
    projects.filter((p) => {
      const status = getGitStatus(p);
      return status?.cloned && status?.upToDate;
    }).length,
  );
</script>

<div class="card bg-surface-50-950 overflow-hidden">
  <!-- Group header -->
  <button
    class="w-full flex items-center justify-between p-3 text-left hover:bg-surface-100-900/30 transition-colors"
    onclick={ontoggle}
  >
    <div class="flex items-center gap-2">
      {#if expanded}
        <ChevronDown size={16} class="text-primary-500" />
      {:else}
        <ChevronRight size={16} class="text-surface-500-400" />
      {/if}
      <span class="font-semibold text-surface-900-100">{group}</span>
      <span class="text-xs text-surface-500-400">({projects.length})</span>
    </div>
    <span
      class="text-xs {upToDateCount === clonedCount && clonedCount > 0
        ? 'text-success-500'
        : 'text-warning-500'}"
    >
      {upToDateCount}/{clonedCount} up to date
    </span>
  </button>

  {#if expanded}
    <div class="border-t border-surface-200-800">
      {#each projects as project (project.name)}
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
            onclick={() => onopenFolder(project)}
            title="Open repository folder"
          >
            <FolderOpen size={14} />
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>
