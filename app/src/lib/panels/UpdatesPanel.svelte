<script lang="ts">
  import {
    Download,
    Check,
    ChevronDown,
    ChevronRight,
    RefreshCw,
  } from "@lucide/svelte";
  import { updateStatus } from "$lib/update-status.svelte";

  let showCliChangelog = $state(false);
  let showAppChangelog = $state(false);
</script>

<div class="h-full flex flex-col overflow-hidden">
  <div
    class="flex items-center gap-2 p-4 bg-surface-50-950 border-b border-surface-200-800"
  >
    <Download size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Updates</h2>
  </div>

  <div class="flex-1 min-h-0 overflow-auto p-4 flex flex-col gap-4">
    <!-- PACE CLI Section -->
    <div class="card bg-surface-50-950 p-4 shadow-md">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-surface-900-50">PACE CLI</h3>
        {#if updateStatus.cli.updateAvailable}
          <span
            class="text-xs font-medium px-2 py-0.5 rounded-full bg-warning-500/20 text-warning-500"
          >
            Update available
          </span>
        {:else}
          <span
            class="text-xs font-medium px-2 py-0.5 rounded-full bg-success-500/20 text-success-500 flex items-center gap-1"
          >
            <Check size={12} /> Up to date
          </span>
        {/if}
      </div>

      <div class="text-sm text-surface-600-300 mb-3">
        <p>
          Current: <span class="font-mono"
            >{updateStatus.cli.currentVersion}</span
          >
        </p>
        {#if updateStatus.cli.updateAvailable}
          <p>
            Latest: <span class="font-mono text-warning-500"
              >{updateStatus.cli.latestVersion}</span
            >
          </p>
        {/if}
      </div>

      {#if updateStatus.cli.updateAvailable}
        {#if updateStatus.cli.changelog}
          <button
            class="text-xs text-primary-500 flex items-center gap-1 mb-2"
            onclick={() => (showCliChangelog = !showCliChangelog)}
          >
            {#if showCliChangelog}
              <ChevronDown size={14} />
            {:else}
              <ChevronRight size={14} />
            {/if}
            Changelog
          </button>
          {#if showCliChangelog}
            <pre
              class="text-xs bg-surface-100-900 rounded p-3 mb-3 overflow-auto max-h-40 font-mono whitespace-pre-wrap">{updateStatus
                .cli.changelog}</pre>
          {/if}
        {/if}

        <button
          onclick={() => (updateStatus.cli.updateAvailable = false)}
          class="btn preset-filled-primary-500 text-sm"
        >
          <RefreshCw size={14} />
          Update CLI
        </button>
      {/if}
    </div>

    <!-- PACE App Section -->
    <div class="card bg-surface-50-950 p-4 shadow-md">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-semibold text-surface-900-50">PACE App</h3>
        {#if updateStatus.app.updateAvailable}
          <span
            class="text-xs font-medium px-2 py-0.5 rounded-full bg-warning-500/20 text-warning-500"
          >
            Update available
          </span>
        {:else}
          <span
            class="text-xs font-medium px-2 py-0.5 rounded-full bg-success-500/20 text-success-500 flex items-center gap-1"
          >
            <Check size={12} /> Up to date
          </span>
        {/if}
      </div>

      <div class="text-sm text-surface-600-300 mb-3">
        <p>
          Current: <span class="font-mono"
            >{updateStatus.app.currentVersion}</span
          >
        </p>
        {#if updateStatus.app.updateAvailable}
          <p>
            Latest: <span class="font-mono text-warning-500"
              >{updateStatus.app.latestVersion}</span
            >
          </p>
        {/if}
      </div>

      {#if updateStatus.app.updateAvailable}
        {#if updateStatus.app.changelog}
          <button
            class="text-xs text-primary-500 flex items-center gap-1 mb-2"
            onclick={() => (showAppChangelog = !showAppChangelog)}
          >
            {#if showAppChangelog}
              <ChevronDown size={14} />
            {:else}
              <ChevronRight size={14} />
            {/if}
            Changelog
          </button>
          {#if showAppChangelog}
            <pre
              class="text-xs bg-surface-100-900 rounded p-3 mb-3 overflow-auto max-h-40 font-mono whitespace-pre-wrap">{updateStatus
                .app.changelog}</pre>
          {/if}
        {/if}

        <button
          onclick={() => (updateStatus.app.updateAvailable = false)}
          class="btn preset-filled-primary-500 text-sm"
        >
          <RefreshCw size={14} />
          Update App
        </button>
      {/if}
    </div>
  </div>
</div>
