<script lang="ts">
  import { tick, onMount, untrack } from "svelte";
  import { Switch } from "@skeletonlabs/skeleton-svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import {
    Globe,
    Hammer,
    Square,
    ChevronDown,
    Terminal,
    RotateCcw,
    Folder,
    FolderOpen,
  } from "@lucide/svelte";
  import { open } from "@tauri-apps/plugin-dialog";
  import { BaseDirectory, readTextFile } from "@tauri-apps/plugin-fs";
  import {
    settings,
    DEFAULT_PUBLISH_TAB_SETTINGS,
    type PublishTabSettings,
  } from "$lib/settings.svelte";
  import { saveSettings } from "$lib/app-init";
  import { configStore, paceArgs } from "$lib/config-store.svelte";
  import {
    type CodesigningData,
    type AndroidCodesignInfo,
    DEFAULT_CODESIGNING_CONFIG,
    getRuntimeForPlatform,
    getFrameworkForPlatform,
    getCodesigningParams,
    parseAndroidCodesignInfo,
    buildCommandPreview,
  } from "$lib/orchestrator/publishing.svelte";
  import { setPublishingStatus } from "$lib/orchestrator/command-status.svelte";
  import CopyButton from "$lib/components/CopyButton.svelte";
  import {
    PLATFORMS,
    platformOrder,
    type Platform,
    type BuildStatus,
  } from "$lib/orchestrator/publish-tab/platforms";
  import CodesigningSection from "$lib/orchestrator/publish-tab/CodesigningSection.svelte";
  import PublishOutputPanel from "$lib/orchestrator/publish-tab/PublishOutputPanel.svelte";

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
  let cleanBeforeBuild = $state(settings.publishTab.cleanBeforeBuild ?? false);

  let msbuildProps = $state<Record<string, string>>({
    ...settings.publishTab.msbuildProps,
  });

  const buildProps = $derived(configStore.activeConfig?.build_props ?? []);

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
      cleanBeforeBuild,
      msbuildProps: { ...msbuildProps },
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
    cleanBeforeBuild = d.cleanBeforeBuild ?? false;
    msbuildProps = {};
  }

  async function pickPath(propName: string) {
    const selected = await open({ directory: true, multiple: false });
    if (selected && typeof selected === "string") {
      msbuildProps = { ...msbuildProps, [propName]: selected };
    }
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
  let outputRef = $state<HTMLDivElement>();
  let elapsedSeconds = $state(0);
  let timerInterval: ReturnType<typeof setInterval> | null = null;

  // Build status tracking for each platform
  let buildStatuses = $state<Record<string, BuildStatus>>({});

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
      ...(platform !== "windows" ? ["--runtime", runtime] : []),
      "--framework",
      framework,
      "--self-contained",
      "/p:DistributionMethod=enterprise",
      "/p:ArchiveOnBuild=true",
    ];

    // Add --no-restore if enabled
    if (noRestore) {
      publishArgs.push("--no-restore");
    }

    // Add MSBuild properties from config
    for (const prop of buildProps) {
      const val = msbuildProps[prop.name];
      const effective = val !== undefined ? val : String(prop.default);
      if (effective !== "" && effective !== String(prop.default))
        publishArgs.push(`-p:${prop.name}=${effective}`);
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

  async function runClean(): Promise<boolean> {
    progressLabel = "Cleaning bin/ and obj/ directories...";
    addLine(
      "\n========== Cleaning bin/ and obj/ directories ==========\n",
      "out",
    );

    const cleanArgs = await paceArgs([
      "--to",
      selectedProject,
      "clean",
      "--projects",
    ]);

    return new Promise((resolve) => {
      try {
        const cmd = Command.create("pace", cleanArgs);

        cmd.stdout.on("data", (data: string) => addLine(data, "out"));
        cmd.stderr.on("data", (data: string) => addLine(data, "err"));

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
    setPublishingStatus(true);
    currentPlatformIndex = 0;
    progress = 0;

    // Initialize build statuses
    buildStatuses = {};
    for (const platform of orderedSelectedPlatforms) {
      buildStatuses[platform] = "pending";
    }

    try {
      if (cleanBeforeBuild) {
        const cleanSuccess = await runClean();
        currentProcess = null;
        if (!cleanSuccess) {
          addLine("\n========== Clean failed ==========\n", "err");
          progressLabel = "Clean failed";
          progress = 100;
          return;
        }
        addLine("\n========== Clean completed ==========\n", "out");
      }

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
      setPublishingStatus(false);
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
    setPublishingStatus(false);
    currentProcess = null;
  }

  const cleanCommandPreview = $derived.by(() => {
    const parts: string[] = ["pace"];
    if (selectedProject) parts.push("--to", selectedProject);
    parts.push("clean", "--projects");
    return parts.join(" ");
  });

  // Command previews as async state+effect to support path expansion
  let commandPreviews = $state<{ platform: Platform; command: string }[]>([]);

  $effect(() => {
    if (!selectedProject || selectedPlatforms.length === 0) {
      commandPreviews = [];
      return;
    }

    const project = projects.find((p) => p.name === selectedProject);
    const repodir = configStore.activeConfig?.repodir ?? "<repodir>";
    const csprojPath = project?.csproj_path
      ? `${repodir}/${project.name}/${project.csproj_path}`
      : "<csproj_path>";

    // Capture reactive deps before async
    const platforms = [...orderedSelectedPlatforms];
    const config = codesigningConfig;
    const aKey = androidKey;
    const iKey = iosBundleId;
    const wKey = windowsKey;
    const signInfo = androidCodesignInfo;
    const bc = buildConfig;
    const nr = noRestore;
    const props = buildProps;
    const msbProps = { ...msbuildProps };

    Promise.all(
      platforms.map(async (platform) => {
        const runtime = getRuntimeForPlatform(platform);
        const framework = getFrameworkForPlatform(platform);
        let command = await buildCommandPreview(
          csprojPath,
          bc,
          runtime,
          framework,
          nr,
          platform,
          config,
          aKey,
          iKey,
          wKey,
          signInfo,
        );
        // Add MSBuild properties to preview
        for (const prop of props) {
          const val = msbProps[prop.name];
          const effective = val !== undefined ? val : String(prop.default);
          if (effective !== "" && effective !== String(prop.default))
            command += ` -p:${prop.name}=${effective}`;
        }
        return { platform, command };
      }),
    ).then((previews) => {
      commandPreviews = previews;
    });
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
    <div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <Hammer size={16} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100 text-sm">Build</span>
      </div>
      <div class="flex flex-wrap gap-2">
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

      <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
        <div class="flex items-center gap-3">
          <Switch
            checked={noRestore}
            onCheckedChange={(details) => (noRestore = details.checked)}
          >
            <Switch.Control><Switch.Thumb /></Switch.Control>
            <Switch.HiddenInput />
          </Switch>
          <span class="text-sm text-surface-900-100"
            >Skip restore (--no-restore)</span
          >
        </div>

        <div class="flex items-center gap-3">
          <Switch
            checked={cleanBeforeBuild}
            onCheckedChange={(details) => (cleanBeforeBuild = details.checked)}
          >
            <Switch.Control><Switch.Thumb /></Switch.Control>
            <Switch.HiddenInput />
          </Switch>
          <span class="text-sm text-surface-900-100"
            >Clean bin/ and obj/ dirs before build</span
          >
        </div>
      </div>
    </div>

    <!-- MSBuild Properties -->
    {#if buildProps.length > 0}
      <div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
        <span class="font-semibold text-surface-900-100 text-sm"
          >MSBuild Properties</span
        >

        {#each buildProps as prop}
          {#if prop.datatype === "boolean"}
            {@const val =
              msbuildProps[prop.name] !== undefined
                ? msbuildProps[prop.name] === "true"
                : prop.default === true || prop.default === "true"}
            <div class="flex items-center gap-3">
              <Switch
                checked={val}
                name="msbuild-{prop.name}"
                onCheckedChange={(details) =>
                  (msbuildProps = {
                    ...msbuildProps,
                    [prop.name]: details.checked ? "true" : "false",
                  })}
              >
                <Switch.Control>
                  <Switch.Thumb />
                </Switch.Control>
                <Switch.HiddenInput />
              </Switch>
              <span class="text-sm font-mono text-surface-900-100"
                >{prop.name}</span
              >
              <span
                class="text-xs ml-auto {val
                  ? 'text-primary-400'
                  : 'text-surface-500-400'}"
              >
                {val ? "true" : "false"}
              </span>
            </div>
          {:else if prop.datatype === "path"}
            <div class="flex flex-col gap-1">
              <label
                class="text-xs font-medium text-surface-600-400"
                for="msbuild-{prop.name}"
              >
                {prop.name}
              </label>
              <div class="input-group grid grid-cols-[1fr_auto]">
                <input
                  id="msbuild-{prop.name}"
                  class="ig-input font-mono text-sm"
                  type="text"
                  placeholder="{String(prop.default) ||
                    '/path/to/dir'} (optional)"
                  value={msbuildProps[prop.name] ?? String(prop.default)}
                  oninput={(e) =>
                    (msbuildProps = {
                      ...msbuildProps,
                      [prop.name]: (e.target as HTMLInputElement).value,
                    })}
                />
                <button
                  class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
                  type="button"
                  onclick={() => pickPath(prop.name)}
                  title="Browse"
                >
                  <FolderOpen size={16} />
                </button>
              </div>
            </div>
          {:else}
            <div class="flex flex-col gap-1">
              <label
                class="text-xs font-medium text-surface-600-400"
                for="msbuild-{prop.name}"
              >
                {prop.name}
              </label>
              <input
                id="msbuild-{prop.name}"
                class="input font-mono text-sm"
                type="text"
                placeholder={String(prop.default) || "(optional)"}
                value={msbuildProps[prop.name] ?? String(prop.default)}
                oninput={(e) =>
                  (msbuildProps = {
                    ...msbuildProps,
                    [prop.name]: (e.target as HTMLInputElement).value,
                  })}
              />
            </div>
          {/if}
        {/each}
      </div>
    {/if}

    <!-- Codesigning Configuration -->
    {#if selectedPlatforms.length > 0}
      <CodesigningSection
        {selectedPlatforms}
        {codesigningConfig}
        {androidCodesignInfo}
        bind:iosBundleId
        bind:windowsKey
        bind:androidKey
      />
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
            {#if cleanBeforeBuild}
              <div class="flex flex-col gap-1">
                <div
                  class="text-xs font-medium text-surface-600-400 flex items-center justify-between"
                >
                  <span>Clean (runs first)</span>
                  <CopyButton text={cleanCommandPreview} />
                </div>
                <code
                  class="text-xs font-mono bg-surface-200-800 px-3 py-2 rounded whitespace-pre-wrap break-all text-surface-900-100"
                >
                  {cleanCommandPreview}
                </code>
              </div>
            {/if}
            {#each commandPreviews as { platform, command }}
              {@const PLATFORMS_ = PLATFORMS}
              {@const platformConfig = PLATFORMS_.find(
                (p) => p.id === platform,
              )}
              {@const Icon = platformConfig?.icon}
              <div class="flex flex-col gap-1">
                <div
                  class="text-xs font-medium text-surface-600-400 flex items-center justify-between"
                >
                  <div class="flex items-center gap-2">
                    {#if Icon}
                      <Icon size={12} />
                    {/if}
                    <span>{platformConfig?.label || platform}</span>
                  </div>
                  <CopyButton text={command} />
                </div>
                <code
                  class="text-xs font-mono bg-surface-200-800 px-3 py-2 rounded whitespace-pre-wrap break-all text-surface-900-100"
                >
                  {command}
                </code>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <PublishOutputPanel
      {isRunning}
      {buildStatuses}
      {orderedSelectedPlatforms}
      {progress}
      {progressLabel}
      {progressBarColor}
      {elapsedSeconds}
      {outputLines}
      bind:outputRef
    />
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
