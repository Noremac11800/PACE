<script lang="ts">
  import { goto } from "$app/navigation";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";
  import { Bug } from "@lucide/svelte";
  import { View } from "./view-types";
  import Sidebar from "./Sidebar.svelte";
  import HomePanel from "./HomePanel.svelte";
  import DependenciesPanel from "./DependenciesPanel.svelte";
  import ConsolePanel from "./ConsolePanel.svelte";
  import AboutPanel from "./AboutPanel.svelte";

  let activeView: View = $state(View.HOME);
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
    <ThemeSwitch />
  </header>

  <Sidebar bind:activeView />

  <!-- Main Content -->
  <div class="relative min-h-0 bg-surface-100-900/25 overflow-auto">
    {#if activeView === View.HOME}
      <HomePanel />
    {:else if activeView === View.DEPENDENCIES}
      <DependenciesPanel />
    {:else if activeView === View.CONSOLE}
      <ConsolePanel />
    {:else if activeView === View.ABOUT}
      <AboutPanel />
    {/if}
  </div>

  <!-- Footer -->
  <footer
    class="col-span-2 flex items-center justify-between bg-surface-50-950 px-2 py-1 border-t border-surface-200-800"
  >
    <button
      class="btn preset-filled-primary-500 text-xs"
      onclick={() => goto("/sandbox")}
    >
      <Bug size={16} />
      Go to sandbox
    </button>
    <p class="text-end">v0.1.0-alpha.1</p>
  </footer>
</main>
