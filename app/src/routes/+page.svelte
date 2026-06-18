<script lang="ts">
  import { goto } from "$app/navigation";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";
  import { View } from "$lib/panels/view-types";
  import Sidebar from "$lib/panels/Sidebar.svelte";
  import HomePanel from "$lib/panels/HomePanel.svelte";
  import DependenciesPanel from "$lib/panels/DependenciesPanel.svelte";
  import ConsolePanel from "$lib/panels/ConsolePanel.svelte";
  import HelpPanel from "$lib/panels/HelpPanel.svelte";
  import AboutPanel from "$lib/panels/AboutPanel.svelte";
  import DirectoryBuildPropsPanel from "$lib/panels/DirectoryBuildPropsPanel.svelte";
  import ProjectGraphPanel from "$lib/panels/ProjectGraphPanel.svelte";
  import SettingsPanel from "$lib/panels/SettingsPanel.svelte";
  import UpdatesPanel from "$lib/panels/UpdatesPanel.svelte";
  import OrchestratorPanel from "$lib/panels/OrchestratorPanel.svelte";
  import {
    paceStatus,
    checkPaceInstalled,
  } from "$lib/state/pace-status.svelte";
  import { fetchAppVersion, appVersion } from "$lib/state/app-version.svelte";
  import { onMount } from "svelte";

  let activeView: View = $state(View.HOME);

  let version = $derived(`v${appVersion.version}`);

  onMount(() => {
    checkPaceInstalled();
    fetchAppVersion();
  });
</script>

<main class="h-full grid grid-cols-[auto_1fr] grid-rows-[auto_1fr_auto]">
  <!-- Header -->
  <header
    class="col-span-2 flex flex-row justify-between items-center px-4 py-2 border-b border-surface-200-800"
  >
    <div class="flex items-center gap-3">
      <img src="/appicon.svg" alt="PACE" class="h-8 w-8" />
      <div class="flex flex-col">
        <span
          class="text-xl font-black tracking-tight bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent"
        >
          PACE
        </span>
        <span
          class="text-[10px] font-medium tracking-widest text-surface-700-300 uppercase"
        >
          Project Automation & Configuration Engine
        </span>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <ThemeSwitch />
    </div>
  </header>

  <Sidebar bind:activeView paceInstalledStatus={paceStatus.installed} />

  <!-- Main Content -->
  <div class="relative min-h-0 bg-surface-100-900/25 overflow-hidden">
    <div class="absolute inset-0" class:hidden={activeView !== View.HOME}>
      <HomePanel onGoToPanel={(view) => (activeView = view)} />
    </div>
    <div
      class="absolute inset-0"
      class:hidden={activeView !== View.DEPENDENCIES}
    >
      <DependenciesPanel />
    </div>
    <div
      class="absolute inset-0"
      class:hidden={activeView !== View.DIRECTORY_BUILD_PROPS}
    >
      <DirectoryBuildPropsPanel />
    </div>
    {#if activeView === View.PROJECT_GRAPH}
      <div class="absolute inset-0">
        <ProjectGraphPanel />
      </div>
    {/if}
    <div
      class="absolute inset-0"
      class:hidden={activeView !== View.ORCHESTRATOR}
    >
      <OrchestratorPanel onGoToPanel={(view) => (activeView = view)} />
    </div>
    <div class="absolute inset-0" class:hidden={activeView !== View.CONSOLE}>
      <ConsolePanel />
    </div>
    <div class="absolute inset-0" class:hidden={activeView !== View.SETTINGS}>
      <SettingsPanel />
    </div>
    <div class="absolute inset-0" class:hidden={activeView !== View.HELP}>
      <HelpPanel />
    </div>
    <div class="absolute inset-0" class:hidden={activeView !== View.ABOUT}>
      <AboutPanel />
    </div>
    <div class="absolute inset-0" class:hidden={activeView !== View.UPDATES}>
      <UpdatesPanel onGoToPanel={(view) => (activeView = view)} />
    </div>
  </div>

  <!-- Footer -->
  <footer
    class="col-span-2 flex items-center justify-end bg-surface-50-950 px-2 py-1 border-t border-surface-200-800"
  >
    <!-- <button
      class="btn preset-filled-primary-500 text-xs"
      onclick={() => goto("/sandbox")}
    >
      <Bug size={16} />
      Go to sandbox
    </button> -->

    <button
      onclick={() => goto("/sandbox")}
      class="text-end text-xs text-surface-500-400"
    >
      {version}
    </button>
  </footer>
</main>
