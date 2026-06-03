<script lang="ts">
  import { tick, onMount, untrack } from "svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import {
    Globe,
    Hammer,
    Square,
    ChevronDown,
    Terminal,
    Apple,
    Monitor,
    Smartphone,
    RotateCcw,
    Folder,
  } from "@lucide/svelte";
  import { BaseDirectory, readTextFile } from "@tauri-apps/plugin-fs";
  import { homeDir, join } from "@tauri-apps/api/path";
  import {
    settings,
    DEFAULT_PUBLISH_TAB_SETTINGS,
    type PublishTabSettings,
  } from "$lib/settings.svelte";
  import { saveSettings } from "$lib/app-init";
  import { configStore } from "$lib/config-store.svelte";

  const PLATFORMS = [
    { id: "ios" as const, label: "iOS", icon: Apple },
    { id: "android" as const, label: "Android", icon: Smartphone },
    { id: "windows" as const, label: "Windows", icon: Monitor },
  ];

  type Platform = (typeof PLATFORMS)[number]["id"];

  // Load settings
  let selectedProject = $state(settings.publishTab.selectedProject);
  let selectedPlatforms = $state<Platform[]>([
    ...settings.publishTab.selectedPlatforms,
  ]);
  let buildConfig = $state<"Debug" | "Release">(
    settings.publishTab.buildConfig,
  );
  let iosBundleId = $state(settings.publishTab.iosBundleId);
  let windowsKey = $state(settings.publishTab.windowsKey);
  let androidKey = $state(settings.publishTab.androidKey);

  let settingsInitialized = $state(false);

  // Derived projects list from active config
  const projects = $derived(configStore.activeConfig?.projects ?? []);

  // Codesigning config from file
  type CodesigningData = {
    ios: Record<string, { CodesignKey: string; CodesignProvision: string }>;
    windows: Record<string, { PackageCertificateThumbprint: string }>;
    android: Record<
      string,
      { KeystorePath: string; CodesignInfoTxtPath: string }
    >;
  };

  let codesigningConfig = $state<CodesigningData>({
    ios: { "*": { CodesignKey: "", CodesignProvision: "" } },
    windows: { "*": { PackageCertificateThumbprint: "" } },
    android: { "*": { KeystorePath: "", CodesignInfoTxtPath: "" } },
  });

  onMount(async () => {
    await loadCodesigningConfig();
    settingsInitialized = true;
  });

  async function loadCodesigningConfig() {
    try {
      const home = await homeDir();
      const content = await readTextFile(".pace/codesigning.json", {
        baseDir: BaseDirectory.Home,
      });
      const parsed = JSON.parse(content) as CodesigningData;
      codesigningConfig = parsed;
    } catch (e) {
      // Use default config if file doesn't exist or is invalid
      console.log("No codesigning config found, using defaults");
    }
  }

  // Derived lists for dropdowns
  const iosBundleIds = $derived(Object.keys(codesigningConfig.ios));
  const windowsKeys = $derived(Object.keys(codesigningConfig.windows));
  const androidKeys = $derived(Object.keys(codesigningConfig.android));

  // Save settings on change
  $effect(() => {
    if (!settingsInitialized) return;
    const snapshot: PublishTabSettings = {
      selectedProject,
      selectedPlatforms: [...selectedPlatforms],
      buildConfig,
      iosBundleId,
      windowsKey,
      androidKey,
    };
    untrack(() => {
      settings.publishTab = snapshot;
      saveSettings().catch((e) =>
        console.error("Failed to save publish settings:", e),
      );
    });
  });

  function togglePlatform(platform: Platform) {
    if (selectedPlatforms.includes(platform)) {
      selectedPlatforms = selectedPlatforms.filter((p) => p !== platform);
    } else {
      selectedPlatforms = [...selectedPlatforms, platform];
    }
  }

  function resetToDefaults() {
    const d = DEFAULT_PUBLISH_TAB_SETTINGS;
    selectedProject = d.selectedProject;
    selectedPlatforms = [...d.selectedPlatforms];
    buildConfig = d.buildConfig;
    iosBundleId = d.iosBundleId;
    windowsKey = d.windowsKey;
    androidKey = d.androidKey;
  }

  // Build execution state
  let isRunning = $state(false);
  let currentPlatformIndex = $state(0);
  let progress = $state(0);
  let progressLabel = $state("");
  let outputLines = $state<{ text: string; type: "out" | "err" }[]>([]);
  let currentProcess: Awaited<
    ReturnType<ReturnType<typeof Command.create>["spawn"]>
  > | null = null;
  let outputRef: HTMLDivElement | undefined;
  let elapsedSeconds = $state(0);
  let timerInterval: ReturnType<typeof setInterval> | null = null;

  const platformOrder: Platform[] = ["ios", "android", "windows"];

  const orderedSelectedPlatforms = $derived(
    platformOrder.filter((p) => selectedPlatforms.includes(p)),
  );

  function startTimer() {
    elapsedSeconds = 0;
    timerInterval = setInterval(() => {
      elapsedSeconds += 1;
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function formatElapsed(s: number): string {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec.toString().padStart(2, "0")}s` : `${sec}s`;
  }

  function addLine(text: string, type: "out" | "err") {
    outputLines = [...outputLines, { text, type }];
    tick().then(() => {
      if (outputRef) outputRef.scrollTop = outputRef.scrollHeight;
    });
  }

  function resetOutput() {
    outputLines = [];
    progress = 0;
    progressLabel = "";
    currentPlatformIndex = 0;
  }

  function getRuntimeForPlatform(platform: Platform): string {
    switch (platform) {
      case "ios":
        return "ios-arm64";
      case "android":
        return "android-arm64";
      case "windows":
        return "win10-x64";
      default:
        return "";
    }
  }

  function getCodesigningParams(platform: Platform): string[] {
    const params: string[] = [];
    switch (platform) {
      case "ios":
        if (iosBundleId) {
          const config = codesigningConfig.ios[iosBundleId];
          if (config?.CodesignKey) {
            params.push(`/p:CodesignKey="${config.CodesignKey}"`);
          }
          if (config?.CodesignProvision) {
            params.push(`/p:CodesignProvision=${config.CodesignProvision}`);
          }
        }
        break;
      case "android":
        if (androidKey) {
          const config = codesigningConfig.android[androidKey];
          if (config?.KeystorePath) {
            params.push(`/p:AndroidKeyStore=${config.KeystorePath}`);
          }
        }
        break;
      case "windows":
        if (windowsKey) {
          const config = codesigningConfig.windows[windowsKey];
          if (config?.PackageCertificateThumbprint) {
            params.push(
              `/p:PackageCertificateThumbprint=${config.PackageCertificateThumbprint}`,
            );
          }
        }
        break;
    }
    return params;
  }

  function getFrameworkForPlatform(platform: Platform): string {
    switch (platform) {
      case "ios":
        return "net10.0-ios";
      case "android":
        return "net10.0-android";
      case "windows":
        return "net10.0-windows10.0.20348.0";
      default:
        return "";
    }
  }

  async function runBuildForPlatform(platform: Platform): Promise<boolean> {
    const project = projects.find((p) => p.name === selectedProject);
    if (!project?.csproj_path) {
      addLine(
        "Error: No project selected or project has no csproj_path",
        "err",
      );
      return false;
    }

    const repodir = configStore.activeConfig?.repodir;
    if (!repodir) {
      addLine("Error: No repodir configured in active config", "err");
      return false;
    }

    // Build absolute path to csproj: {repodir}/{project.name}/{project.csproj_path}
    const csprojPath = `${repodir}/${project.name}/${project.csproj_path}`;

    const framework = getFrameworkForPlatform(platform);
    const runtime = getRuntimeForPlatform(platform);

    // Build dotnet publish command
    const publishArgs: string[] = [
      "publish",
      csprojPath,
      "-c",
      buildConfig,
      "--runtime",
      runtime,
      "--framework",
      framework,
      "--self-contained",
      "/p:DistributionMethod=enterprise",
      "/p:DevSolution=" + (buildConfig === "Debug" ? "true" : "false"),
      "/p:ArchiveOnBuild=true",
    ];

    // Add platform-specific codesigning params
    const codesigningParams = getCodesigningParams(platform);
    publishArgs.push(...codesigningParams);

    return new Promise((resolve) => {
      progressLabel = `Publishing ${platform}...`;

      try {
        const cmd = Command.create("dotnet", publishArgs);

        cmd.stdout.on("data", (data: string) => {
          addLine(data, "out");
        });

        cmd.stderr.on("data", (data: string) => {
          addLine(data, "err");
        });

        cmd.on("close", (payload: { code: number | null }) => {
          resolve(payload.code === 0);
        });

        cmd.spawn().then((child) => {
          currentProcess = child;
        });
      } catch (e) {
        addLine(`Error: ${e instanceof Error ? e.message : String(e)}`, "err");
        resolve(false);
      }
    });
  }

  async function runPublish() {
    if (isRunning || !selectedProject || selectedPlatforms.length === 0) return;

    resetOutput();
    startTimer();
    isRunning = true;
    currentPlatformIndex = 0;
    progress = 0;

    try {
      for (let i = 0; i < orderedSelectedPlatforms.length; i++) {
        currentPlatformIndex = i;
        const platform = orderedSelectedPlatforms[i];
        const platformProgress = Math.round(
          (i / orderedSelectedPlatforms.length) * 100,
        );
        progress = platformProgress;

        addLine(
          `\n========== Starting build for ${platform} ==========\n`,
          "out",
        );

        const success = await runBuildForPlatform(platform);

        if (!success) {
          addLine(
            `\n========== Build failed for ${platform} ==========\n`,
            "err",
          );
          progressLabel = `Build failed for ${platform}`;
          progress = 100;
          break;
        }

        addLine(
          `\n========== Build completed for ${platform} ==========\n`,
          "out",
        );
      }

      if (currentPlatformIndex === orderedSelectedPlatforms.length - 1) {
        progress = 100;
        progressLabel = "All builds completed successfully";
      }
    } catch (e) {
      addLine(`Error: ${e instanceof Error ? e.message : String(e)}`, "err");
      progressLabel = "Error";
      progress = 100;
    } finally {
      stopTimer();
      isRunning = false;
      currentProcess = null;
    }
  }

  function cancelBuild() {
    currentProcess?.kill();
    stopTimer();
    addLine("Build cancelled by user.", "err");
    progressLabel = "Cancelled";
    progress = 100;
    isRunning = false;
    currentProcess = null;
  }

  const commandPreview = $derived.by(() => {
    if (!selectedProject) return "Select a project to see preview";
    if (selectedPlatforms.length === 0)
      return "Select platforms to see preview";
    const project = projects.find((p) => p.name === selectedProject);
    const repodir = configStore.activeConfig?.repodir ?? "<repodir>";
    const csprojPath = project?.csproj_path
      ? `${repodir}/${project.name}/${project.csproj_path}`
      : "<csproj_path>";

    if (selectedPlatforms.length === 1) {
      const platform = selectedPlatforms[0];
      const framework = getFrameworkForPlatform(platform);
      const runtime = getRuntimeForPlatform(platform);

      let preview = `dotnet publish ${csprojPath} -c ${buildConfig} --runtime ${runtime} --framework ${framework} --self-contained /p:DistributionMethod=enterprise /p:DevSolution=${buildConfig === "Debug" ? "true" : "false"} /p:ArchiveOnBuild=true`;

      // Add codesigning preview for selected platform
      if (platform === "ios" && iosBundleId) {
        const config = codesigningConfig.ios[iosBundleId];
        if (config?.CodesignKey) {
          preview += ` /p:CodesignKey="${config.CodesignKey}"`;
        }
        if (config?.CodesignProvision) {
          preview += ` /p:CodesignProvision=${config.CodesignProvision}`;
        }
      }

      return preview;
    } else {
      return `dotnet publish ${csprojPath} -c ${buildConfig} (multiple platforms: ${selectedPlatforms.join(", ")})`;
    }
  });

  const progressBarColor = $derived.by(() => {
    if (/failed|cancelled|error/i.test(progressLabel)) return "bg-error-500";
    if (/completed|succeeded/i.test(progressLabel)) return "bg-success-500";
    return "bg-primary-500";
  });
</script>

<div class="h-full flex flex-col">
  <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
    <!-- Project Selection -->
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <Folder size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100">Project</span>
      </div>

      {#if projects.length === 0}
        <div class="text-sm text-surface-500-400">
          No projects available. Load a config with projects first.
        </div>
      {:else}
        <div class="flex flex-col gap-1">
          <span class="text-xs font-medium text-surface-600-400"
            >Select Project</span
          >
          <div class="relative">
            <select
              bind:value={selectedProject}
              class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-2 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
              style="background-image:none"
            >
              <option value="">— Select a project —</option>
              {#each projects as project}
                <option value={project.name}>{project.name}</option>
              {/each}
            </select>
            <ChevronDown
              size={14}
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
            />
          </div>
        </div>
      {/if}
    </div>

    <!-- Platform Selection -->
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <Globe size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100">Target Platforms</span>
      </div>

      <div class="flex flex-wrap gap-2">
        {#each PLATFORMS as platform}
          {@const Icon = platform.icon}
          {@const isSelected = selectedPlatforms.includes(platform.id)}
          <button
            type="button"
            onclick={() => togglePlatform(platform.id)}
            class="flex items-center gap-2 px-4 py-2 rounded text-sm font-medium border transition-colors {isSelected
              ? 'bg-primary-500 border-primary-500 text-white'
              : 'bg-surface-100-900 border-surface-300-700 text-surface-700-300 hover:border-primary-500 hover:text-primary-500'}"
          >
            <Icon size={16} />
            {platform.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- Build Configuration -->
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <Hammer size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100"
          >Build Configuration</span
        >
      </div>

      <div class="flex flex-col gap-1">
        <span class="text-xs font-medium text-surface-600-400"
          >Configuration</span
        >
        <div class="flex flex-wrap gap-2">
          {#each ["Debug", "Release"] as const as cfg}
            <button
              type="button"
              onclick={() => (buildConfig = cfg)}
              class="px-3 py-1.5 rounded text-xs font-medium border transition-colors {buildConfig ===
              cfg
                ? 'bg-primary-500 border-primary-500 text-white'
                : 'bg-surface-100-900 border-surface-300-700 text-surface-700-300 hover:border-primary-500 hover:text-primary-500'}"
            >
              {cfg}
            </button>
          {/each}
        </div>
      </div>
    </div>

    <!-- Codesigning Configuration -->
    {#if selectedPlatforms.length > 0}
      <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
        <div class="flex items-center gap-2">
          <span class="font-semibold text-surface-900-100"
            >Codesigning Configuration</span
          >
        </div>

        {#if selectedPlatforms.includes("ios")}
          <div class="flex flex-col gap-1">
            <label
              class="text-xs font-medium text-surface-600-400"
              for="ios-bundle"
            >
              iOS Bundle ID
            </label>
            <div class="relative">
              <select
                id="ios-bundle"
                bind:value={iosBundleId}
                class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-2 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
                style="background-image:none"
              >
                <option value="*">— Default (*) —</option>
                {#each iosBundleIds.filter((id) => id !== "*") as bundleId}
                  <option value={bundleId}>{bundleId}</option>
                {/each}
              </select>
              <ChevronDown
                size={14}
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
              />
            </div>
          </div>
        {/if}

        {#if selectedPlatforms.includes("windows")}
          <div class="flex flex-col gap-1">
            <label
              class="text-xs font-medium text-surface-600-400"
              for="windows-cert"
            >
              Windows Certificate
            </label>
            <div class="relative">
              <select
                id="windows-cert"
                bind:value={windowsKey}
                class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-2 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
                style="background-image:none"
              >
                <option value="*">— Default (*) —</option>
                {#each windowsKeys.filter((k) => k !== "*") as key}
                  <option value={key}>{key}</option>
                {/each}
              </select>
              <ChevronDown
                size={14}
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
              />
            </div>
          </div>
        {/if}

        {#if selectedPlatforms.includes("android")}
          <div class="flex flex-col gap-1">
            <label
              class="text-xs font-medium text-surface-600-400"
              for="android-keystore"
            >
              Android Keystore
            </label>
            <div class="relative">
              <select
                id="android-keystore"
                bind:value={androidKey}
                class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-2 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
                style="background-image:none"
              >
                <option value="*">— Default (*) —</option>
                {#each androidKeys.filter((k) => k !== "*") as key}
                  <option value={key}>{key}</option>
                {/each}
              </select>
              <ChevronDown
                size={14}
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
              />
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Command Preview -->
    {#if selectedPlatforms.length > 0}
      <div class="card bg-surface-50-950 p-4">
        <div class="flex items-center gap-2 mb-2">
          <Terminal size={16} class="text-primary-500 shrink-0" />
          <span
            class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
          >
            Command Preview
          </span>
        </div>
        <code
          class="block text-sm font-mono bg-surface-200-800 px-3 py-2 rounded break-all text-surface-900-100"
        >
          {commandPreview}
        </code>
      </div>
    {/if}

    <!-- Progress -->
    {#if isRunning || progress > 0}
      <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
        <div class="flex items-center justify-between gap-2 text-xs">
          <span class="text-surface-600-400 truncate">{progressLabel}</span>
          <span
            class="font-mono text-surface-600-400 shrink-0 flex items-center gap-2"
          >
            {#if orderedSelectedPlatforms.length > 1 && isRunning}
              <span
                >Platform {currentPlatformIndex + 1} / {orderedSelectedPlatforms.length}</span
              >
              <span class="text-surface-400-500">·</span>
            {/if}
            <span>{progress}%</span>
            <span class="text-surface-400-500">·</span>
            <span>{formatElapsed(elapsedSeconds)}</span>
          </span>
        </div>

        <div class="w-full h-2 bg-surface-200-800 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-300 {progressBarColor}"
            style="width: {progress}%"
          ></div>
        </div>

        <!-- Platform segment strip -->
        {#if orderedSelectedPlatforms.length > 1}
          <div class="flex gap-0.5">
            {#each orderedSelectedPlatforms as platform, i}
              <div
                class="h-1.5 flex-1 rounded-full transition-colors duration-200 {i <
                currentPlatformIndex
                  ? progressBarColor
                  : i === currentPlatformIndex && isRunning
                    ? progressBarColor
                    : 'bg-surface-200-800'}"
              ></div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Output log -->
    {#if outputLines.length > 0}
      <div class="card bg-surface-50-950 p-4 flex flex-col gap-2">
        <span
          class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
          >Output</span
        >
        <div
          bind:this={outputRef}
          class="h-60 overflow-auto bg-surface-200-800 rounded p-3 font-mono text-xs leading-relaxed"
        >
          {#each outputLines as line}
            <div
              class="{line.type === 'err'
                ? 'text-error-400'
                : 'text-surface-900-100'} wrap-break-word"
            >
              {line.text}
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>

  <!-- Sticky footer -->
  <div
    class="shrink-0 flex items-center gap-3 px-4 py-3 border-t border-surface-200-800 bg-surface-50-950"
  >
    {#if isRunning}
      <button
        class="btn preset-filled-error-500 flex items-center gap-2"
        onclick={cancelBuild}
      >
        <Square size={16} />
        Cancel Publish
      </button>
    {:else}
      <button
        class="btn preset-filled-primary-500 flex items-center gap-2"
        onclick={runPublish}
        disabled={!selectedProject || selectedPlatforms.length === 0}
      >
        <Globe size={16} />
        Publish
      </button>
    {/if}
    <button
      class="btn preset-tonal flex items-center gap-2"
      onclick={resetToDefaults}
      disabled={isRunning}
      title="Reset all publish settings to defaults"
    >
      <RotateCcw size={16} />
      Reset to defaults
    </button>
  </div>
</div>
