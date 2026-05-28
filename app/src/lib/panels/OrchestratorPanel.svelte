<script lang="ts">
  import { onMount } from "svelte";
  import {
    Cog,
    Folder,
    FileCode,
    Package,
    Layers,
    Hammer,
    Rocket,
  } from "@lucide/svelte";
  import { loadPaceConfig, type PaceConfig } from "$lib/pace-config";
  import ProjectsTab from "$lib/orchestrator/ProjectsTab.svelte";
  import DependenciesTab from "$lib/orchestrator/DependenciesTab.svelte";
  import BuildTab from "$lib/orchestrator/BuildTab.svelte";
  import DeployTab from "$lib/orchestrator/DeployTab.svelte";
  import LogsTab from "$lib/orchestrator/LogsTab.svelte";

  let config = $state<PaceConfig | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let activeTab = $state<
    "projects" | "dependencies" | "build" | "deploy" | "logs"
  >("projects");

  onMount(async () => {
    try {
      const loadedConfig = await loadPaceConfig();
      if (loadedConfig) {
        config = loadedConfig;
      } else {
        error = "Failed to load PACE configuration";
      }
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error";
    } finally {
      loading = false;
    }
  });

  const tabs = [
    { id: "projects" as const, label: "Projects", icon: Folder },
    { id: "dependencies" as const, label: "Dependencies", icon: Package },
    { id: "build" as const, label: "Build", icon: Hammer },
    { id: "deploy" as const, label: "Deploy", icon: Rocket },
    { id: "logs" as const, label: "Logs", icon: FileCode },
  ];
</script>

<div class="h-full flex flex-col overflow-hidden">
  <!-- Header -->
  <div
    class="flex items-center gap-2 p-4 bg-surface-50-950 border-b border-surface-200-800 shrink-0"
  >
    <Cog size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Orchestrator</h2>
  </div>

  <!-- Tabs -->
  <div
    class="flex border-b border-surface-200-800 bg-surface-50-950 shrink-0 overflow-x-auto"
  >
    {#each tabs as tab}
      <button
        class="flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap {activeTab ===
        tab.id
          ? 'text-primary-500 border-b-2 border-primary-500 bg-surface-100-900/50'
          : 'text-surface-600-400 hover:text-surface-900-100 hover:bg-surface-100-900/30'}"
        onclick={() => (activeTab = tab.id)}
      >
        <svelte:component this={tab.icon} size={16} />
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Tab Content -->
  <div class="flex-1 overflow-auto p-4">
    {#if loading}
      <div class="flex-1 flex items-center justify-center min-h-[200px]">
        <div class="text-center">
          <Cog size={48} class="mx-auto mb-4 text-primary-500 animate-spin" />
          <p class="text-surface-700-300">Loading PACE configuration...</p>
        </div>
      </div>
    {:else if error}
      <div class="flex-1 flex items-center justify-center min-h-[200px]">
        <div
          class="card bg-error-500/10 border border-error-500 p-6 text-center max-w-md"
        >
          <p class="text-error-500 font-semibold mb-2">Error</p>
          <p class="text-surface-700-300">{error}</p>
        </div>
      </div>
    {:else if config}
      {#if activeTab === "projects"}
        <ProjectsTab {config} />
      {:else if activeTab === "dependencies"}
        <DependenciesTab />
      {:else if activeTab === "build"}
        <BuildTab />
      {:else if activeTab === "deploy"}
        <DeployTab />
      {:else if activeTab === "logs"}
        <LogsTab />
      {/if}
    {/if}
  </div>
</div>
