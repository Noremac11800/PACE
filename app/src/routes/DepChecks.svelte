<script lang="ts">
  import {
    isPythonInstalled,
    getPythonVersion,
    isGitInstalled,
    isPipxInstalled,
    installPace,
  } from "$lib/dependency_utils";
  import { Command } from "@tauri-apps/plugin-shell";
  import { open } from "@tauri-apps/plugin-dialog";
  import { onMount } from "svelte";
  import {
    Check,
    X,
    Loader,
    RefreshCw,
    Folder,
    Package,
    Github,
    Play,
    Settings,
    Tag,
    Trash2,
  } from "@lucide/svelte";

  let { class: classname = "" } = $props();

  const MIN_PYTHON_VERSION = "3.11";
  const EXEC_DELAY = 250;

  let pythonFound: boolean | undefined = $state(undefined);
  let pythonVersion = $state("");
  let gitFound: boolean | undefined = $state(undefined);
  let pipxFound: boolean | undefined = $state(undefined);
  let pipxVersion = $state("");
  let paceRepoPath: string = $state("/home/cam/Documents/Development/PACE");
  let paceInstallResult: string = $state("");
  let paceHelpResult: string = $state("");
  let paceUninstallResult: string = $state("");
  let isInstalling = $state(false);
  let isRunningHelp = $state(false);
  let isUninstalling = $state(false);
  let isInstallingPipx = $state(false);
  let isCheckingPace = $state(false);
  let pipxInstallResult: string = $state("");
  let paceInstalled: boolean | undefined = $state(undefined);
  let paceVersion = $state("");

  const sleep = (ms: number) =>
    new Promise((resolve) => setTimeout(resolve, ms));

  async function checkPython() {
    pythonFound = undefined;
    await sleep(EXEC_DELAY);
    pythonFound = await isPythonInstalled(MIN_PYTHON_VERSION);
    pythonVersion = await getPythonVersion();
  }

  async function checkGit() {
    gitFound = undefined;
    await sleep(EXEC_DELAY);
    gitFound = await isGitInstalled();
  }

  async function checkPipx() {
    pipxFound = undefined;
    pipxVersion = "";
    await sleep(EXEC_DELAY);
    pipxFound = await isPipxInstalled();
    if (pipxFound) {
      try {
        let result = await Command.create("pipx", ["--version"]).execute();
        if (result.code === 0) {
          pipxVersion = result.stdout.trim();
        }
      } catch {
        // ignore version fetch errors
      }
    }
  }

  async function installPipx() {
    isInstallingPipx = true;
    pipxInstallResult = "";
    await sleep(EXEC_DELAY);
    try {
      let result = await Command.create("pip install pipx", [
        "-m",
        "pip",
        "install",
        "pipx",
      ]).execute();
      console.log(result);
      if (result.code === 0) {
        pipxInstallResult = "Pipx installed successfully. Ensuring PATH...";
        let ensurePathResult = await Command.create("pipx", [
          "ensurepath",
        ]).execute();
        pipxInstallResult =
          ensurePathResult.code === 0
            ? "Pipx installed and PATH updated."
            : `Pipx installed but PATH update failed: ${ensurePathResult.stderr}`;
      } else {
        pipxInstallResult = result.stderr;
      }
      await checkPipx();
    } catch (error) {
      pipxInstallResult = error as string;
    } finally {
      isInstallingPipx = false;
      await checkAll();
    }
  }

  async function checkPace() {
    isCheckingPace = true;
    paceVersion = "";
    await sleep(EXEC_DELAY);
    try {
      let result = await Command.create("pace", ["--version"]).execute();
      paceInstalled = result.code === 0;
      if (paceInstalled) {
        paceVersion = result.stdout.trim();
      }
    } catch {
      paceInstalled = false;
    } finally {
      isCheckingPace = false;
    }
  }

  async function installPACE() {
    isInstalling = true;
    await sleep(EXEC_DELAY);
    paceInstallResult = await installPace(paceRepoPath);
    isInstalling = false;
    await checkPace();
  }

  async function uninstallPACE() {
    isUninstalling = true;
    paceUninstallResult = "";
    await sleep(EXEC_DELAY);
    try {
      let result = await Command.create("pipx", [
        "uninstall",
        "pace",
      ]).execute();
      paceUninstallResult =
        result.code === 0 ? "PACE uninstalled successfully" : result.stderr;
      await checkPace();
    } catch (error) {
      paceUninstallResult = error as string;
    } finally {
      isUninstalling = false;
    }
  }

  async function runPACEHelp() {
    try {
      isRunningHelp = true;
      await sleep(EXEC_DELAY);
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
    pythonVersion = "";
    gitFound = undefined;
    pipxFound = undefined;
    pipxVersion = "";
    paceInstalled = undefined;
    paceVersion = "";
    paceHelpResult = "";
    paceInstallResult = "";
    paceUninstallResult = "";
    pipxInstallResult = "";

    await checkPython();
    await checkGit();
    await checkPipx();
    if (pythonFound && gitFound && pipxFound) {
      await checkPace();
    }
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
            <Check size={16} />
            Ready
          </span>
        {:else}
          <span class="chip preset-filled-error-500 flex items-center gap-1">
            <X size={16} />
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
            <Check size={16} />
            Ready
          </span>
        {:else}
          <span class="chip preset-filled-error-500 flex items-center gap-1">
            <X size={16} />
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
              v{pipxVersion || "Installed"}
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
            <Check size={16} />
            Ready
          </span>
        {:else}
          <div class="flex items-center gap-2">
            <span class="chip preset-filled-error-500 flex items-center gap-1">
              <X size={16} />
              Missing
            </span>
            {#if pythonFound}
              <button
                class="btn preset-filled-secondary-500 text-xs flex items-center gap-1 px-2 py-1"
                onclick={installPipx}
                disabled={isInstallingPipx}
              >
                {#if isInstallingPipx}
                  <Loader size={14} class="animate-spin" />
                  Installing...
                {:else}
                  <Package size={14} />
                  Install
                {/if}
              </button>
            {/if}
          </div>
        {/if}
      </div>
    </div>
    {#if pipxInstallResult && pipxFound === false}
      <div class="mt-2 p-2 bg-surface-100-900 rounded text-xs">
        <pre
          class="text-surface-700-300 whitespace-pre-wrap">{pipxInstallResult}</pre>
      </div>
    {/if}
  </div>

  <!-- PACE Installation Card -->
  {#if pythonFound && gitFound && pipxFound}
    <div class="card bg-surface-50-950 shadow-md p-4">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h4 class="h4 text-primary-500 flex items-center gap-2">
            <img src="/appicon.svg" alt="PACE" class="h-5 w-5" />
            PACE Installation
          </h4>
          {#if paceInstalled && paceVersion}
            <p class="text-xs text-surface-700-300 flex items-center gap-1">
              <Tag size={12} />
              v{paceVersion.replace(/^pace\s*/, "")}
            </p>
          {/if}
        </div>
        {#if paceInstalled !== undefined}
          {#if paceInstalled}
            <span
              class="chip preset-filled-success-500 flex items-center gap-1"
            >
              <Check size={14} />
              Installed
            </span>
          {:else}
            <span class="chip preset-filled-error-500 flex items-center gap-1">
              <X size={14} />
              Not Installed
            </span>
          {/if}
        {:else if isCheckingPace}
          <Loader size={18} class="animate-spin text-surface-500" />
        {/if}
      </div>

      <!-- Repository Path Input -->
      <label
        for="pace-repo-path"
        class="block text-sm text-surface-700-300 mb-1"
      >
        Path to PACE repository root
      </label>
      <div class="input-group grid grid-cols-[auto_1fr] mb-4">
        <button
          class="ig-cell preset-tonal cursor-pointer"
          onclick={async () => {
            const selected = await open({ directory: true });
            if (selected) {
              paceRepoPath = selected as string;
            }
          }}
          title="Select directory"
        >
          <Folder size={18} />
        </button>
        <input
          id="pace-repo-path"
          class="ig-input"
          type="text"
          placeholder="PACE repository path"
          bind:value={paceRepoPath}
        />
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap gap-2">
        {#if paceInstalled === false}
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
        {:else if paceInstalled}
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

          <button
            class="btn preset-filled-error-500 flex items-center gap-2"
            onclick={uninstallPACE}
            disabled={isUninstalling}
          >
            {#if isUninstalling}
              <Loader size={16} class="animate-spin" />
              Uninstalling...
            {:else}
              <Trash2 size={16} />
              Uninstall
            {/if}
          </button>
        {/if}
      </div>

      <!-- Results -->
      {#if paceInstallResult}
        <div class="mt-4 p-3 bg-surface-100-900 rounded text-sm">
          <p class="text-surface-700-300 mb-1">Installation Result:</p>
          <p class="font-mono">{paceInstallResult}</p>
        </div>
      {/if}

      {#if paceUninstallResult}
        <div class="mt-4 p-3 bg-surface-100-900 rounded text-sm">
          <p class="text-surface-700-300 mb-1">Uninstall Result:</p>
          <p class="font-mono">{paceUninstallResult}</p>
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
