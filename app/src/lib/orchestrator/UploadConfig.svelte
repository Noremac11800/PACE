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
    Smartphone,
    Monitor,
    Apple,
    Package,
    Check,
    X,
    Loader,
  } from "@lucide/svelte";
  import { readDir } from "@tauri-apps/plugin-fs";
  import {
    settings,
    DEFAULT_UPLOAD_TAB_SETTINGS,
    type UploadTabSettings,
  } from "$lib/settings.svelte";
  import { saveSettings } from "$lib/app-init";
  import { configStore } from "$lib/config-store.svelte";

  type Platform = "ios" | "android" | "windows";
  type BuildConfig = "Debug" | "Release";

  interface PackageFile {
    name: string;
    path: string;
    platform: Platform;
    buildConfig: BuildConfig;
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

  // Derived projects list from active config
  const projects = $derived(configStore.activeConfig?.projects ?? []);
  const repodir = $derived(configStore.activeConfig?.repodir);

  // UI State
  let isUploading = $state(false);
  let currentProcess: any = $state(null);
  let outputLines: { type: "out" | "err"; text: string }[] = $state([]);
  let outputRef: HTMLDivElement | null = null;
  let showOutput = $state(true);
  let availablePackages: PackageFile[] = $state([]);
  let scanningPackages = $state(false);

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
    console.log("scanForPackages called:", { selectedProject, repodir });
    if (!selectedProject || !repodir) {
      console.log("Missing project or repodir, skipping scan");
      return;
    }

    // Find the project and get its csproj_path
    const project = projects.find((p) => p.name === selectedProject);
    if (!project?.csproj_path) {
      console.log("No csproj_path found for project:", selectedProject);
      return;
    }

    scanningPackages = true;
    const packages: PackageFile[] = [];

    // Get the directory containing the .csproj file
    const csprojDir = project.csproj_path.substring(
      0,
      project.csproj_path.lastIndexOf("/"),
    );
    const projectPath = `${repodir}/${selectedProject}/${csprojDir}`;
    console.log("Project path:", projectPath);
    console.log(
      "csproj_path:",
      project.csproj_path,
      "-> csprojDir:",
      csprojDir,
    );

    // Recursive function to search directories for package files
    async function searchDirectory(
      dirPath: string,
      platform: Platform,
      buildConfig: BuildConfig,
    ) {
      try {
        console.log("Searching directory:", dirPath);
        const entries = await readDir(dirPath);
        console.log(`Found ${entries.length} entries in ${dirPath}`);
        for (const entry of entries) {
          const entryPath = `${dirPath}/${entry.name}`;
          if (entry.isFile) {
            const name = entry.name?.toLowerCase() || "";
            if (
              name.endsWith(".ipa") ||
              name.endsWith(".msix") ||
              name.endsWith(".aab") ||
              name.endsWith(".apk")
            ) {
              console.log("Found package:", entry.name, "at", entryPath);
              packages.push({
                name: entry.name!,
                path: entryPath,
                platform,
                buildConfig,
              });
            }
          } else if (entry.isDirectory) {
            // Recursively search subdirectories
            await searchDirectory(entryPath, platform, buildConfig);
          }
        }
      } catch (e) {
        console.log("Error reading directory:", dirPath, e);
        // Directory doesn't exist or can't be read, skip silently
      }
    }

    // Detect platform from directory name
    function detectPlatform(dirName: string): Platform | null {
      const lower = dirName.toLowerCase();
      if (lower.includes("ios")) return "ios";
      if (lower.includes("android")) return "android";
      if (lower.includes("windows") || lower.includes("win")) return "windows";
      return null;
    }

    // Search bin/Debug and bin/Release recursively
    const buildConfigs = ["Debug", "Release"] as const;

    for (const buildConfig of buildConfigs) {
      const basePath = `${projectPath}/bin/${buildConfig}`;
      console.log(`Checking ${buildConfig} path:`, basePath);

      try {
        const entries = await readDir(basePath);
        console.log(
          `Found ${entries.length} entries in ${basePath}:`,
          entries.map((e) => e.name),
        );
        for (const entry of entries) {
          if (entry.isDirectory) {
            const platform = detectPlatform(entry.name);
            console.log(`Entry ${entry.name} -> platform: ${platform}`);
            if (platform) {
              const platformPath = `${basePath}/${entry.name}`;
              console.log(`Starting recursive search in:`, platformPath);
              await searchDirectory(platformPath, platform, buildConfig);
            }
          }
        }
      } catch (e) {
        console.log(`Error reading ${basePath}:`, e);
        // bin/Debug or bin/Release doesn't exist, skip
      }
    }

    availablePackages = packages.sort((a, b) => {
      // Sort by build config (Release first), then platform
      if (a.buildConfig !== b.buildConfig) {
        return a.buildConfig === "Release" ? -1 : 1;
      }
      return a.platform.localeCompare(b.platform);
    });

    console.log(`Scan complete. Found ${packages.length} packages.`);

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

  function getPlatformIcon(platform: Platform) {
    switch (platform) {
      case "ios":
        return Apple;
      case "android":
        return Smartphone;
      case "windows":
        return Monitor;
    }
  }

  function getApiPlatform(platform: Platform): string {
    switch (platform) {
      case "ios":
        return "iOS";
      case "android":
        return "Android";
      case "windows":
        return "Windows";
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
    addLine("Upload cancelled", "err");
  }

  async function runUpload() {
    if (
      isUploading ||
      selectedPackages.length === 0 ||
      !username ||
      !appName ||
      !version
    )
      return;

    resetOutput();
    isUploading = true;

    for (const packagePath of selectedPackages) {
      const pkg = availablePackages.find((p) => p.path === packagePath);
      if (!pkg) continue;

      const success = await uploadPackage(pkg);
      if (!success) {
        addLine(`Failed to upload ${pkg.name}`, "err");
      }
    }

    isUploading = false;
    currentProcess = null;
  }

  async function uploadPackage(pkg: PackageFile): Promise<boolean> {
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
    ];

    if (buildNotes) {
      paceArgs.push("--build-description", buildNotes);
    }

    return new Promise((resolve) => {
      try {
        const cmd = Command.create("pace", paceArgs);

        cmd.stdout.on("data", (data: string) => {
          addLine(data, "out");
        });

        cmd.stderr.on("data", (data: string) => {
          addLine(data, "err");
        });

        cmd.on("close", (payload: { code: number | null }) => {
          if (payload.code === 0) {
            addLine(`✓ Successfully uploaded ${pkg.name}`, "out");
          } else {
            addLine(
              `✗ Failed to upload ${pkg.name} (exit code: ${payload.code})`,
              "err",
            );
          }
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

  const commandPreview = $derived.by(() => {
    if (selectedPackages.length === 0) return "Select packages to see preview";
    if (!username) return "Enter username to see preview";
    if (!appName) return "Enter app name to see preview";
    if (!version) return "Enter version to see preview";

    const pkg = availablePackages.find((p) => p.path === selectedPackages[0]);
    if (!pkg) return "No package selected";

    const apiPlatform = getApiPlatform(pkg.platform);
    let cmd = `pace upload "${pkg.path}" --username "${username}" --app-name "${appName}" --platform ${apiPlatform} --release-type ${pkg.buildConfig} --version "${version}"`;
    if (buildNotes) {
      cmd += ` --build-description "${buildNotes}"`;
    }
    return cmd;
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
        {#if scanningPackages}
          <span class="text-xs text-surface-500-400 ml-auto">Scanning...</span>
        {/if}
      </div>

      {#if !selectedProject}
        <div class="text-sm text-surface-500-400">
          Select a project to see available packages.
        </div>
      {:else if availablePackages.length === 0}
        <div class="text-sm text-surface-500-400">
          No .ipa, .msix, .aab, or .apk files found in Debug/Release
          directories.
        </div>
      {:else}
        <div class="flex flex-col gap-2">
          {#each availablePackages as pkg}
            {@const Icon = getPlatformIcon(pkg.platform)}
            {@const isSelected = selectedPackages.includes(pkg.path)}
            <button
              type="button"
              onclick={() => togglePackage(pkg.path)}
              class="flex items-center gap-3 p-3 rounded border transition-colors text-left {isSelected
                ? 'bg-primary-500/10 border-primary-500'
                : 'bg-surface-100-900 border-surface-300-700 hover:border-primary-500/50'}"
            >
              <div
                class="flex items-center justify-center w-5 h-5 rounded border {isSelected
                  ? 'bg-primary-500 border-primary-500'
                  : 'border-surface-500'}"
              >
                {#if isSelected}
                  <Check size={12} class="text-white" />
                {/if}
              </div>
              <Icon
                size={16}
                class={isSelected ? "text-primary-500" : "text-surface-500-400"}
              />
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-surface-900-100 truncate">
                  {pkg.name}
                </div>
                <div class="text-xs text-surface-500-400">
                  {getApiPlatform(pkg.platform)} • {pkg.buildConfig}
                </div>
              </div>
            </button>
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
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <Terminal size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100">Command preview</span>
      </div>
      <div class="bg-surface-900-100 rounded p-3 overflow-x-auto">
        <code class="text-xs text-surface-50-950 font-mono whitespace-pre"
          >{commandPreview}</code
        >
      </div>
    </div>

    <!-- Output -->
    {#if showOutput}
      <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <Terminal size={18} class="text-primary-500" />
          <span class="font-semibold text-surface-900-100">Output</span>
          {#if isUploading}
            <Loader size={14} class="animate-spin ml-2 text-primary-500" />
          {/if}
        </div>
        <div
          bind:this={outputRef}
          class="bg-surface-900-100 rounded p-3 h-48 overflow-y-auto font-mono text-xs flex flex-col gap-1"
        >
          {#if outputLines.length === 0}
            <span class="text-surface-500-400 italic"
              >Upload output will appear here...</span
            >
          {:else}
            {#each outputLines as line}
              <span
                class={line.type === "err"
                  ? "text-error-500"
                  : "text-surface-50-950"}
              >
                {line.text}
              </span>
            {/each}
          {/if}
        </div>
      </div>
    {/if}
  </div>

  <!-- Footer Actions -->
  <div
    class="border-t border-surface-200-800 p-4 flex items-center justify-between gap-4 bg-surface-50-950"
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
          !version}
      >
        <Upload size={16} />
        Upload {selectedPackages.length > 0
          ? `(${selectedPackages.length})`
          : ""}
      </button>
    {/if}
  </div>
</div>
