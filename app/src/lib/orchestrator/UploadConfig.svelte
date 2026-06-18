<script lang="ts">
  import { tick, onMount, untrack } from "svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import {
    CloudUpload,
    Folder,
    ChevronDown,
    Terminal,
    Square,
    Upload,
    RotateCcw,
    Package,
    RotateCw,
    ExternalLink,
    Settings,
    TriangleAlert,
  } from "@lucide/svelte";
  import { readDir } from "@tauri-apps/plugin-fs";
  import { openPath, openUrl } from "@tauri-apps/plugin-opener";
  import { dirname, join } from "@tauri-apps/api/path";
  import {
    settings,
    DEFAULT_UPLOAD_TAB_SETTINGS,
    type UploadTabSettings,
  } from "$lib/settings.svelte";
  import { saveSettings } from "$lib/app-init";
  import { configStore } from "$lib/config-store.svelte";
  import { setUploadingStatus } from "$lib/orchestrator/command-status.svelte";
  import CopyButton from "$lib/components/CopyButton.svelte";
  import type {
    Platform,
    BuildConfig,
    PackageFile,
    UploadStatus,
  } from "$lib/orchestrator/upload-tab/types";
  import {
    getPlatformIcon,
    getApiPlatform,
  } from "$lib/orchestrator/upload-tab/platform";
  import PackageRow from "$lib/orchestrator/upload-tab/PackageRow.svelte";
  import UploadOutputPanel from "$lib/orchestrator/upload-tab/UploadOutputPanel.svelte";

  interface Props {
    onGoToSettings?: () => void;
  }

  let { onGoToSettings }: Props = $props();

  async function openStorageEndpoint() {
    let url = settings.general.storageEndpointUrl;
    if (!url) return;
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = "https://" + url;
    }
    try {
      await openUrl(url);
    } catch (e) {
      console.error("Failed to open URL:", e);
    }
  }

  // Load settings
  let selectedProject = $state(settings.uploadTab.selectedProject);
  let selectedPackages = $state<string[]>([
    ...settings.uploadTab.selectedPackages,
  ]);
  let username = $state(settings.uploadTab.username);
  let appName = $state(settings.uploadTab.appName);
  let version = $state(settings.uploadTab.version);
  let buildNotes = $state(settings.uploadTab.buildNotes);

  let settingsInitialized = $state(false);

  // Endpoint configuration
  const endpointUrl = $derived(settings.general.storageEndpointUrl);
  const isEndpointConfigured = $derived(!!endpointUrl);

  // Derived projects list from active config
  const projects = $derived(configStore.activeConfig?.projects ?? []);
  const repodir = $derived(configStore.activeConfig?.repodir);

  // UI State
  let isUploading = $state(false);
  let currentProcess: any = $state(null);
  let outputLines: { type: "out" | "err"; text: string }[] = $state([]);
  let outputRef = $state<HTMLDivElement | null>(null);
  let showOutput = $state(true);
  let availablePackages: PackageFile[] = $state([]);
  let scanningPackages = $state(false);

  // Upload status tracking for parallel uploads
  let uploadStatuses = $state<Record<string, UploadStatus>>({});
  let uploadProgress = $state<Record<string, string>>({});

  // Initialize settings loaded flag
  onMount(() => {
    tick().then(() => {
      settingsInitialized = true;
      if (selectedProject) {
        scanForPackages();
      }
    });
  });

  // Save settings on change
  $effect(() => {
    if (!settingsInitialized) return;
    const snapshot: UploadTabSettings = {
      selectedProject,
      selectedPackages: [...selectedPackages],
      username,
      appName,
      version,
      buildNotes,
    };
    untrack(() => {
      settings.uploadTab = snapshot;
      saveSettings().catch((e) =>
        console.error("Failed to save upload settings:", e),
      );
    });
  });

  // Scan for packages when project changes
  $effect(() => {
    if (selectedProject && repodir) {
      scanForPackages();
    } else {
      availablePackages = [];
      selectedPackages = [];
    }
  });

  async function scanForPackages() {
    if (!selectedProject || !repodir) {
      return;
    }

    // Find the project and get its csproj_path
    const project = projects.find((p) => p.name === selectedProject);
    if (!project?.csproj_path) {
      return;
    }

    scanningPackages = true;
    const packages: PackageFile[] = [];

    // Get the project directory (where .csproj is located)
    const csprojDir = await dirname(project.csproj_path);
    const projectPath = await join(repodir, selectedProject, csprojDir);

    // Detect platform from file extension
    function detectPlatformFromExtension(filename: string): Platform | null {
      const lower = filename.toLowerCase();
      if (lower.endsWith(".ipa")) return "ios";
      if (lower.endsWith(".apk")) return "android";
      if (lower.endsWith(".msix")) return "windows";
      return null;
    }

    // Detect build config from path
    function detectBuildConfigFromPath(path: string): BuildConfig {
      const lower = path.toLowerCase();
      if (lower.includes("debug")) return "Debug";
      if (lower.includes("release")) return "Release";
      return "Release"; // Default
    }

    // Function to search for package files with max depth
    async function searchDirectory(
      dirPath: string,
      maxDepth: number,
      currentDepth = 0,
    ) {
      if (currentDepth >= maxDepth) return;

      try {
        const entries = await readDir(dirPath);
        for (const entry of entries) {
          const entryPath = await join(dirPath, entry.name);
          if (entry.isFile) {
            const name = entry.name || "";
            // Detect platform from file extension
            const platform = detectPlatformFromExtension(name);
            if (platform) {
              const buildConfig = detectBuildConfigFromPath(entryPath);
              packages.push({
                name: entry.name!,
                path: entryPath,
                platform,
                buildConfig,
              });
            }
          } else if (entry.isDirectory) {
            // Recursively search subdirectories
            await searchDirectory(entryPath, maxDepth, currentDepth + 1);
          }
        }
      } catch (e) {
        // console.error("Error reading directory:", e);
      }
    }

    // Search bin/ with depth 5 and AppPackages/ with depth 2
    const binPath = await join(projectPath, "bin");
    const appPackagesPath = await join(projectPath, "AppPackages");

    await searchDirectory(binPath, 5);
    await searchDirectory(appPackagesPath, 2);

    availablePackages = packages.sort((a, b) => {
      // Sort by build config (Release first), then platform
      if (a.buildConfig !== b.buildConfig) {
        return a.buildConfig === "Release" ? -1 : 1;
      }
      return a.platform.localeCompare(b.platform);
    });

    // Filter out any selected packages that are no longer available
    const availablePaths = new Set(packages.map((p) => p.path));
    selectedPackages = selectedPackages.filter((p) => availablePaths.has(p));

    scanningPackages = false;
  }

  function togglePackage(path: string) {
    if (selectedPackages.includes(path)) {
      selectedPackages = selectedPackages.filter((p) => p !== path);
    } else {
      selectedPackages = [...selectedPackages, path];
    }
  }

  async function revealPackage(pkg: PackageFile) {
    try {
      const dir = await dirname(pkg.path);
      await openPath(dir);
    } catch (e) {
      console.error("Failed to open package folder:", e);
    }
  }

  function addLine(text: string, type: "out" | "err" = "out") {
    outputLines = [...outputLines, { type, text }];
    tick().then(() => {
      if (outputRef) {
        outputRef.scrollTop = outputRef.scrollHeight;
      }
    });
  }

  function resetOutput() {
    outputLines = [];
  }

  function cancelUpload() {
    if (currentProcess) {
      currentProcess.kill();
      currentProcess = null;
    }
    isUploading = false;
    setUploadingStatus(false);
    addLine("Upload cancelled", "err");
  }

  async function runUpload() {
    if (
      isUploading ||
      selectedPackages.length === 0 ||
      !username ||
      !appName ||
      !version ||
      !isEndpointConfigured
    )
      return;

    resetOutput();
    isUploading = true;
    setUploadingStatus(true);

    // Initialize upload statuses
    uploadStatuses = {};
    uploadProgress = {};
    for (const packagePath of selectedPackages) {
      uploadStatuses[packagePath] = "pending";
      uploadProgress[packagePath] = "";
    }

    // Run all uploads in parallel
    const uploadPromises = selectedPackages.map(async (packagePath) => {
      const pkg = availablePackages.find((p) => p.path === packagePath);
      if (!pkg) {
        uploadStatuses[packagePath] = "error";
        return false;
      }

      uploadStatuses[packagePath] = "uploading";
      const success = await uploadPackage(pkg, packagePath);
      uploadStatuses[packagePath] = success ? "success" : "error";
      return success;
    });

    await Promise.all(uploadPromises);

    isUploading = false;
    setUploadingStatus(false);
    currentProcess = null;
  }

  async function uploadPackage(
    pkg: PackageFile,
    packagePath: string,
  ): Promise<boolean> {
    const apiPlatform = getApiPlatform(pkg.platform);

    const paceArgs = [
      "upload",
      pkg.path,
      "--username",
      username,
      "--app-name",
      appName,
      "--platform",
      apiPlatform,
      "--release-type",
      pkg.buildConfig,
      "--version",
      version,
      "--endpoint",
      endpointUrl,
    ];

    if (buildNotes) {
      paceArgs.push("--build-description", buildNotes);
    }

    return new Promise((resolve) => {
      try {
        const cmd = Command.create("pace", paceArgs);

        cmd.stdout.on("data", (data: string) => {
          uploadProgress[packagePath] = data.trim();
        });

        cmd.stderr.on("data", (data: string) => {
          uploadProgress[packagePath] = data.trim();
        });

        cmd.on("close", (payload: { code: number | null }) => {
          resolve(payload.code === 0);
        });

        cmd.spawn();
      } catch (e) {
        addLine(`Error: ${e instanceof Error ? e.message : String(e)}`, "err");
        resolve(false);
      }
    });
  }

  function resetToDefaults() {
    const d = DEFAULT_UPLOAD_TAB_SETTINGS;
    selectedProject = d.selectedProject;
    selectedPackages = [...d.selectedPackages];
    username = d.username;
    appName = d.appName;
    version = d.version;
    buildNotes = d.buildNotes;
    resetOutput();
  }

  // Command preview data structure for UI rendering
  const commandPreviews = $derived.by(() => {
    if (selectedPackages.length === 0) return [];
    if (!username || !appName || !version) return [];

    return selectedPackages
      .map((packagePath) => {
        const pkg = availablePackages.find((p) => p.path === packagePath);
        if (!pkg) return null;

        const apiPlatform = getApiPlatform(pkg.platform);
        let cmd = `pace upload "${pkg.path}" --username "${username}" --app-name "${appName}" --platform ${apiPlatform} --release-type ${pkg.buildConfig} --version "${version}" --endpoint "${endpointUrl}"`;
        if (buildNotes) {
          cmd += ` --build-description "${buildNotes}"`;
        }

        return {
          pkg,
          command: cmd,
        };
      })
      .filter(
        (item): item is { pkg: PackageFile; command: string } => item !== null,
      );
  });
