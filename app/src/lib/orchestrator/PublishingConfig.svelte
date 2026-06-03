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
    Check,
    X,
    Loader,
  } from "@lucide/svelte";
  import { BaseDirectory, readTextFile } from "@tauri-apps/plugin-fs";
  import {
    settings,
    DEFAULT_PUBLISH_TAB_SETTINGS,
    type PublishTabSettings,
  } from "$lib/settings.svelte";
  import { saveSettings } from "$lib/app-init";
  import { configStore } from "$lib/config-store.svelte";
  import {
    type CodesigningData,
    type AndroidCodesignInfo,
    DEFAULT_CODESIGNING_CONFIG,
    getRuntimeForPlatform,
    getFrameworkForPlatform,
    getCodesigningParams,
    parseAndroidCodesignInfo,
    buildCommandPreview,
  } from "./publishing.svelte";

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
  let noRestore = $state(settings.publishTab.noRestore ?? false);

  let settingsInitialized = $state(false);

  // Derived projects list from active config
  const projects = $derived(configStore.activeConfig?.projects ?? []);

  let codesigningConfig = $state<CodesigningData>(DEFAULT_CODESIGNING_CONFIG);

  // Parsed Android codesign info from text file
  let androidCodesignInfo = $state<AndroidCodesignInfo>({
    Alias: "",
    KeyPass: "",
    StorePass: "",
  });

  onMount(async () => {
    await loadCodesigningConfig();
    settingsInitialized = true;
  });

  async function loadCodesigningConfig() {
    try {
      const content = await readTextFile(".pace/codesigning.json", {
        baseDir: BaseDirectory.Home,
      });
      const parsed = JSON.parse(content) as CodesigningData;
      codesigningConfig = parsed;
    } catch {
      // Use default config if file doesn't exist or is invalid
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
      noRestore,
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
    noRestore = d.noRestore ?? false;
  }

  // Load Android codesign info when key changes
  $effect(() => {
    if (!settingsInitialized) return;

    // Access codesigningConfig to ensure it's tracked as a dependency
    const androidConfig = codesigningConfig.android;

    if (androidKey) {
      const config = androidConfig[androidKey];
      if (config?.CodesignInfoTxtPath) {
        parseAndroidCodesignInfo(config.CodesignInfoTxtPath).then((info) => {
          androidCodesignInfo = info;
        });
      } else {
        androidCodesignInfo = { Alias: "", KeyPass: "", StorePass: "" };
      }
    } else {
      androidCodesignInfo = { Alias: "", KeyPass: "", StorePass: "" };
    }
  });

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

  // Build status tracking for each platform
  type BuildStatus = "pending" | "building" | "success" | "error";
  let buildStatuses = $state<Record<string, BuildStatus>>({});

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

    // Add --no-restore if enabled
    if (noRestore) {
      publishArgs.push("--no-restore");
    }

    // Add Android-specific params for Debug builds
    if (platform === "android" && buildConfig === "Debug") {
      publishArgs.push("/p:EmbedAssembliesIntoApk=true");
    }

    // Add platform-specific codesigning params
    const codesigningParams = await getCodesigningParams(
      platform,
      codesigningConfig,
      androidKey,
      iosBundleId,
      windowsKey,
      androidCodesignInfo,
    );
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

    // Initialize build statuses
    buildStatuses = {};
    for (const platform of orderedSelectedPlatforms) {
      buildStatuses[platform] = "pending";
    }

    try {
      for (let i = 0; i < orderedSelectedPlatforms.length; i++) {
        currentPlatformIndex = i;
        const platform = orderedSelectedPlatforms[i];
        const platformProgress = Math.round(
          (i / orderedSelectedPlatforms.length) * 100,
        );
        progress = platformProgress;
        progressLabel = `Building ${platform}...`;
        buildStatuses[platform] = "building";

        addLine(
          `\n========== Starting build for ${platform} ==========\n`,
          "out",
        );

        const success = await runBuildForPlatform(platform);

        if (!success) {
          buildStatuses[platform] = "error";
          addLine(
            `\n========== Build failed for ${platform} ==========\n`,
            "err",
          );
          progressLabel = `Build failed for ${platform}`;
          progress = 100;
          break;
        }

        buildStatuses[platform] = "success";
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

  // Command preview data structure for UI rendering
  const commandPreviews = $derived.by(() => {
    if (!selectedProject || selectedPlatforms.length === 0) return [];

    const project = projects.find((p) => p.name === selectedProject);
    const repodir = configStore.activeConfig?.repodir ?? "<repodir>";
    const csprojPath = project?.csproj_path
      ? `${repodir}/${project.name}/${project.csproj_path}`
      : "<csproj_path>";

    // For multiple platforms, we can't easily show async previews in $derived
    // So we'll return the structure and let the UI handle single preview or summary
    return orderedSelectedPlatforms.map((platform) => ({
      platform,
      csprojPath,
    }));
  });

  const progressBarColor = $derived.by(() => {
    if (/failed|cancelled|error/i.test(progressLabel)) return "bg-error-500";
    if (/completed|succeeded/i.test(progressLabel)) return "bg-success-500";
    return "bg-primary-500";
  });
</script>

<div class="h-full flex flex-col">
  <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
    <!-- Project & Platform Selection -->
    <div class="grid grid-cols-2 gap-3">
      <div class="card bg-surface-50-950 p-3 flex flex-col gap-2">
        <div class="flex items-center gap-2">
          <Folder size={16} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100 text-sm">Project</span
          >
        </div>
        {#if projects.length === 0}
          <div class="text-xs text-surface-500-400">No projects available.</div>
        {:else}
          <div class="relative">
            <select
              bind:value={selectedProject}
              class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-1.5 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
              style="background-image:none"
            >
              <option value="">— Select —</option>
              {#each projects as project}
                <option value={project.name}>{project.name}</option>
              {/each}
            </select>
            <ChevronDown
              size={14}
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-500-400 pointer-events-none"
            />
          </div>
        {/if}
      </div>

      <div class="card bg-surface-50-950 p-3 flex flex-col gap-2">
        <div class="flex items-center gap-2">
          <Globe size={16} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100 text-sm"
            >Platforms</span
          >
        </div>
        <div class="flex flex-wrap gap-2">
          {#each PLATFORMS as platform}
            {@const Icon = platform.icon}
            {@const isSelected = selectedPlatforms.includes(platform.id)}
            <button
              type="button"
              onclick={() => togglePlatform(platform.id)}
              class="flex items-center gap-2 px-3 py-2 rounded text-sm font-medium border transition-colors {isSelected
                ? 'bg-primary-500 border-primary-500 text-white'
                : 'bg-surface-100-900 border-surface-300-700 text-surface-700-300 hover:border-primary-500 hover:text-primary-500'}"
            >
              <Icon size={16} />
              {platform.label}
            </button>
          {/each}
        </div>
      </div>
    </div>

    <!-- Build Configuration -->
    <div class="card bg-surface-50-950 p-3 flex flex-col gap-2">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Hammer size={16} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100 text-sm">Build</span>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex gap-2">
            {#each ["Debug", "Release"] as const as cfg}
              <button
                type="button"
                onclick={() => (buildConfig = cfg)}
                class="px-3 py-2 rounded text-sm font-medium border transition-colors {buildConfig ===
                cfg
                  ? 'bg-primary-500 border-primary-500 text-white'
                  : 'bg-surface-100-900 border-surface-300-700 text-surface-700-300 hover:border-primary-500 hover:text-primary-500'}"
              >
                {cfg}
              </button>
            {/each}
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <span class="text-xs font-medium text-surface-600-400"
              >--no-restore</span
            >
            <div class="relative inline-flex items-center">
              <input
                type="checkbox"
                bind:checked={noRestore}
                class="peer sr-only"
              />
              <div
                class="w-9 h-5 bg-surface-300-700 rounded-full peer-checked:bg-primary-500 transition-colors"
              ></div>
              <div
                class="absolute left-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-4"
              ></div>
            </div>
          </label>
        </div>
      </div>
    </div>

    <!-- Codesigning Configuration -->
    {#if selectedPlatforms.length > 0}
      <div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
        <span class="font-semibold text-surface-900-100 text-sm"
          >Codesigning</span
        >
        <div class="grid gap-3">
          {#if selectedPlatforms.includes("ios")}
            <div class="flex flex-col gap-1">
              <label
                class="text-xs font-medium text-surface-600-400"
                for="ios-bundle">iOS Bundle</label
              >
              <div class="relative">
                <select
                  id="ios-bundle"
                  bind:value={iosBundleId}
                  class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-1.5 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
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
                for="windows-cert">Windows Cert</label
              >
              <div class="relative">
                <select
                  id="windows-cert"
                  bind:value={windowsKey}
                  class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-1.5 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
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
            <div class="flex flex-col gap-2">
              <div class="flex flex-col gap-1">
                <label
                  class="text-xs font-medium text-surface-600-400"
                  for="android-keystore">Android Keystore</label
                >
                <div class="relative">
                  <select
                    id="android-keystore"
                    bind:value={androidKey}
                    class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-1.5 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
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
              {#if androidKey && androidKey !== "*"}
                {@const config = codesigningConfig.android[androidKey]}
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div class="flex flex-col gap-1">
                    <span class="font-medium text-surface-600-400">Alias</span>
                    <span
                      class="px-2 py-1.5 bg-surface-100-900 rounded border border-surface-300-700 {androidCodesignInfo?.Alias
                        ? 'text-surface-900-100'
                        : 'text-surface-500-400 italic'}"
                    >
                      {androidCodesignInfo?.Alias || "Not loaded"}
                    </span>
                  </div>
                  <div class="flex flex-col gap-1">
                    <span class="font-medium text-surface-600-400"
                      >Key Pass</span
                    >
                    <span
                      class="px-2 py-1.5 bg-surface-100-900 rounded border border-surface-300-700 {androidCodesignInfo?.KeyPass
                        ? 'text-surface-900-100'
                        : 'text-surface-500-400 italic'}"
                    >
                      {androidCodesignInfo?.KeyPass ? "••••••" : "Not loaded"}
                    </span>
                  </div>
                  <div class="flex flex-col gap-1 col-span-2">
                    <span class="font-medium text-surface-600-400"
                      >Store Pass</span
                    >
                    <span
                      class="px-2 py-1.5 bg-surface-100-900 rounded border border-surface-300-700 {androidCodesignInfo?.StorePass
                        ? 'text-surface-900-100'
                        : 'text-surface-500-400 italic'}"
                    >
                      {androidCodesignInfo?.StorePass ? "••••••" : "Not loaded"}
                    </span>
                  </div>
                  {#if !androidCodesignInfo?.Alias && config?.CodesignInfoTxtPath}
                    <div class="col-span-2 text-xs text-surface-500-400">
                      Info file: {config.CodesignInfoTxtPath}
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Command Preview -->
    {#if selectedPlatforms.length > 0}
      <div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <Terminal size={14} class="text-primary-500 shrink-0" />
          <span
            class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
          >
            Command preview
          </span>
        </div>

        {#if commandPreviews.length === 0}
          <div class="text-sm text-surface-500-400">
            Select a project and platforms to see preview
          </div>
        {:else}
          <div class="flex flex-col gap-3">
            {#each commandPreviews as { platform, csprojPath }}
              {@const PLATFORMS_ = PLATFORMS}
              {@const platformConfig = PLATFORMS_.find(
                (p) => p.id === platform,
              )}
              {@const Icon = platformConfig?.icon}
              <div class="flex flex-col gap-1">
                <div
                  class="text-xs font-medium text-surface-600-400 flex items-center gap-2"
                >
                  {#if Icon}
                    <Icon size={12} />
                  {/if}
                  <span>{platformConfig?.label || platform}</span>
                </div>
                <code
                  class="text-xs font-mono bg-surface-200-800 px-3 py-2 rounded whitespace-pre-wrap break-all text-surface-900-100"
                >
                  dotnet publish {csprojPath} -c {buildConfig} --runtime {getRuntimeForPlatform(
                    platform,
                  )} --framework {getFrameworkForPlatform(platform)} --self-contained
                  /p:DistributionMethod=enterprise /p:ArchiveOnBuild=true
                </code>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Build Status -->
    {#if isRunning || Object.keys(buildStatuses).length > 0}
      <div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <span
            class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
          >
            Build Status
          </span>
          <span
            class="font-mono text-xs text-surface-600-400 flex items-center gap-2"
          >
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

        <div class="flex flex-col gap-2">
          {#each orderedSelectedPlatforms as platform}
            {@const PLATFORMS_ = PLATFORMS}
            {@const platformConfig = PLATFORMS_.find((p) => p.id === platform)}
            {@const Icon = platformConfig?.icon}
            {@const status = buildStatuses[platform] || "pending"}
            <div
              class="flex items-center gap-3 p-2 rounded bg-surface-100-900 border border-surface-300-700"
            >
              <div
                class="flex items-center justify-center w-8 h-8 rounded-full shrink-0 {status ===
                'success'
                  ? 'bg-success-500/20'
                  : status === 'error'
                    ? 'bg-error-500/20'
                    : status === 'building'
                      ? 'bg-primary-500/20'
                      : 'bg-surface-300-700/50'}"
              >
                {#if status === "success"}
                  <Check size={16} class="text-success-500" />
                {:else if status === "error"}
                  <X size={16} class="text-error-500" />
                {:else if status === "building"}
                  <Loader size={16} class="animate-spin text-primary-500" />
                {:else}
                  <div class="w-4 h-4 rounded-full bg-surface-500-400"></div>
                {/if}
              </div>
              <div class="flex-1 min-w-0">
                <div
                  class="text-sm font-medium text-surface-900-100 flex items-center gap-2"
                >
                  {#if Icon}
                    <Icon size={14} />
                  {/if}
                  <span>{platformConfig?.label || platform}</span>
                </div>
              </div>
              <div
                class="text-xs font-medium uppercase {status === 'success'
                  ? 'text-success-500'
                  : status === 'error'
                    ? 'text-error-500'
                    : status === 'building'
                      ? 'text-primary-500'
                      : 'text-surface-500-400'}"
              >
                {status}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Output log -->
    {#if outputLines.length > 0}
      <div class="card bg-surface-50-950 p-3 flex flex-col gap-2">
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
    class="shrink-0 flex items-center justify-end gap-3 px-4 py-3 border-t border-surface-200-800 bg-surface-50-950"
  >
    <button
      class="btn preset-tonal flex items-center gap-2"
      onclick={resetToDefaults}
      disabled={isRunning}
      title="Reset all publish settings to defaults"
    >
      <RotateCcw size={16} />
      Reset
    </button>

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
  </div>
</div>
