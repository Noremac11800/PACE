<script lang="ts">
  import {
    isPythonInstalled,
    getPythonVersion,
    isGitInstalled,
    isPipxInstalled,
    installPace,
  } from "$lib/dependency_utils";
  import { Command } from "@tauri-apps/plugin-shell";
  import { onMount } from "svelte";
  import {
    Check,
    X,
    Loader,
    RefreshCw,
    Terminal,
    Package,
    Github,
    Play,
    Settings,
  } from "@lucide/svelte";

  let { class: classname = "" } = $props();

  const MIN_PYTHON_VERSION = "3.11";

  let pythonFound: boolean | undefined = $state(undefined);
  let pythonVersion = $state("");
  let gitFound: boolean | undefined = $state(undefined);
  let pipxFound: boolean | undefined = $state(undefined);
  let paceRepoPath: string = $state("/home/cam/Documents/Development/PACE");
  let paceInstallResult: string = $state("");
  let paceHelpResult: string = $state("");
  let isInstalling = $state(false);
  let isRunningHelp = $state(false);

  const sleep = (ms: number) =>
    new Promise((resolve) => setTimeout(resolve, ms));

  async function checkPython() {
    pythonFound = undefined;
    await sleep(1000);
    pythonFound = await isPythonInstalled(MIN_PYTHON_VERSION);
    pythonVersion = await getPythonVersion();
  }

  async function checkGit() {
    gitFound = undefined;
    await sleep(1000);
    gitFound = await isGitInstalled();
  }

  async function checkPipx() {
    pipxFound = undefined;
    await sleep(1000);
    pipxFound = await isPipxInstalled();
  }

  async function installPACE() {
    isInstalling = true;
    await sleep(1000);
    paceInstallResult = await installPace(paceRepoPath);
    isInstalling = false;
  }

  async function runPACEHelp() {
    try {
      isRunningHelp = true;
      await sleep(1000);
      let helpResult = await Command.create("pace", ["--help"]).execute();
      paceHelpResult = helpResult.stdout;
    } catch (error) {
      paceHelpResult = error as string;
    } finally {
      isRunningHelp = false;
    }
  }

  async function checkAll() {
    pythonFound = undefined;
    gitFound = undefined;
    pipxFound = undefined;
    await checkPython();
    await checkGit();
    await checkPipx();
  }

  onMount(async () => {
    await checkAll();
  });
</script>

