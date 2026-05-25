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

  let { class: classname = "" } = $props();

  const MIN_PYTHON_VERSION = "3.11";

  let pythonFound: boolean | undefined = $state(undefined);
  let pythonVersion = $state("");
  let gitFound: boolean | undefined = $state(undefined);
  let pipxFound: boolean | undefined = $state(undefined);
  let paceRepoPath: string = $state("/home/cam/Documents/Development/PACE");
  let paceInstallResult: string = $state("");
  let paceHelpResult: string = $state("");

  async function checkPython() {
    pythonFound = await isPythonInstalled(MIN_PYTHON_VERSION);
    pythonVersion = await getPythonVersion();
  }

  async function checkGit() {
    gitFound = await isGitInstalled();
  }

  async function checkPipx() {
    pipxFound = await isPipxInstalled();
  }

  async function installPACE() {
    paceInstallResult = await installPace(paceRepoPath);
  }

  async function runPACEHelp() {
    try {
      let helpResult = await Command.create("pace", ["--help"]).execute();
      console.log(helpResult);
      paceHelpResult = helpResult.stdout;
    } catch (error) {
      paceHelpResult = error as string;
    }
  }

  onMount(async () => {
    await checkPython();
    await checkGit();
    await checkPipx();
  });
</script>

<div class="flex flex-col border rounded-md border-surface-500 p-2 {classname}">
  <button
    class="btn preset-filled-primary-500 text-xs self-center"
    onclick={checkPython}
  >
    Check if Python is installed
  </button>
  {#if pythonFound}
    <p>Python is installed</p>
    <p>
      Version: {pythonVersion}
      <img src="/python.svg" alt="Python logo" class="inline-block h-4 w-4" />
    </p>
    <button
      class="btn preset-filled-primary-500 text-xs self-center"
      onclick={checkGit}
    >
      Check if Git is installed
    </button>
    {#if gitFound}
      <p>Git is installed</p>
      <button
        class="btn preset-filled-primary-500 text-xs self-center"
        onclick={checkPipx}
      >
        Check if Pipx is installed
      </button>
      {#if pipxFound}
        <p>Pipx is installed</p>
        <input
          type="text"
          placeholder="PACE repository path"
          bind:value={paceRepoPath}
        />
        <button
          class="btn preset-filled-primary-500 text-xs self-center"
          onclick={installPACE}
        >
          Install PACE <img
            src="/appglyph.svg"
            alt="PACE logo"
            class="inline-block h-4 w-4"
          />
        </button>

        <button
          class="btn preset-filled-primary-500 text-xs self-center"
          onclick={runPACEHelp}
        >
          Run PACE --help
        </button>
        {#if paceInstallResult}
          <p>{paceInstallResult}</p>
        {/if}
        {#if paceHelpResult}
          <pre class="whitespace-pre-wrap text-xs">{paceHelpResult}</pre>
        {/if}
      {:else if pipxFound === false}
        <p>Pipx is not installed or cannot be accessed</p>
      {/if}
    {:else if gitFound === false}
      <p>Git is not installed or cannot be accessed</p>
    {/if}
  {:else if pythonFound === false}
    <p>Python is not installed or cannot be accessed</p>
  {/if}
</div>
