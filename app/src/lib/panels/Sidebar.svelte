<script lang="ts">
  import {
    House,
    Package,
    Terminal,
    CircleQuestionMark,
    FileCode,
    Network,
    Settings,
    Download,
    TriangleAlert,
    Check,
    Cog,
    Loader,
  } from "@lucide/svelte";
  import { View } from "$lib/panels/view-types";
  import { updateStatus } from "$lib/update-status.svelte";
  import { theme } from "$lib/theme";
  import { isAnyCommandRunning } from "$lib/orchestrator/command-status.svelte";

  interface Props {
    activeView: View;
    paceInstalledStatus: boolean | undefined;
  }

  let { activeView = $bindable(), paceInstalledStatus }: Props = $props();

  let paceReady = $derived(paceInstalledStatus === true);
  let hasUpdates = $derived(
    updateStatus.cli.updateAvailable || updateStatus.app.updateAvailable,
  );
</script>

<aside
  class="flex flex-col items-center gap-2 p-2 bg-surface-50-950 border-r border-surface-200-800"
>
  <button
    class="btn {activeView === View.HOME
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.HOME)}
    title="Home"
  >
    <House size={20} />
  </button>
  <button
    class="btn {activeView === View.DEPENDENCIES
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2 relative"
    onclick={() => (activeView = View.DEPENDENCIES)}
    title="Dependencies"
  >
    <Package size={20} />
    {#if paceInstalledStatus === false}
      <span
        class="absolute -top-1.5 -right-1.5 bg-error-500 text-surface-50 rounded-full p-0.5"
      >
        <TriangleAlert size={10} />
      </span>
    {/if}
  </button>
  <button
    class="btn {activeView === View.DIRECTORY_BUILD_PROPS
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.DIRECTORY_BUILD_PROPS)}
    title="Directory.Build.props"
    disabled={!paceReady}
  >
    <FileCode size={20} />
  </button>
  <button
    class="btn {activeView === View.PROJECT_GRAPH
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.PROJECT_GRAPH)}
    title="Project Graph"
    disabled={!paceReady}
  >
    <Network size={20} />
  </button>
  <button
    class="btn {activeView === View.ORCHESTRATOR
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2 relative"
    onclick={() => (activeView = View.ORCHESTRATOR)}
    title="Orchestrator"
    disabled={!paceReady}
  >
    {#if isAnyCommandRunning()}
      <Loader size={20} class="animate-spin" />
    {:else}
      <Cog size={20} />
    {/if}
  </button>
  <button
    class="btn {activeView === View.CONSOLE
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.CONSOLE)}
    title="Console"
    disabled={!paceReady}
  >
    <Terminal size={20} />
  </button>
  <div class="flex-1"></div>
  <button
    class="btn {activeView === View.SETTINGS
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.SETTINGS)}
    title="Settings"
  >
    <Settings size={20} />
  </button>
  <button
    class="btn {activeView === View.HELP
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.HELP)}
    title="Help"
  >
    <CircleQuestionMark size={20} />
  </button>
  <button
    class="btn {activeView === View.ABOUT
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2"
    onclick={() => (activeView = View.ABOUT)}
    title="About"
  >
    {#if activeView === View.ABOUT}
      <img src="/appglyph.svg" alt="PACE Logo" class="w-5 h-5" />
    {:else if $theme === "dark"}
      <img src="/appglyph.svg" alt="PACE Logo" class="w-5 h-5" />
    {:else}
      <img src="/appglyph-dark.svg" alt="PACE Logo" class="w-5 h-5" />
    {/if}
  </button>
  <button
    class="btn {activeView === View.UPDATES
      ? 'preset-filled-primary-500'
      : 'preset-tonal'} p-2 relative"
    onclick={() => (activeView = View.UPDATES)}
    title="Updates"
  >
    <Download size={20} />
    {#if paceInstalledStatus !== false && hasUpdates}
      <span
        class="absolute -top-1.5 -right-1.5 bg-warning-500 text-surface-950 rounded-full p-0.5"
      >
        <TriangleAlert size={12} />
      </span>
    {:else if paceInstalledStatus !== false}
      <span
        class="absolute -top-1.5 -right-1.5 bg-success-500 text-surface-950 rounded-full p-0.5"
      >
        <Check size={12} />
      </span>
    {/if}
  </button>
</aside>