<div class="flex flex-col gap-4 {classname}">
  <!-- Dependency Status Card -->
  <div class="card bg-surface-50-950 shadow-md p-4">
    <div class="flex items-center justify-between mb-4">
      <h4 class="h4 text-primary-500 flex items-center gap-2">
        <Settings size={20} />
        Dependencies
      </h4>
      <button
        class="btn preset-tonal p-2"
        onclick={checkAll}
        title="Refresh all checks"
      >
        <RefreshCw size={16} />
      </button>
    </div>

    <!-- Python Status -->
    <div
      class="flex items-center justify-between py-2 border-b border-surface-200-800"
    >
      <div class="flex items-center gap-3">
        <div class="ig-cell preset-tonal p-2 rounded">
          <img src="/python.svg" alt="Python" class="h-5 w-5" />
        </div>
        <div>
          <p class="font-medium">Python</p>
          <p class="text-xs text-surface-700-300">
            {#if pythonFound === undefined}
              Checking...
            {:else if pythonFound}
              v{pythonVersion}
            {:else}
              Not installed or &lt; {MIN_PYTHON_VERSION}
            {/if}
          </p>
        </div>
      </div>
      <div>
        {#if pythonFound === undefined}
          <Loader size={20} class="animate-spin text-surface-500" />
        {:else if pythonFound}
          <span class="chip preset-filled-success-500 flex items-center gap-1">
            <Check size={12} />
            Ready
          </span>
        {:else}
          <span class="chip preset-filled-error-500 flex items-center gap-1">
            <X size={12} />
            Missing
          </span>
        {/if}
      </div>
    </div>

    <!-- Git Status -->
    <div
      class="flex items-center justify-between py-2 border-b border-surface-200-800"
    >
      <div class="flex items-center gap-3">
        <div class="ig-cell preset-tonal p-2 rounded">
          <Github size={20} />
        </div>
        <div>
          <p class="font-medium">Git</p>
          <p class="text-xs text-surface-700-300">
            {#if gitFound === undefined}
              Checking...
            {:else if gitFound}
              Installed
            {:else}
              Not installed
            {/if}
          </p>
        </div>
      </div>
      <div>
        {#if gitFound === undefined}
          <Loader size={20} class="animate-spin text-surface-500" />
        {:else if gitFound}
          <span class="chip preset-filled-success-500 flex items-center gap-1">
            <Check size={12} />
            Ready
          </span>
        {:else}
          <span class="chip preset-filled-error-500 flex items-center gap-1">
            <X size={12} />
            Missing
          </span>
        {/if}
      </div>
    </div>

    <!-- Pipx Status -->
    <div class="flex items-center justify-between py-2">
      <div class="flex items-center gap-3">
        <div class="ig-cell preset-tonal p-2 rounded">
          <Package size={20} />
        </div>
        <div>
          <p class="font-medium">Pipx</p>
          <p class="text-xs text-surface-700-300">
            {#if pipxFound === undefined}
              Checking...
            {:else if pipxFound}
              Installed
            {:else}
              Not installed
            {/if}
          </p>
        </div>
      </div>
      <div>
        {#if pipxFound === undefined}
          <Loader size={20} class="animate-spin text-surface-500" />
        {:else if pipxFound}
          <span class="chip preset-filled-success-500 flex items-center gap-1">
            <Check size={12} />
            Ready
          </span>
        {:else}
          <span class="chip preset-filled-error-500 flex items-center gap-1">
            <X size={12} />
            Missing
          </span>
        {/if}
      </div>
    </div>
  </div>

  <!-- PACE Installation Card -->
  {#if pythonFound && gitFound && pipxFound}
    <div class="card bg-surface-50-950 shadow-md p-4">
      <h4 class="h4 text-primary-500 flex items-center gap-2 mb-4">
        <img src="/appglyph.svg" alt="PACE" class="h-5 w-5" />
        PACE Installation
      </h4>

      <!-- Repository Path Input -->
      <div class="input-group grid grid-cols-[auto_1fr] mb-4">
        <div class="ig-cell preset-tonal">
          <Terminal size={18} />
        </div>
        <input
          class="ig-input"
          type="text"
          placeholder="PACE repository path"
          bind:value={paceRepoPath}
        />
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap gap-2">
        <button
          class="btn preset-filled-primary-500 flex items-center gap-2"
          onclick={installPACE}
          disabled={isInstalling}
        >
          {#if isInstalling}
            <Loader size={16} class="animate-spin" />
            Installing...
          {:else}
            <Package size={16} />
            Install PACE
          {/if}
        </button>

        <button
          class="btn preset-tonal flex items-center gap-2"
          onclick={runPACEHelp}
          disabled={isRunningHelp}
        >
          {#if isRunningHelp}
            <Loader size={16} class="animate-spin" />
            Running...
          {:else}
            <Play size={16} />
            Test PACE
          {/if}
        </button>
      </div>

      <!-- Results -->
      {#if paceInstallResult}
        <div class="mt-4 p-3 bg-surface-100-900 rounded text-sm">
          <p class="text-surface-700-300 mb-1">Installation Result:</p>
          <p class="font-mono">{paceInstallResult}</p>
        </div>
      {/if}

      {#if paceHelpResult}
        <div class="mt-4">
          <p class="text-xs text-surface-700-300 mb-1">PACE Help Output:</p>
          <pre
            class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-xs overflow-auto max-h-48">{paceHelpResult}</pre>
        </div>
      {/if}
    </div>
  {:else if pythonFound === false || gitFound === false || pipxFound === false}
    <div class="card bg-surface-50-950 shadow-md p-4">
      <div class="flex items-start gap-3">
        <div class="ig-cell preset-filled-error-500 p-2 rounded">
          <X size={20} />
        </div>
        <div>
          <h4 class="h4 text-error-500">Missing Dependencies</h4>
          <p class="text-sm text-surface-700-300 mt-1">
            Please install the missing dependencies above before proceeding with
            PACE installation.
          </p>
        </div>
      </div>
    </div>
  {/if}
</div>
