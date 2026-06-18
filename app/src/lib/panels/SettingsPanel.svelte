<script lang="ts">
  import {
    Settings,
    PanelRightClose,
    PanelRightOpen,
    Monitor,
    Palette,
    Database,
    RotateCcw,
  } from "@lucide/svelte";
  import { settings, resetSettings } from "$lib/state/settings.svelte";
  import { saveSettings, applyTheme } from "$lib/utils/app-init";
  import GeneralSection from "$lib/panels/settings/GeneralSection.svelte";
  import AppearanceSection from "$lib/panels/settings/AppearanceSection.svelte";
  import StorageSection from "$lib/panels/settings/StorageSection.svelte";

  interface TocEntry {
    id: string;
    label: string;
    icon: typeof Monitor;
  }

  const toc: TocEntry[] = [
    { id: "general", label: "General", icon: Monitor },
    { id: "appearance", label: "Appearance", icon: Palette },
    { id: "storage", label: "Storage", icon: Database },
  ];

  let activeSection = $state("general");
  let tocOpen = $state(true);
  let initialized = $state(false);
  let saveTimeout: ReturnType<typeof setTimeout> | null = null;

  const settingsSnapshot = $derived.by(() => ({
    theme: settings.general.theme,
    language: settings.general.language,
    autoCheckUpdates: settings.general.autoCheckUpdates,
    storageEndpointUrl: settings.general.storageEndpointUrl,
    fontSize: settings.appearance.fontSize,
    compactMode: settings.appearance.compactMode,
    paceCliPath: settings.cliPaths.paceCliPath,
    gitPath: settings.cliPaths.gitPath,
    dotnetPath: settings.cliPaths.dotnetPath,
    defaultSolutionDirectory: settings.projectDefaults.defaultSolutionDirectory,
    defaultBranch: settings.projectDefaults.defaultBranch,
    buildTab: { ...settings.buildTab },
    publishTab: { ...settings.publishTab },
    uploadTab: { ...settings.uploadTab },
    lastActiveConfig: settings.lastActiveConfig,
  }));

  $effect(() => {
    void settingsSnapshot;

    if (!initialized) {
      initialized = true;
      return;
    }

    if (saveTimeout) clearTimeout(saveTimeout);

    saveTimeout = setTimeout(() => {
      saveSettings().catch((err) => {
        console.error("[SettingsPanel] Failed to save settings:", err);
      });
    }, 300);

    return () => {
      if (saveTimeout) clearTimeout(saveTimeout);
    };
  });

  function scrollTo(id: string) {
    activeSection = id;
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
</script>

<div class="h-full flex flex-col overflow-hidden">
  <!-- Header -->
  <div
    class="flex items-center justify-between p-4 bg-surface-50-950 border-b border-surface-200-800"
  >
    <div class="flex items-center gap-2">
      <Settings size={24} class="text-primary-500" />
      <h2 class="h3 text-primary-500">Settings</h2>
    </div>
    <button
      class="btn preset-tonal flex items-center gap-2 text-sm"
      onclick={() => {
        if (confirm("Reset all settings to default? This cannot be undone.")) {
          resetSettings();
          applyTheme(settings.general.theme);
          saveSettings();
        }
      }}
      title="Reset all settings to default"
    >
      <RotateCcw size={14} />
      Reset to default
    </button>
  </div>

  <!-- Content Grid -->
  <div
    class="flex-1 grid overflow-hidden transition-[grid-template-columns] duration-300 ease-in-out grid-cols-[1fr_var(--toc-width)]"
    style="--toc-width: {tocOpen ? '220px' : '56px'};"
  >
    <!-- Main Content -->
    <div class="overflow-auto p-6 space-y-8" id="settings-content">
      <GeneralSection />
      <AppearanceSection />
      <StorageSection />
    </div>

    <!-- Sidebar TOC -->
    <div
      class="border-l border-surface-200-800 bg-surface-50-950 flex flex-col"
    >
      <button
        class="p-2 mx-2 mt-2 btn preset-tonal self-end"
        onclick={() => (tocOpen = !tocOpen)}
        title={tocOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        {#if tocOpen}
          <PanelRightClose size={20} />
        {:else}
          <PanelRightOpen size={20} />
        {/if}
      </button>

      <nav class="flex-1 overflow-auto p-2 space-y-1">
        {#each toc as entry (entry.id)}
          {@const Icon = entry.icon}
          <button
            class="w-full text-left {tocOpen
              ? 'px-3'
              : 'px-1'} py-2 rounded-md text-sm transition-colors flex items-center {tocOpen
              ? 'gap-2 justify-start'
              : 'justify-center'} {activeSection === entry.id
              ? 'bg-primary-500 text-white'
              : 'text-surface-700-300 hover:bg-surface-200-800'}"
            onclick={() => scrollTo(entry.id)}
            title={entry.label}
          >
            <Icon size={18} />
            {#if tocOpen}
              <span>{entry.label}</span>
            {:else}
              <span class="sr-only">{entry.label}</span>
            {/if}
          </button>
        {/each}
      </nav>
    </div>
  </div>
</div>
