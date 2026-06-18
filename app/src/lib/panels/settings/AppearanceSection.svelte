<script lang="ts">
  import { Palette } from "@lucide/svelte";
  import { settings } from "$lib/settings.svelte";
  import { applyTheme } from "$lib/app-init";
  import {
    SettingSelect,
    SettingRadioGroup,
  } from "$lib/snippets/SettingsSnippets.svelte";
</script>

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
        (settings.appearance.fontSize = v as "small" | "medium" | "large"),
      [
        { value: "small", label: "Small" },
        { value: "medium", label: "Medium" },
        { value: "large", label: "Large" },
      ],
    )}
  </div>
</section>
