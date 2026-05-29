<script lang="ts">
  import {
    Settings,
    PanelRightClose,
    PanelRightOpen,
    Monitor,
    Terminal,
    Folder,
    Palette,
  } from "@lucide/svelte";
  import { settings } from "$lib/settings.svelte";
  import { saveSettings } from "$lib/app-init";
  import {
    SettingSwitch,
    SettingInput,
    SettingFolderPicker,
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
    { id: "cli-paths", label: "CLI paths", icon: Terminal },
    { id: "project-defaults", label: "Project defaults", icon: Folder },
    { id: "appearance", label: "Appearance", icon: Palette },
  ];

  let activeSection = $state("general");
  let tocOpen = $state(true);
  let initialized = $state(false);

  $effect(() => {
    JSON.stringify(settings);
    if (!initialized) {
      initialized = true;
      return;
    }
    saveSettings();
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
    class="flex items-center gap-2 p-4 bg-surface-50-950 border-b border-surface-200-800"
  >
    <Settings size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Settings</h2>
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
            "Theme",
            "Choose your preferred color theme",
            settings.general.theme,
            (v) => (settings.general.theme = v as "light" | "dark" | "system"),
            [
              { value: "light", label: "Light" },
              { value: "dark", label: "Dark" },
              { value: "system", label: "System" },
            ],
          )}
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

      <!-- CLI Paths Section -->
      <section id="cli-paths" class="border-b border-surface-200-800 pb-8">
        <h2 class="h2 text-primary-500 mb-4 flex items-center gap-2">
          <Terminal size={24} class="text-primary-500" />
          CLI paths
        </h2>
        <div class="space-y-1">
          {@render SettingFolderPicker(
            "PACE CLI Path",
            "Path to the PACE CLI executable",
            settings.cliPaths.paceCliPath,
            (v) => (settings.cliPaths.paceCliPath = v),
          )}
          {@render SettingFolderPicker(
            "Git Path",
            "Path to the Git executable",
            settings.cliPaths.gitPath,
            (v) => (settings.cliPaths.gitPath = v),
          )}
          {@render SettingFolderPicker(
            ".NET Path",
            "Path to the .NET SDK",
            settings.cliPaths.dotnetPath,
            (v) => (settings.cliPaths.dotnetPath = v),
          )}
        </div>
      </section>

      <!-- Project Defaults Section -->
      <section
        id="project-defaults"
        class="border-b border-surface-200-800 pb-8"
      >
        <h2 class="h2 text-primary-500 mb-4 flex items-center gap-2">
          <Folder size={24} class="text-primary-500" />
          Project defaults
        </h2>
        <div class="space-y-1">
          {@render SettingFolderPicker(
            "Default Solution Directory",
            "Default directory for new solutions",
            settings.projectDefaults.defaultSolutionDirectory,
            (v) => (settings.projectDefaults.defaultSolutionDirectory = v),
          )}
          {@render SettingInput(
            "Default Branch",
            "Default branch name for new repositories",
            settings.projectDefaults.defaultBranch,
            (v) => (settings.projectDefaults.defaultBranch = v),
          )}
        </div>
      </section>

      <!-- Appearance Section -->
      <section id="appearance" class="pb-8">
        <h2 class="h2 text-primary-500 mb-4 flex items-center gap-2">
          <Palette size={24} class="text-primary-500" />
          Appearance
        </h2>
        <div class="space-y-1">
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
          {@render SettingSwitch(
            "Compact Mode",
            "Use a more compact layout to show more content",
            settings.appearance.compactMode,
            (v) => (settings.appearance.compactMode = v),
          )}
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
        {#each toc as entry}
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
