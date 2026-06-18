<script lang="ts">
  import { GitBranch, Check, X, Loader } from "@lucide/svelte";
  import type { PaceProject, ProjectGitStatus } from "$lib/types/pace-config";

  interface Props {
    project: PaceProject;
    gitStatus: ProjectGitStatus | undefined;
    loading: boolean;
    compact?: boolean;
  }

  let { project, gitStatus, loading, compact = false }: Props = $props();
</script>

{#if compact}
  <!-- Compact row for Git tab -->
  <div
    class="flex items-center gap-3 py-2 px-3 border-b border-surface-100-900/50 hover:bg-surface-100-900/30"
  >
    <div class="flex-1 min-w-0">
      <div class="font-medium text-surface-900-100 text-sm truncate">
        {project.name}
      </div>
      <div class="text-xs text-surface-500-400 truncate">
        {project.csproj_path}
      </div>
    </div>

    <!-- Status badges -->
    <div class="flex items-center gap-2 shrink-0">
      {#if loading}
        <span
          class="inline-flex items-center gap-1 text-xs text-surface-500-400"
        >
          <Loader size={12} class="animate-spin" />
          Checking...
        </span>
      {:else if gitStatus}
        <!-- Cloned status -->
        <span
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium {gitStatus.cloned
            ? 'bg-success-500/10 text-success-500'
            : 'bg-error-500/10 text-error-500'}"
        >
          {#if gitStatus.cloned}
            <Check size={10} />
            Cloned
          {:else}
            <X size={10} />
            Missing
          {/if}
        </span>

        <!-- Up to date status -->
        {#if gitStatus.cloned}
          <span
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium {gitStatus.upToDate
              ? 'bg-success-500/10 text-success-500'
              : gitStatus.behindRemote
                ? 'bg-tertiary-500/10 text-tertiary-500'
                : 'bg-warning-500/10 text-warning-500'}"
          >
            {#if gitStatus.upToDate}
              <Check size={10} />
              Up to date
            {:else if gitStatus.behindRemote}
              <X size={10} />
              {gitStatus.aheadBehind || "Behind remote"}
            {:else}
              <X size={10} />
              {gitStatus.aheadBehind || "Changes"}
            {/if}
          </span>
        {/if}

        <!-- Branch -->
        {#if gitStatus.cloned}
          <span
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-primary-500/10 text-primary-500"
          >
            <GitBranch size={10} />
            {gitStatus.branch}
          </span>
        {/if}
      {:else}
        <span class="text-xs text-surface-500-400">-</span>
      {/if}
    </div>
  </div>
{:else}
  <!-- Full table row for Projects tab -->
  <tr class="border-b border-surface-100-900/50 hover:bg-surface-100-900/30">
    <td class="py-2 px-3">
      <div class="font-medium text-surface-900-100 break-words">
        {project.name}
      </div>
      <div class="text-xs text-surface-500-400 break-words">
        {project.csproj_path}
      </div>
    </td>
    <td class="py-2 px-3 text-center">
      {#if loading}
        <Loader size={16} class="animate-spin mx-auto text-primary-500" />
      {:else if gitStatus}
        {#if gitStatus.cloned}
          <Check size={18} class="mx-auto text-success-500" />
        {:else}
          <X size={18} class="mx-auto text-error-500" />
        {/if}
      {:else}
        <span class="text-surface-500-400">-</span>
      {/if}
    </td>
    <td class="py-2 px-3 text-center">
      {#if loading}
        <span class="text-surface-500-400">...</span>
      {:else if gitStatus?.cloned}
        {#if gitStatus.upToDate}
          <span class="inline-flex items-center gap-1 text-success-500">
            <Check size={14} />
            <span class="text-xs">Yes</span>
          </span>
        {:else if gitStatus.behindRemote}
          <span
            class="inline-flex items-center gap-1 text-tertiary-500"
            title={gitStatus.aheadBehind}
          >
            <X size={14} />
            <span class="text-xs break-all"
              >{gitStatus.aheadBehind || "Behind remote"}</span
            >
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
      {#if loading}
        <span class="text-surface-500-400">...</span>
      {:else if gitStatus?.cloned}
        <span class="inline-flex items-center gap-1 min-w-0">
          <GitBranch size={14} class="text-primary-500 shrink-0" />
          <span class="text-surface-700-300 break-all">{gitStatus.branch}</span>
        </span>
      {:else}
        <span class="text-surface-500-400">-</span>
      {/if}
    </td>
  </tr>
{/if}
