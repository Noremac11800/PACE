<script lang="ts">
  import { onMount } from "svelte";
  import {
    Cog,
    Folder,
    GitBranch,
    Hammer,
    Rocket,
    PenLine,
    Package,
    RefreshCw,
    FolderOpen,
  } from "@lucide/svelte";
  import { revealItemInDir } from "@tauri-apps/plugin-opener";
  import {
    configStore,
    loadAvailableConfigs,
    loadConfig,
    getActiveConfigPath,
  } from "$lib/config-store.svelte";
  import { settings } from "$lib/settings.svelte";
  import ProjectsTab from "$lib/orchestrator/ProjectsTab.svelte";
  import BuildTab from "$lib/orchestrator/BuildTab.svelte";
  import DeployTab from "$lib/orchestrator/DeployTab.svelte";
  import GitTab from "$lib/orchestrator/GitTab.svelte";
  import ConfigEditorTab from "$lib/orchestrator/ConfigEditorTab.svelte";
  import NugetTab from "$lib/orchestrator/NugetTab.svelte";
  import ConfigSelector from "$lib/panels/ConfigSelector.svelte";

  let refreshing = $state(false);

  async function refreshConfig() {
    if (!configStore.activeConfigName || refreshing) return;
    refreshing = true;
    try {
      await loadConfig(configStore.activeConfigName);
    } finally {
      refreshing = false;
    }
  }

  async function openConfigFolder() {
    const configPath = await getActiveConfigPath();
    if (configPath) {
      await revealItemInDir(configPath);
    }
  }

  let activeTab = $state<
    "projects" | "build" | "deploy" | "git" | "editor" | "nuget"
  >("projects");

  const allTabs = [
    { id: "projects" as const, label: "Projects", icon: Folder },
    { id: "nuget" as const, label: "NuGet", icon: Package },
    { id: "git" as const, label: "Git", icon: GitBranch },
    { id: "build" as const, label: "Build", icon: Hammer },
    { id: "deploy" as const, label: "Deploy", icon: Rocket },
    { id: "editor" as const, label: "Config editor", icon: PenLine },
  ];

  const isDefaultConfig = $derived(
    configStore.activeConfigName === "default.toml",
  );

  const tabs = $derived(
    allTabs.filter((tab) => tab.id !== "editor" || !isDefaultConfig),
  );

  $effect(() => {
    if (isDefaultConfig && activeTab === "editor") {
      activeTab = "projects";
    }
  });

  onMount(async () => {
    await loadAvailableConfigs();
    if (
      configStore.availableConfigs.length > 0 &&
      !configStore.activeConfigName
    ) {
      const saved = settings.lastActiveConfig;
      const match = saved
        ? configStore.availableConfigs.find((c) => c.filename === saved)
        : null;
      const toLoad = match
        ? match.filename
        : configStore.availableConfigs[0].filename;
      await loadConfig(toLoad);
    }
  });
</script>

<div class="h-full flex flex-col overflow-hidden">
  <!-- Header -->
  <div
    class="flex items-center justify-between gap-2 px-4 py-3 bg-surface-50-950 border-b border-surface-200-800 shrink-0"
  >
    <div class="flex items-center gap-2">
      <Cog size={24} class="text-primary-500" />
      <h2 class="h3 text-primary-500">Orchestrator</h2>
    </div>

    <div class="flex items-center gap-2">
      <button
        class="btn preset-tonal p-2 hover:preset-filled-primary-500 transition-colors"
        onclick={refreshConfig}
        disabled={refreshing || !configStore.activeConfigName}
        title="Refresh config"
      >
        <RefreshCw size={16} class={refreshing ? "animate-spin" : ""} />
      </button>
      <button
        class="btn preset-tonal p-2 hover:preset-filled-primary-500 transition-colors"
        onclick={openConfigFolder}
        disabled={!configStore.activeConfigName}
        title="Open config folder"
      >
        <FolderOpen size={16} />
      </button>
      <ConfigSelector />
    </div>
  </div>

  <!-- Tabs -->
  <div
    class="flex border-b border-surface-200-800 bg-surface-50-950 shrink-0 overflow-x-auto"
  >
    {#each tabs as tab}
      {@const Icon = tab.icon}
      <button
        class="flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap {activeTab ===
        tab.id
          ? 'text-primary-500 border-b-2 border-primary-500 bg-surface-100-900/50'
          : 'text-surface-600-400 hover:text-surface-900-100 hover:bg-surface-100-900/30'}"
        onclick={() => (activeTab = tab.id)}
      >
        <Icon size={16} />
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Tab Content -->
  <div class="flex-1 overflow-hidden flex flex-col">
    {#if configStore.loading}
      <div class="flex-1 flex items-center justify-center min-h-[200px]">
        <div class="text-center">
          <Cog size={48} class="mx-auto mb-4 text-primary-500 animate-spin" />
          <p class="text-surface-700-300">Loading PACE configuration...</p>
        </div>
      </div>
    {:else if configStore.error}
      <div class="flex items-center justify-center min-h-[200px] p-4">
        <div
          class="card bg-error-500/10 border border-error-500 p-6 text-center max-w-md"
        >
          <p class="text-error-500 font-semibold mb-2">Error</p>
          <p class="text-surface-700-300 break-all">{configStore.error}</p>
        </div>
      </div>
    {:else}
      <!-- Editor Tab -->
      <div
        class="flex-1 overflow-auto p-4"
        class:hidden={activeTab !== "editor"}
      >
        {#if configStore.activeConfig}
          <ConfigEditorTab />
        {:else}
          <div
            class="flex items-center justify-center min-h-[200px] text-surface-500-400 text-sm"
          >
            Select or create a config to start editing.
          </div>
        {/if}
      </div>
      <!-- Other Tabs (only show if config loaded) -->
      {#if configStore.activeConfig}
        <div
          class="flex-1 overflow-auto p-4"
          class:hidden={activeTab !== "projects"}
        >
          <ProjectsTab config={configStore.activeConfig} />
        </div>
        <div
          class="flex-1 overflow-auto p-4"
          class:hidden={activeTab !== "nuget"}
        >
          <NugetTab />
        </div>
        <div
          class="flex-1 flex flex-col overflow-hidden"
          class:hidden={activeTab !== "build"}
        >
          <BuildTab />
        </div>
        <div
          class="flex-1 overflow-auto p-4"
          class:hidden={activeTab !== "deploy"}
        >
          <DeployTab />
        </div>
        <div
          class="flex-1 overflow-auto p-4"
          class:hidden={activeTab !== "git"}
        >
          <GitTab />
        </div>
      {:else}
        <div
          class="flex items-center justify-center min-h-[200px] p-4 text-surface-500-400 text-sm"
        >
          No config loaded. Use the picker above to select or create one.
        </div>
      {/if}
    {/if}
  </div>
</div>
