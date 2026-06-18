<script lang="ts">
  import {
    RefreshCw,
    FolderOpen,
    CircleAlert,
    Loader,
    Trash2,
  } from "@lucide/svelte";
  import type { CachedPackage } from "./types.ts";
  import CachedPackageList from "./CachedPackageList.svelte";

  let {
    path = $bindable(""),
    loading,
    cleaning,
    error,
    packages,
    filtered,
    onrefresh,
    onclean,
    onopenFolder,
    onbrowse,
    oninput,
  }: {
    path?: string;
    loading: boolean;
    cleaning: boolean;
    error: string | null;
    packages: CachedPackage[];
    filtered: CachedPackage[];
    onrefresh: () => void;
    onclean: () => void;
    onopenFolder: () => void;
    onbrowse: () => void;
    oninput: () => void;
  } = $props();
</script>

<div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <FolderOpen size={18} class="text-primary-500" />
      <span class="font-semibold text-surface-900-100">Custom Cache Path</span>
    </div>
    <div class="flex items-center gap-2">
      {#if path}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
          onclick={onopenFolder}
          title="Open folder"
        >
          <FolderOpen size={14} />
        </button>
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
          disabled={cleaning || loading || !path}
          title="Clean custom cache"
        >
          {#if cleaning}
            <Loader size={14} class="animate-spin" />
            Cleaning...
          {:else}
            <Trash2 size={14} />
            Clean
          {/if}
        </button>
      {/if}
    </div>
  </div>

  <div class="input-group grid grid-cols-[1fr_auto]">
    <input
      class="ig-input font-mono text-sm"
      type="text"
      placeholder="/path/to/nuget/packages"
      bind:value={path}
      {oninput}
    />
    <button
      class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
      type="button"
      onclick={onbrowse}
      title="Browse"
    >
      <FolderOpen size={16} />
    </button>
  </div>

  {#if loading}
    <div class="flex items-center gap-2 text-sm text-surface-500-400 py-2">
      <Loader size={16} class="animate-spin" />
      Scanning custom cache directory...
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
  {:else if path && !loading}
    <div
      class="flex items-center gap-2 text-sm text-surface-500-400 bg-surface-100-900/40 rounded p-3"
    >
      <CircleAlert size={16} class="shrink-0" />
      No .nupkg files found in this directory.
    </div>
  {:else if !path}
    <p class="text-sm text-surface-500-400">
      Select a folder to load packages from a custom NuGet cache location.
    </p>
  {/if}
</div>
