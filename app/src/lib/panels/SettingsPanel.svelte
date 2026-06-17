<script lang="ts">
  import {
    Settings,
    PanelRightClose,
    PanelRightOpen,
    Monitor,
    Palette,
    Database,
    ExternalLink,
    RotateCcw,
    AlertTriangle,
    Check,
  } from "@lucide/svelte";
  import { openUrl } from "@tauri-apps/plugin-opener";
  import { settings, resetSettings } from "$lib/settings.svelte";
  import { saveSettings, applyTheme } from "$lib/app-init";
  import {
    SettingSwitch,
    SettingSelect,
    SettingRadioGroup,
  } from "$lib/snippets/SettingsSnippets.svelte";

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

  // Derived state for endpoint URL validation
  const endpointUrl = $derived(settings.general.storageEndpointUrl);
  const endpointUrlValid = $derived(
    !endpointUrl ||
      endpointUrl.startsWith("http://") ||
      endpointUrl.startsWith("https://"),
  );

  // Explicitly track all settings values for reactivity
  $effect(() => {
    // Track general settings
    const theme = settings.general.theme;
    const language = settings.general.language;
    const autoCheckUpdates = settings.general.autoCheckUpdates;
    const storageEndpointUrl = settings.general.storageEndpointUrl;

    // Track appearance settings
    const fontSize = settings.appearance.fontSize;
    const compactMode = settings.appearance.compactMode;

    // Track CLI paths
    const paceCliPath = settings.cliPaths.paceCliPath;
    const gitPath = settings.cliPaths.gitPath;
    const dotnetPath = settings.cliPaths.dotnetPath;

    // Track project defaults
    const defaultSolutionDirectory =
      settings.projectDefaults.defaultSolutionDirectory;
    const defaultBranch = settings.projectDefaults.defaultBranch;

    // Track tab settings
    const buildTab = { ...settings.buildTab };
    const publishTab = { ...settings.publishTab };
    const uploadTab = { ...settings.uploadTab };

    // Track last active config
    const lastActiveConfig = settings.lastActiveConfig;

    if (!initialized) {
      initialized = true;
      return;
    }

    // Clear any pending save
    if (saveTimeout) {
      clearTimeout(saveTimeout);
    }

    // Debounce the save
    saveTimeout = setTimeout(() => {
      saveSettings().catch((err) => {
        console.error("[SettingsPanel] Failed to save settings:", err);
      });
    }, 300);
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
    class="flex-1 grid overflow-hidden transition-[grid-template-columns] duration-300 ease-in-out"
    style="grid-template-columns: 1fr {tocOpen ? '220px' : '56px'};"
  >
    <!-- Main Content -->
    <div class="overflow-auto p-6 space-y-8" id="settings-content">
      <!-- General Section -->
      <section id="general" class="border-b border-surface-200-800 pb-8">
        <h2 class="h2 text-primary-500 mb-4 flex items-center gap-2">
          <Monitor size={24} class="text-primary-500" />
          General
        </h2>
        <div class="space-y-1">
          {@render SettingSelect(
            "Language",
            "Select the application language",
            settings.general.language,
            (v) => (settings.general.language = v),
            [
              { value: "en", label: "English" },
              { value: "es", label: "Spanish" },
              { value: "fr", label: "French" },
              { value: "de", label: "German" },
            ],
          )}
          {@render SettingSwitch(
            "Auto-check for updates",
            "Automatically check for CLI and app updates on startup",
            settings.general.autoCheckUpdates,
            (v) => (settings.general.autoCheckUpdates = v),
          )}
        </div>
      </section>

      <!-- Appearance Section -->
      <section id="appearance" class="border-b border-surface-200-800 pb-8">
        <h2 class="h2 text-primary-500 mb-4 flex items-center gap-2">
          <Palette size={24} class="text-primary-500" />
          Appearance
        </h2>
        <div class="space-y-1">
          {@render SettingSelect(
            "Theme",
            "Choose your preferred color theme",
            settings.general.theme,
            (v) => {
              settings.general.theme = v as "light" | "dark" | "system";
              applyTheme(settings.general.theme);
            },
            [
              { value: "light", label: "Light" },
              { value: "dark", label: "Dark" },
              { value: "system", label: "System" },
            ],
          )}
          {@render SettingRadioGroup(
            "Font Size",
            "Select the base font size for the application",
            settings.appearance.fontSize,
            (v) =>
              (settings.appearance.fontSize = v as
                | "small"
                | "medium"
                | "large"),
            [
              { value: "small", label: "Small" },
              { value: "medium", label: "Medium" },
              { value: "large", label: "Large" },
            ],
          )}
        </div>
      </section>

      <!-- Storage Section -->
      <section id="storage" class="pb-8">
        <h2 class="h2 text-primary-500 mb-4 flex items-center gap-2">
          <Database size={24} class="text-primary-500" />
          Storage
        </h2>
        <div class="space-y-1">
          <!-- Storage Endpoint URL Input with Open Button -->
          <div
            class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
          >
            <label
              class="block text-sm font-semibold text-surface-900-50 mb-2"
              for="storage-endpoint-url">Application storage endpoint URL</label
            >
            <p class="text-xs text-surface-600-300 mb-2 leading-relaxed">
              Configure the endpoint URL for application storage uploads
            </p>
            <div class="input-group grid grid-cols-[1fr_auto]">
              <input
                id="storage-endpoint-url"
                type="text"
                class="ig-input {endpointUrl && !endpointUrlValid
                  ? 'border-warning-500 focus:border-warning-500'
                  : ''}"
                placeholder="https://company.storage.com"
                bind:value={settings.general.storageEndpointUrl}
              />
              <button
                class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
                type="button"
                title="Open in browser"
                onclick={async () => {
                  let url = settings.general.storageEndpointUrl;
                  if (!url) return;
                  if (
                    !url.startsWith("http://") &&
                    !url.startsWith("https://")
                  ) {
                    url = "https://" + url;
                  }
                  try {
                    await openUrl(url);
                  } catch (e) {
                    console.error("Failed to open URL:", e);
                  }
                }}
              >
                <ExternalLink size={16} />
              </button>
            </div>
            {#if endpointUrl && !endpointUrlValid}
              <div
                class="flex items-center gap-1.5 mt-2 text-xs text-warning-600-400"
              >
                <AlertTriangle size={12} />
                <span>URL must start with http:// or https://</span>
              </div>
            {:else if endpointUrl && endpointUrlValid}
              <div
                class="flex items-center gap-1.5 mt-2 text-xs text-success-600-400"
              >
                <Check size={12} />
                <span>Valid URL format</span>
              </div>
            {/if}
          </div>
        </div>
      </section>
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
