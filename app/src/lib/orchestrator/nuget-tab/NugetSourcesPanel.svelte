<script lang="ts">
  import {
    RefreshCw,
    FolderOpen,
    Server,
    CircleCheckBig,
    CircleX,
    CircleAlert,
    Loader,
  } from "@lucide/svelte";
  import type { NugetSource } from "./types.ts";

  let {
    sources,
    loading,
    error,
    configDir,
    onrefresh,
    onopenConfig,
  }: {
    sources: NugetSource[];
    loading: boolean;
    error: string | null;
    configDir: string;
    onrefresh: () => void;
    onopenConfig: () => void;
  } = $props();
</script>

<div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <Server size={18} class="text-primary-500" />
      <span class="font-semibold text-surface-900-100">NuGet Sources</span>
    </div>
    <div class="flex items-center gap-2">
      {#if configDir}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
          onclick={onopenConfig}
          title="Open NuGet config folder"
        >
          <FolderOpen size={14} />
        </button>
      {/if}
      <button
        class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
        onclick={onrefresh}
        disabled={loading}
        title="Refresh sources"
      >
        <RefreshCw size={14} class={loading ? "animate-spin" : ""} />
        Refresh
      </button>
    </div>
  </div>

  {#if configDir}
    <code class="text-xs text-surface-500-400">{configDir}</code>
  {/if}

  {#if loading}
    <div class="flex items-center gap-2 text-sm text-surface-500-400 py-2">
      <Loader size={16} class="animate-spin" />
      Running dotnet nuget list source...
    </div>
  {:else if error}
    <div
      class="flex items-center gap-2 text-sm text-error-500 bg-error-500/10 rounded p-3"
    >
      <CircleAlert size={16} class="shrink-0" />
      <span class="break-all">{error}</span>
    </div>
  {:else if sources.length === 0}
    <p class="text-sm text-surface-500-400">No sources found.</p>
  {:else}
    <div class="flex flex-col gap-2">
      {#each sources as source (source.name)}
        <div class="flex flex-col bg-surface-100-900/50 rounded">
          <div class="flex items-start gap-3 p-3">
            {#if source.enabled}
              <CircleCheckBig
                size={16}
                class="text-success-500 mt-0.5 shrink-0"
              />
            {:else}
              <CircleX size={16} class="text-error-500 mt-0.5 shrink-0" />
            {/if}
            <div class="flex flex-col gap-0.5 min-w-0 flex-1">
              <span class="text-sm font-medium text-surface-900-100"
                >{source.name}</span
              >
              <code class="text-xs text-surface-500-400 break-all"
                >{source.url}</code
              >
            </div>
            <span
              class="ml-auto text-xs shrink-0 px-2 py-0.5 rounded-full {source.enabled
                ? 'bg-success-500/15 text-success-500'
                : 'bg-surface-300-700/30 text-surface-500-400'}"
            >
              {source.enabled ? "Enabled" : "Disabled"}
            </span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
