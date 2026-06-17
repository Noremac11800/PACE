<script lang="ts">
  import { tick, onMount, untrack } from "svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import {
    Hammer,
    Square,
    ChevronDown,
    Terminal,
    FolderOpen,
    RotateCcw,
  } from "@lucide/svelte";
  import { open } from "@tauri-apps/plugin-dialog";
  import { configStore, paceArgs } from "$lib/config-store.svelte";
  import { settings, DEFAULT_BUILD_TAB_SETTINGS } from "$lib/settings.svelte";
  import { saveSettings } from "$lib/app-init";
  import { setBuildingStatus } from "$lib/orchestrator/command-status.svelte";
  import CopyButton from "$lib/components/CopyButton.svelte";

  const FRAMEWORKS = [
    { id: "net10.0-android", label: "Android" },
    { id: "net10.0-ios", label: "iOS" },
    { id: "net10.0-maccatalyst", label: "macOS Catalyst" },
    { id: "net10.0-windows10.0.20348.0", label: "Windows" },
  ] as const;

  type Framework = (typeof FRAMEWORKS)[number]["id"];

  let fromProject = $state<string>(settings.buildTab.fromProject);
  let toProject = $state<string>(settings.buildTab.toProject);
  let buildConfig = $state<"Debug" | "Release">(settings.buildTab.buildConfig);
  let selectedFramework = $state<Framework | "">(
    (settings.buildTab.selectedFrameworks[0] as Framework) ?? "",
  );
  let noRestore = $state<boolean>(settings.buildTab.noRestore);
  let cleanBeforeBuild = $state<boolean>(
    settings.buildTab.cleanBeforeBuild ?? false,
  );

  let msbuildProps = $state<Record<string, string>>({
    ...settings.buildTab.msbuildProps,
  });

  const buildProps = $derived(configStore.activeConfig?.build_props ?? []);

  let settingsInitialized = $state(false);

  onMount(() => {
    settingsInitialized = true;
  });

  $effect(() => {
    if (!settingsInitialized) return;
    const snapshot = {
      fromProject,
      toProject,
      buildConfig,
      selectedFrameworks: selectedFramework ? [selectedFramework] : [],
      msbuildProps: { ...msbuildProps },
      noRestore,
      cleanBeforeBuild,
    };
    let cancelled = false;
    untrack(() => {
      settings.buildTab = snapshot;
      saveSettings().catch((e) => {
        if (!cancelled) console.error("Failed to save build settings:", e);
      });
    });
    return () => {
      cancelled = true;
    };
  });

  function resetToDefaults() {
    const d = DEFAULT_BUILD_TAB_SETTINGS;
    fromProject = d.fromProject;
    toProject = d.toProject;
    buildConfig = d.buildConfig;
    selectedFramework = "";
    msbuildProps = {};
    noRestore = d.noRestore;
    cleanBeforeBuild = d.cleanBeforeBuild;
  }

  async function pickPath(propName: string) {
    const selected = await open({ directory: true, multiple: false });
    if (selected && typeof selected === "string") {
      msbuildProps = { ...msbuildProps, [propName]: selected };
    }
  }

  let isRunning = $state(false);
  let progress = $state(0);
  let progressLabel = $state("");
  let outputLines = $state<{ text: string; type: "out" | "err" }[]>([]);
  let currentProcess: Awaited<
    ReturnType<ReturnType<typeof Command.create>["spawn"]>
  > | null = null;
  let outputRef: HTMLDivElement | undefined;

  const projects = $derived(configStore.activeConfig?.projects ?? []);

  const filteredProjects = $derived.by(() => {
    const from = fromProject || null;
    const to = toProject || null;
    if (!from && !to) return projects;

    // Build reverse dependency graph: dep -> set of projects that depend on it
    const dependents = new Map<string, Set<string>>();
    for (const p of projects) dependents.set(p.name, new Set());
    for (const p of projects)
      for (const dep of p.depends_on) dependents.get(dep)?.add(p.name);

    // Build forward dependency graph: project -> what it depends on
    const dependencies = new Map<string, Set<string>>();
    for (const p of projects) dependencies.set(p.name, new Set(p.depends_on));

    function canReachDownstream(start: string, end: string): boolean {
      if (start === end) return true;
      const visited = new Set<string>();
      const queue = [start];
      while (queue.length) {
        const cur = queue.shift()!;
        if (cur === end) return true;
        if (!visited.has(cur)) {
          visited.add(cur);
          for (const n of dependents.get(cur) ?? [])
            if (!visited.has(n)) queue.push(n);
        }
      }
      return false;
    }

    function canReachUpstream(start: string, end: string): boolean {
      if (start === end) return true;
      const visited = new Set<string>();
      const queue = [start];
      while (queue.length) {
        const cur = queue.shift()!;
        if (cur === end) return true;
        if (!visited.has(cur)) {
          visited.add(cur);
          for (const n of dependencies.get(cur) ?? [])
            if (!visited.has(n)) queue.push(n);
        }
      }
      return false;
    }

    let included: Set<string>;
    if (!from && to) {
      // --to only: target + all its transitive dependencies
      included = new Set<string>();
      for (const p of projects)
        if (canReachUpstream(to, p.name)) included.add(p.name);
      const queue = [...included];
      while (queue.length) {
        const cur = queue.shift()!;
        for (const dep of dependencies.get(cur) ?? []) {
          if (!included.has(dep)) {
            included.add(dep);
            queue.push(dep);
          }
        }
      }
    } else if (from && !to) {
      // --from only: source + all downstream dependents
      included = new Set<string>();
      for (const p of projects)
        if (canReachDownstream(from, p.name)) included.add(p.name);
    } else {
      // both: projects on any path from -> to
      included = new Set<string>();
      for (const p of projects)
        if (
          canReachDownstream(from!, p.name) &&
          canReachDownstream(p.name, to!)
        )
          included.add(p.name);
    }

    return projects.filter((p) => included.has(p.name));
  });

  const cleanCommandPreview = $derived.by(() => {
    const parts: string[] = ["pace"];
    if (fromProject) parts.push("--from", fromProject);
    if (toProject) parts.push("--to", toProject);
    parts.push("clean", "--projects");
    return parts.join(" ");
  });

  const commandPreview = $derived.by(() => {
    const parts: string[] = ["pace"];
    if (fromProject) parts.push("--from", fromProject);
    if (toProject) parts.push("--to", toProject);
    parts.push("dotnet", "build");
    parts.push("-c", buildConfig);
    if (selectedFramework) parts.push("-f", selectedFramework);
    if (noRestore) parts.push("--no-restore");
    for (const prop of buildProps) {
      const val = msbuildProps[prop.name];
      const effective = val !== undefined ? val : String(prop.default);
      if (effective !== "" && effective !== String(prop.default))
        parts.push(`-p:${prop.name}=${effective}`);
    }
    const buildCommand = parts.join(" ");
    return cleanBeforeBuild
      ? `${cleanCommandPreview}\n${buildCommand}`
      : buildCommand;
  });

  function addLine(text: string, type: "out" | "err") {
    outputLines = [...outputLines, { text, type }];
    tick().then(() => {
      if (outputRef) outputRef.scrollTop = outputRef.scrollHeight;
    });
  }

  let projectsBuilt = $state(0);
  let projectsTotal = $state(0);
  let elapsedSeconds = $state(0);
  let timerInterval: ReturnType<typeof setInterval> | null = null;

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

  function resetOutput() {
    outputLines = [];
    progress = 0;
    progressLabel = "";
    projectsBuilt = 0;
    projectsTotal = 0;
    elapsedSeconds = 0;
  }

  function parseProgress(chunk: string) {
    for (const raw of chunk.split("\n")) {
      const line = raw.replace(/\r$/, "");

      if (/Build succeeded/i.test(line)) {
        projectsBuilt = projectsTotal || projectsBuilt;
        progress = 100;
        progressLabel = "Build succeeded";
      } else if (/Build FAILED/i.test(line) || /Build failed/i.test(line)) {
        progress = 100;
        progressLabel = "Build failed";
      } else if (/^Creating solution/i.test(line)) {
        progress = Math.max(progress, 5);
        progressLabel = "Creating solution...";
      } else if (/^Adding projects/i.test(line)) {
        progress = Math.max(progress, 10);
        progressLabel = "Adding projects to solution...";
      } else if (/^Building solution/i.test(line)) {
        progress = Math.max(progress, 15);
        progressLabel = "Building solution...";
        projectsTotal = filteredProjects.length;
      } else if (line.includes(" -> ")) {
        // "ProjectName -> C:\path\to\output.dll"
        projectsBuilt += 1;
        const total = projectsTotal || filteredProjects.length;
        if (total > 0) {
          progress = Math.max(
            progress,
            Math.min(15 + Math.round((projectsBuilt / total) * 82), 97),
          );
        }
        const projectName = line.split(" -> ")[0].trim();
        progressLabel = `Built ${projectName}`;
      }
    }
  }

  async function runBuild() {
    if (isRunning) return;
    resetOutput();
    startTimer();
    isRunning = true;
    setBuildingStatus(true);
    progress = 0;
    progressLabel = "Starting...";

    const dotnetPassthrough: string[] = ["build", "-c", buildConfig];
    if (selectedFramework) dotnetPassthrough.push("-f", selectedFramework);
    if (noRestore) dotnetPassthrough.push("--no-restore");
    for (const prop of buildProps) {
      const val = msbuildProps[prop.name];
      const effective = val !== undefined ? val : String(prop.default);
      if (effective !== "" && effective !== String(prop.default))
        dotnetPassthrough.push(`-p:${prop.name}=${effective}`);
    }

    const extraPaceArgs: string[] = [];
    if (fromProject) extraPaceArgs.push("--from", fromProject);
    if (toProject) extraPaceArgs.push("--to", toProject);

    const allArgs = await paceArgs([
      ...extraPaceArgs,
      "dotnet",
      ...dotnetPassthrough,
    ]);

    try {
      if (cleanBeforeBuild) {
        progressLabel = "Cleaning bin/ and obj/ directories...";
        const cleanArgs = await paceArgs([
          ...extraPaceArgs,
          "clean",
          "--projects",
        ]);
        const cleanCmd = Command.create("pace", cleanArgs);
        cleanCmd.stdout.on("data", (data: string) => addLine(data, "out"));
        cleanCmd.stderr.on("data", (data: string) => addLine(data, "err"));
        const cleanChild = await cleanCmd.spawn();
        currentProcess = cleanChild;
        const cleanCode = await new Promise<number | null>((resolve) => {
          cleanCmd.on("close", (payload: { code: number | null }) =>
            resolve(payload.code),
          );
        });
        currentProcess = null;
        if (cleanCode !== 0) {
          addLine(`Clean failed with exit code ${cleanCode}.`, "err");
          progressLabel = "Clean failed";
          progress = 100;
          return;
        }
        if (!isRunning) return; // cancelled during clean
      }

      const cmd = Command.create("pace", allArgs);
      const child = await cmd.spawn();
      currentProcess = child;

      cmd.stdout.on("data", (data: string) => {
        addLine(data, "out");
        parseProgress(data);
      });

      cmd.stderr.on("data", (data: string) => {
        addLine(data, "err");
        parseProgress(data);
      });

      await new Promise<void>((resolve) => {
        cmd.on("close", () => resolve());
      });
    } catch (e) {
      addLine(`Error: ${e instanceof Error ? e.message : String(e)}`, "err");
      progressLabel = "Error";
      progress = 100;
    } finally {
      stopTimer();
      isRunning = false;
      setBuildingStatus(false);
      currentProcess = null;
    }
  }

  function cancelBuild() {
    currentProcess?.kill();
    stopTimer();
    addLine("Build cancelled.", "err");
    progressLabel = "Cancelled";
    progress = 100;
    isRunning = false;
    setBuildingStatus(false);
    currentProcess = null;
  }

  const progressBarColor = $derived.by(() => {
    if (/failed|cancelled|error/i.test(progressLabel)) return "bg-error-500";
    if (/succeeded/i.test(progressLabel)) return "bg-success-500";
    return "bg-primary-500";
  });
