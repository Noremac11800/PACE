<script lang="ts">
  import { goto } from "$app/navigation";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";
  import { Bug } from "@lucide/svelte";
  import DepChecks from "./DepChecks.svelte";

  const version = "v0.1.0-alpha.1";
</script>

<main class="h-full grid grid-rows-[auto_1fr_auto]">
  <header class="relative flex flex-row justify-between items-center px-4 py-2">
    <ThemeSwitch />
  </header>

  <div
    class="relative min-h-0 bg-surface-100-900/25 flex items-start justify-center p-4 overflow-auto"
  >
    <DepChecks class="min-w-[300px] max-w-[500px] w-full py-4" />
  </div>

  <footer
    class="flex items-center justify-between bg-surface-50-950 px-2 py-1 border-t border-surface-200-800"
  >
    <button
      class="btn preset-filled-primary-500 text-xs"
      onclick={() => goto("/sandbox")}
    >
      <Bug size={16} />
      Go to sandbox
    </button>
    <p class="text-end">
      {version}
    </p>
  </footer>
</main>
