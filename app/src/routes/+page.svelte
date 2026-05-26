<script lang="ts">
  import { goto } from "$app/navigation";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";
  import {
    Bug,
    Home,
    Package,
    Settings,
    Terminal,
    CircleHelp,
  } from "@lucide/svelte";
  import DepChecks from "./DepChecks.svelte";

  const version = "v0.1.0-alpha.1";

  let activeView: "home" | "dependencies" | "console" | "about" =
    $state("dependencies");
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

  <!-- Sidebar -->
  <aside
    class="flex flex-col items-center gap-2 p-2 bg-surface-50-950 border-r border-surface-200-800"
  >
    <button
      class="btn {activeView === 'home'
        ? 'preset-filled-primary-500'
        : 'preset-tonal'} p-2"
      onclick={() => (activeView = "home")}
      title="Home"
    >
      <Home size={20} />
    </button>
    <button
      class="btn {activeView === 'dependencies'
        ? 'preset-filled-primary-500'
        : 'preset-tonal'} p-2"
      onclick={() => (activeView = "dependencies")}
      title="Dependencies"
    >
      <Package size={20} />
    </button>
    <button
      class="btn {activeView === 'console'
        ? 'preset-filled-primary-500'
        : 'preset-tonal'} p-2"
      onclick={() => (activeView = "console")}
      title="Console"
    >
      <Terminal size={20} />
    </button>
    <button
      class="btn {activeView === 'about'
        ? 'preset-filled-primary-500'
        : 'preset-tonal'} p-2"
      onclick={() => (activeView = "about")}
      title="About"
    >
      <CircleHelp size={20} />
    </button>
  </aside>

  <!-- Main Content -->
  <div class="relative min-h-0 bg-surface-100-900/25 overflow-auto p-4">
    {#if activeView === "home"}
      <div class="min-h-full flex items-center justify-center">
        <div class="card bg-surface-50-950 shadow-md p-8 text-center max-w-md">
          <img src="/appicon.svg" alt="PACE" class="h-16 w-16 mx-auto mb-4" />
          <h1 class="h1 text-primary-500 mb-2">Welcome to PACE</h1>
          <p class="text-surface-700-300 mb-4">
            Project Automation and Configuration Engine
          </p>
          <p class="text-sm text-surface-700-300">
            Use the sidebar to navigate between views.
          </p>
        </div>
      </div>
    {:else if activeView === "dependencies"}
      <div class="min-h-full flex items-center justify-center">
        <DepChecks class="min-w-[300px] max-w-[500px] w-full" />
      </div>
    {:else if activeView === "console"}
      <div class="min-h-full flex items-center justify-center">
        <div class="card bg-surface-50-950 shadow-md p-8 text-center max-w-md">
          <Terminal size={48} class="mx-auto mb-4 text-primary-500" />
          <h2 class="h2 text-primary-500 mb-2">Console</h2>
          <p class="text-surface-700-300">
            Command output and logs will appear here.
          </p>
        </div>
      </div>
    {:else if activeView === "about"}
      <div class="min-h-full flex items-center justify-center">
        <div class="card bg-surface-50-950 shadow-md p-8 text-center max-w-md">
          <img src="/appicon.svg" alt="PACE" class="h-16 w-16 mx-auto mb-4" />
          <h2 class="h2 text-primary-500 mb-2">About PACE</h2>
          <p class="text-surface-700-300 mb-2">Version {version}</p>
          <p class="text-sm text-surface-700-300">
            A project automation and configuration tool for managing
            multi-repository projects.
          </p>
        </div>
      </div>
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
    <p class="text-end">
      {version}
    </p>
  </footer>
</main>