</script>

<div class="h-full flex flex-col">
  <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
    <!-- Storage Endpoint Configuration Warning -->
    {#if !isEndpointConfigured}
      <div
        class="card bg-warning-500/10 border border-warning-500 p-4 flex flex-col gap-3"
      >
        <div class="flex items-center gap-2">
          <TriangleAlert size={18} class="text-warning-500" />
          <span class="font-semibold text-warning-600-400"
            >Storage Endpoint Not Configured</span
          >
        </div>
        <p class="text-sm text-surface-700-300">
          You need to configure a storage endpoint before uploading packages.
        </p>
        {#if onGoToSettings}
          <button
            class="btn preset-tonal flex items-center gap-2 self-start text-sm"
            onclick={onGoToSettings}
          >
            <Settings size={14} />
            Configure in Settings
          </button>
        {/if}
      </div>
    {/if}

    <!-- Storage Endpoint Link -->
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <CloudUpload size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100"
            >Storage Endpoint</span
          >
        </div>
        <button
          class="btn preset-tonal flex items-center gap-2 text-sm"
          onclick={openStorageEndpoint}
          disabled={!settings.general.storageEndpointUrl}
          title="Open storage endpoint in browser"
        >
          <ExternalLink size={14} />
          Go to website
        </button>
      </div>
      <div class="text-xs text-surface-600-400">
        {settings.general.storageEndpointUrl || "Not configured"}
      </div>
    </div>

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
            >Select project</span
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

    <!-- Package Files -->
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <Package size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100"
          >Available packages</span
        >
        {#if selectedProject}
          <button
            type="button"
            onclick={() => scanForPackages()}
            disabled={scanningPackages}
            class="ml-auto p-1.5 rounded hover:bg-surface-200-800 disabled:opacity-50"
            title="Refresh packages"
          >
            <RotateCw
              size={14}
              class={scanningPackages ? "animate-spin" : ""}
            />
          </button>
        {/if}
        {#if scanningPackages}
          <span class="text-xs text-surface-500-400">Scanning...</span>
        {/if}
      </div>

      {#if !selectedProject}
        <div class="text-sm text-surface-500-400">
          Select a project to see available packages.
        </div>
      {:else if availablePackages.length === 0}
        <div class="text-sm text-surface-500-400">
          No .ipa, .msix, or .apk files found in Debug/Release/publish
          directories.
        </div>
      {:else}
        <div class="flex flex-col gap-2">
          {#each availablePackages as pkg (pkg.path)}
            <PackageRow
              {pkg}
              selected={selectedPackages.includes(pkg.path)}
              ontoggle={() => togglePackage(pkg.path)}
              onreveal={() => revealPackage(pkg)}
            />
          {/each}
        </div>
        <div class="text-xs text-surface-500-400">
          {selectedPackages.length} of {availablePackages.length} selected
        </div>
      {/if}
    </div>

    <!-- Upload Details -->
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <CloudUpload size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100">Upload details</span>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label
            class="text-xs font-medium text-surface-600-400"
            for="upload-username">Username</label
          >
          <input
            id="upload-username"
            type="text"
            class="input text-sm"
            placeholder="your.username"
            bind:value={username}
          />
        </div>
        <div class="flex flex-col gap-1">
          <label
            class="text-xs font-medium text-surface-600-400"
            for="upload-appname">App name</label
          >
          <input
            id="upload-appname"
            type="text"
            class="input text-sm"
            placeholder="MyApp"
            bind:value={appName}
          />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label
            class="text-xs font-medium text-surface-600-400"
            for="upload-version">Version</label
          >
          <input
            id="upload-version"
            type="text"
            class="input text-sm"
            placeholder="1.0.0"
            bind:value={version}
          />
        </div>
      </div>

      <div class="flex flex-col gap-1">
        <label
          class="text-xs font-medium text-surface-600-400"
          for="upload-notes">Build notes</label
        >
        <textarea
          id="upload-notes"
          class="input text-sm min-h-[80px] resize-none"
          placeholder="Enter build notes or description..."
          bind:value={buildNotes}
        />
      </div>
    </div>

    <!-- Command Preview -->
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
          Select packages and fill in required fields to see preview
        </div>
      {:else}
        <div class="flex flex-col gap-3">
          {#each commandPreviews as { pkg, command }}
            {@const Icon = getPlatformIcon(pkg.platform)}
            <div class="flex flex-col gap-1">
              <div
                class="text-xs font-medium text-surface-600-400 flex items-center justify-between"
              >
                <div class="flex items-center gap-2">
                  <Icon size={12} />
                  <span>{pkg.name}</span>
                  <span class="text-surface-500-400"
                    >({pkg.platform} {pkg.buildConfig})</span
                  >
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

    <UploadOutputPanel
      {selectedPackages}
      {availablePackages}
      {uploadStatuses}
      {uploadProgress}
      {isUploading}
      {outputLines}
      bind:outputRef
    />
  </div>

  <!-- Footer Actions -->
  <div
    class="border-t border-surface-200-800 p-4 flex items-center justify-end gap-3 bg-surface-50-950"
  >
    <button
      class="btn preset-tonal flex items-center gap-2"
      onclick={resetToDefaults}
      disabled={isUploading}
      title="Reset all upload settings to defaults"
    >
      <RotateCcw size={16} />
      Reset
    </button>

    {#if isUploading}
      <button
        class="btn preset-filled-error-500 flex items-center gap-2"
        onclick={cancelUpload}
      >
        <Square size={16} />
        Cancel upload
      </button>
    {:else}
      <button
        class="btn preset-filled-primary-500 flex items-center gap-2"
        onclick={runUpload}
        disabled={selectedPackages.length === 0 ||
          !username ||
          !appName ||
          !version ||
          !isEndpointConfigured}
      >
        <Upload size={16} />
        Upload {selectedPackages.length > 0
          ? `(${selectedPackages.length})`
          : ""}
      </button>
    {/if}
  </div>
</div>
