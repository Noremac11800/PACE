<script lang="ts">
  import {
    Download,
    Check,
    ChevronDown,
    ChevronRight,
    RefreshCw,
    Loader,
    Package,
    ExternalLink,
    Github,
  } from "@lucide/svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import {
    updateStatus,
    checkPypiForCliUpdate,
  } from "$lib/update-status.svelte";
  import { checkPaceInstalled, paceStatus } from "$lib/pace-status.svelte";
  import { View } from "$lib/panels/view-types";

  interface Props {
    onGoToPanel?: (view: View) => void;
  }

  let { onGoToPanel }: Props = $props();

  let showCliChangelog = $state(false);
  let showAppChangelog = $state(false);
  let isUpdatingCli = $state(false);
  let cliUpdateResult = $state("");

  async function updateCli() {
    isUpdatingCli = true;
    cliUpdateResult = "";
    try {
      const result = await Command.create("pipx", [
        "upgrade",
        "pace-dotnet",
      ]).execute();

      if (result.code === 0) {
        cliUpdateResult = "CLI updated successfully!";
        // Refresh the installed version status
        await checkPaceInstalled();
        // Re-check PyPI for latest (current should now match)
        await checkPypiForCliUpdate();
      } else {
        cliUpdateResult = `Update failed: ${result.stderr}`;
      }
    } catch (error) {
      cliUpdateResult = `Error: ${error}`;
    } finally {
      isUpdatingCli = false;
    }
  }
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
        {#if paceStatus.installed === false}
          <span
            class="text-xs font-medium px-2 py-0.5 rounded-full bg-error-500/20 text-error-500"
          >
            Not installed
          </span>
        {:else if updateStatus.cli.updateAvailable}
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

      {#if paceStatus.installed === false}
        <div class="text-sm text-surface-600-300 mb-3">
          <p class="text-error-500">PACE CLI is not installed.</p>
          <button
            class="mt-4 w-full flex items-center justify-between gap-2 rounded-lg bg-success-500/10 border border-success-500/30 px-4 py-3 text-sm text-success-500 hover:bg-success-500/20 transition-colors"
            onclick={() => onGoToPanel?.(View.DEPENDENCIES)}
          >
            <span class="flex items-center gap-2">
              <Package size={16} />
              Go to Dependencies panel to install
            </span>
            <ChevronRight size={16} />
          </button>
        </div>
      {:else}
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
            onclick={updateCli}
            disabled={isUpdatingCli}
            class="btn preset-filled-primary-500 text-sm"
          >
            {#if isUpdatingCli}
              <Loader size={14} class="animate-spin" />
              Updating...
            {:else}
              <RefreshCw size={14} />
              Update CLI
            {/if}
          </button>

          {#if cliUpdateResult}
            <div
              class="mt-2 text-xs"
              class:text-success-500={cliUpdateResult.includes("success")}
              class:text-error-500={!cliUpdateResult.includes("success")}
            >
              {cliUpdateResult}
            </div>
          {/if}
        {/if}

        <a
          href="https://pypi.org/project/pace-dotnet/"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-3 flex items-center justify-between gap-2 rounded-lg bg-surface-100-900/50 border border-surface-200-800 px-3 py-2 text-sm text-surface-700-200 hover:bg-primary-500/10 hover:border-primary-500/30 hover:text-primary-500 transition-colors"
        >
          <span class="flex items-center gap-2">
            <Package size={14} />
            View on PyPI
          </span>
          <ExternalLink size={12} />
        </a>
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

      <a
        href="https://github.com/Noremac11800/pace-dotnet-releases/releases"
        target="_blank"
        rel="noopener noreferrer"
        class="mt-3 flex items-center justify-between gap-2 rounded-lg bg-surface-100-900/50 border border-surface-200-800 px-3 py-2 text-sm text-surface-700-200 hover:bg-primary-500/10 hover:border-primary-500/30 hover:text-primary-500 transition-colors"
      >
        <span class="flex items-center gap-2">
          <Github size={16} />
          View on GitHub Releases
        </span>
        <ExternalLink size={12} />
      </a>
    </div>
  </div>
</div>
