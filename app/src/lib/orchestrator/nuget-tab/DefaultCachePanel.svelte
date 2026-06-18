<script lang="ts">
  import {
    Package,
    RefreshCw,
    FolderOpen,
    CircleAlert,
    Loader,
    Trash2,
  } from "@lucide/svelte";
  import type { CachedPackage } from "./types.ts";
  import CachedPackageList from "./CachedPackageList.svelte";

  let {
    path,
    loading,
    cleaning,
    error,
    packages,
    filtered,
    projectsCount,
    onrefresh,
    onclean,
    onopenFolder,
  }: {
    path: string;
    loading: boolean;
    cleaning: boolean;
    error: string | null;
    packages: CachedPackage[];
    filtered: CachedPackage[];
    projectsCount: number;
    onrefresh: () => void;
    onclean: () => void;
    onopenFolder: () => void;
  } = $props();
</script>

<div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <Package size={18} class="text-primary-500" />
      <span class="font-semibold text-surface-900-100">Default NuGet Cache</span>
    </div>
    <div class="flex items-center gap-2">
      {#if !loading && path}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
          onclick={onopenFolder}
          title="Open folder"
        >
          <FolderOpen size={14} />
        </button>
      {/if}
      <button
        class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
        onclick={onrefresh}
        disabled={loading || cleaning}
        title="Refresh packages"
      >
        <RefreshCw size={14} class={loading ? "animate-spin" : ""} />
        Refresh
      </button>
      <button
        class="btn preset-filled-error-500 flex items-center gap-1.5 text-xs py-1 px-2"
        onclick={onclean}
        disabled={cleaning || loading}
        title="Clean default cache"
      >
        {#if cleaning}
          <Loader size={14} class="animate-spin" />
          Cleaning...
        {:else}
          <Trash2 size={14} />
          Clean
        {/if}
      </button>
    </div>
  </div>

  {#if !loading && path}
    <code class="text-xs text-surface-500-400">{path}</code>
  {/if}

  {#if projectsCount > 0}
    <p class="text-xs text-surface-500-400">
      Showing packages matching {projectsCount} project{projectsCount === 1
        ? ""
        : "s"} from the active config.
    </p>
  {/if}

  {#if loading}
    <div class="flex items-center gap-2 text-sm text-surface-500-400 py-2">
      <Loader size={16} class="animate-spin" />
      Scanning cache directory...
    </div>
  {:else if error}
    <div
      class="flex items-center gap-2 text-sm text-error-500 bg-error-500/10 rounded p-3"
    >
      <CircleAlert size={16} class="shrink-0" />
      <span class="break-all">{error}</span>
    </div>
  {:else if packages.length > 0}
    <CachedPackageList total={packages} {filtered} />
  {:else if !loading}
    <div
      class="flex items-center gap-2 text-sm text-surface-500-400 bg-surface-100-900/40 rounded p-3"
    >
      <CircleAlert size={16} class="shrink-0" />
      No packages found in the default cache directory.
    </div>
  {/if}
</div>
