<script lang="ts">
  import { Monitor } from "@lucide/svelte";
  import { settings } from "$lib/settings.svelte";
  import {
    SettingSwitch,
    SettingSelect,
  } from "$lib/snippets/SettingsSnippets.svelte";
</script>

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
