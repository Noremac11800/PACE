<script lang="ts">
  import { ChevronLeft } from "@lucide/svelte";
  import { setContext } from "svelte";
  import LanguageSwitcher from "$lib/components/LanguageSwitcher.svelte";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";
  import { fetchAppVersion, appVersion } from "$lib/state/app-version.svelte";
  import type { LayoutProps } from "./+layout";

  const { children } = $props();

  let data = $state<LayoutProps>({ title: "Sandbox" });
  let version = $derived(`v${appVersion.version}`);

  setContext("data", data);
  fetchAppVersion();
</script>

<header
  class="flex flex-row items-center gap-2 p-2 bg-surface-50-950 border-b border-surface-200-800"
>
  <button
    class="btn hover:preset-tonal aspect-square p-2 rounded-full"
    onclick={() => history.back()}
  >
    <ChevronLeft />
  </button>
  <h4 class="h4">{data.title}</h4>
  <div class="flex-1"></div>
  <LanguageSwitcher />
  <ThemeSwitch />
</header>

<main class="flex-1 bg-surface-100-900/25 overflow-y-auto">
  {@render children()}
</main>

<footer
  class="flex flex-row items-center justify-center gap-2 p-1 bg-surface-50-950 border-t border-surface-200-800"
>
  <p class="text-sm italic text-surface-700-300">
    <!-- &copy; {new Date().getFullYear()} VentureCodable - All rights reserved -->
    {version}
  </p>
</footer>