</script>

<div class="h-full flex flex-col">
  <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
    <!-- Configuration -->
    <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <Hammer size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100"
          >Build Configuration</span
        >
      </div>

      <!-- From / To project pickers -->
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label
            class="text-xs font-medium text-surface-600-400"
            for="from-picker"
          >
            Build from
          </label>
          <div class="relative">
            <select
              id="from-picker"
              bind:value={fromProject}
              class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-2 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
              style="background-image:none"
            >
              <option value="">— None (all projects) —</option>
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

        <div class="flex flex-col gap-1">
          <label
            class="text-xs font-medium text-surface-600-400"
            for="to-picker"
          >
            Build to
          </label>
          <div class="relative">
            <select
              id="to-picker"
              bind:value={toProject}
              class="w-full appearance-none bg-surface-100-900 border border-surface-300-700 rounded px-3 py-2 pr-8 text-sm text-surface-900-100 focus:outline-none focus:border-primary-500 transition-colors"
              style="background-image:none"
            >
              <option value="">— None (all projects) —</option>
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
      </div>

      <!-- Build config radio -->
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

      <!-- Framework single-select -->
      <div class="flex flex-col gap-1">
        <span class="text-xs font-medium text-surface-600-400"
          >Target Framework</span
        >
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            onclick={() => (selectedFramework = "")}
            class="px-3 py-1.5 rounded text-xs font-medium border transition-colors {selectedFramework ===
            ''
              ? 'bg-primary-500 border-primary-500 text-white'
              : 'bg-surface-100-900 border-surface-300-700 text-surface-700-300 hover:border-primary-500 hover:text-primary-500'}"
          >
            All available
          </button>
          {#each FRAMEWORKS as fw}
            <button
              type="button"
              onclick={() => (selectedFramework = fw.id)}
              class="px-3 py-1.5 rounded text-xs font-medium border transition-colors {selectedFramework ===
              fw.id
                ? 'bg-primary-500 border-primary-500 text-white'
                : 'bg-surface-100-900 border-surface-300-700 text-surface-700-300 hover:border-primary-500 hover:text-primary-500'}"
            >
              {fw.label}
            </button>
          {/each}
        </div>
      </div>

      <!-- No Restore toggle -->
      <label class="flex items-center gap-3 cursor-pointer group">
        <div
          role="checkbox"
          aria-checked={noRestore}
          tabindex="0"
          class="w-9 h-5 rounded-full transition-colors flex items-center px-0.5 shrink-0 {noRestore
            ? 'bg-primary-500'
            : 'bg-surface-300-700'}"
          onclick={() => (noRestore = !noRestore)}
          onkeydown={(e) => e.key === " " && (noRestore = !noRestore)}
        >
          <div
            class="w-4 h-4 rounded-full bg-white shadow transition-transform {noRestore
              ? 'translate-x-4'
              : 'translate-x-0'}"
          ></div>
        </div>
        <span
          class="text-sm text-surface-900-100 group-hover:text-primary-500 transition-colors"
        >
          Skip restore (--no-restore)
        </span>
      </label>

      <!-- Clean before build toggle -->
      <label class="flex items-center gap-3 cursor-pointer group">
        <div
          role="checkbox"
          aria-checked={cleanBeforeBuild}
          tabindex="0"
          class="w-9 h-5 rounded-full transition-colors flex items-center px-0.5 shrink-0 {cleanBeforeBuild
            ? 'bg-primary-500'
            : 'bg-surface-300-700'}"
          onclick={() => (cleanBeforeBuild = !cleanBeforeBuild)}
          onkeydown={(e) =>
            e.key === " " && (cleanBeforeBuild = !cleanBeforeBuild)}
        >
          <div
            class="w-4 h-4 rounded-full bg-white shadow transition-transform {cleanBeforeBuild
              ? 'translate-x-4'
              : 'translate-x-0'}"
          ></div>
        </div>
        <span
          class="text-sm text-surface-900-100 group-hover:text-primary-500 transition-colors"
        >
          Clean bin/ and obj/ dirs before build
        </span>
      </label>
    </div>

    <!-- MSBuild Properties -->
    {#if buildProps.length > 0}
      <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
        <span class="font-semibold text-surface-900-100"
          >MSBuild Properties</span
        >

        {#each buildProps as prop}
          {#if prop.datatype === "boolean"}
            {@const val =
              msbuildProps[prop.name] !== undefined
                ? msbuildProps[prop.name] === "true"
                : prop.default === true || prop.default === "true"}
            <label
              class="flex items-center gap-3 cursor-pointer group"
              for="msbuild-{prop.name}"
            >
              <div
                role="checkbox"
                aria-checked={val}
                tabindex="0"
                id="msbuild-{prop.name}"
                class="w-9 h-5 rounded-full transition-colors flex items-center px-0.5 shrink-0 {val
                  ? 'bg-primary-500'
                  : 'bg-surface-300-700'}"
                onclick={() =>
                  (msbuildProps = {
                    ...msbuildProps,
                    [prop.name]: val ? "false" : "true",
                  })}
                onkeydown={(e) =>
                  e.key === " " &&
                  (msbuildProps = {
                    ...msbuildProps,
                    [prop.name]: val ? "false" : "true",
                  })}
              >
                <div
                  class="w-4 h-4 rounded-full bg-white shadow transition-transform {val
                    ? 'translate-x-4'
                    : 'translate-x-0'}"
                ></div>
              </div>
              <span
                class="text-sm font-mono text-surface-900-100 group-hover:text-primary-500 transition-colors"
                >{prop.name}</span
              >
              <span
                class="text-xs ml-auto {val
                  ? 'text-primary-400'
                  : 'text-surface-500-400'}">{val ? "true" : "false"}</span
              >
            </label>
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

    <!-- Command preview -->
    <div class="card bg-surface-50-950 p-4">
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="flex items-center gap-2">
          <Terminal size={16} class="text-primary-500 shrink-0" />
          <span
            class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
            >Command Preview</span
          >
        </div>
        <CopyButton text={commandPreview} />
      </div>
      <code
        class="block text-sm font-mono bg-surface-200-800 px-3 py-2 rounded break-all whitespace-pre-wrap text-surface-900-100"
      >
        {commandPreview}
      </code>
    </div>

    <!-- Progress -->
    {#if isRunning || progress > 0}
      {@const total = projectsTotal || filteredProjects.length}
      <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
        <!-- Label + project counter + timer -->
        <div class="flex items-center justify-between gap-2 text-xs">
          <span class="text-surface-600-400 truncate">{progressLabel}</span>
          <span
            class="font-mono text-surface-600-400 shrink-0 flex items-center gap-2"
          >
            {#if total > 0 && progress > 0 && progress < 100}
              <span>{projectsBuilt} / {total} projects</span>
            {:else}
              <span>{progress}%</span>
            {/if}
            <span class="text-surface-400-500">·</span>
            <span>{formatElapsed(elapsedSeconds)}</span>
          </span>
        </div>

        <!-- Progress bar -->
        <div class="w-full h-2 bg-surface-200-800 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-300 {progressBarColor}"
            style="width: {progress}%"
          ></div>
        </div>

        <!-- Per-project segment strip (when we know the total) -->
        {#if total > 0 && total <= 50 && progress > 0 && progress < 100}
          <div class="flex gap-0.5">
            {#each { length: total } as _, i}
              <div
                class="h-1.5 flex-1 rounded-full transition-colors duration-200 {i <
                projectsBuilt
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
    class="shrink-0 flex items-center justify-end gap-3 px-4 py-3 border-t border-surface-200-800 bg-surface-50-950"
  >
    <button
      class="btn preset-tonal flex items-center gap-2"
      onclick={resetToDefaults}
      disabled={isRunning}
      title="Reset all build settings to defaults"
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
        Cancel Build
      </button>
    {:else}
      <button
        class="btn preset-filled-primary-500 flex items-center gap-2"
        onclick={runBuild}
      >
        <Hammer size={16} />
        Build
      </button>
    {/if}
  </div>
</div>
