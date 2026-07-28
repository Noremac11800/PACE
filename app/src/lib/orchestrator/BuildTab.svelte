<script lang="ts">
  import { tick, onMount, untrack } from "svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import { Hammer, Square, RotateCcw } from "@lucide/svelte";
  import { open } from "@tauri-apps/plugin-dialog";
  import {
    configStore,
    paceArgs,
    paceCommandPreview,
  } from "$lib/state/config-store.svelte";
  import {
    settings,
    DEFAULT_BUILD_TAB_SETTINGS,
  } from "$lib/state/settings.svelte";
  import { saveSettings } from "$lib/utils/app-init";
  import { setBuildingStatus } from "$lib/orchestrator/command-status.svelte";
  import { type Framework } from "$lib/orchestrator/build-tab/frameworks";
  import BuildOptionsForm from "$lib/orchestrator/build-tab/BuildOptionsForm.svelte";
  import BuildOutputPanel from "$lib/orchestrator/build-tab/BuildOutputPanel.svelte";

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
  let summarizeWarnings = $state<boolean>(
    settings.buildTab.summarizeWarnings ?? false,
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
      summarizeWarnings,
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
    summarizeWarnings = d.summarizeWarnings;
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
  let outputRef = $state<HTMLDivElement>();

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

  // Async command previews using $state + $effect
  let cleanCommandPreview = $state("pace clean --projects");
  let commandPreview = $state("pace dotnet build");

  $effect(() => {
    const cleanParts: string[] = [];
    if (fromProject) cleanParts.push("--from", fromProject);
    if (toProject) cleanParts.push("--to", toProject);
    cleanParts.push("clean", "--projects");
    // Capture deps
    const deps = { fromProject, toProject };
    paceCommandPreview(cleanParts).then((preview) => {
      cleanCommandPreview = preview;
    });
  });

  $effect(() => {
    const parts: string[] = [];
    if (fromProject) parts.push("--from", fromProject);
    if (toProject) parts.push("--to", toProject);
    parts.push("dotnet");
    if (summarizeWarnings) parts.push("--summarize-warnings");
    parts.push("build");
    parts.push("-c", buildConfig);
    if (selectedFramework) parts.push("-f", selectedFramework);
    if (noRestore) parts.push("--no-restore");
    for (const prop of buildProps) {
      const val = msbuildProps[prop.name];
      const effective = val !== undefined ? val : String(prop.default);
      if (effective !== "" && effective !== String(prop.default))
        parts.push(`-p:${prop.name}=${effective}`);
    }
    // Capture deps
    const deps = {
      fromProject,
      toProject,
      buildConfig,
      selectedFramework,
      noRestore,
      buildProps: [...buildProps],
      msbuildProps: { ...msbuildProps },
      cleanBeforeBuild,
      summarizeWarnings,
    };
    paceCommandPreview(parts).then((preview) => {
      commandPreview = cleanBeforeBuild
        ? `${cleanCommandPreview}\n${preview}`
        : preview;
    });
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

    const dotnetPassthrough: string[] = [
      ...(summarizeWarnings ? ["--summarize-warnings"] : []),
      "build",
      "-c",
      buildConfig,
    ];
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
    <BuildOptionsForm
      {projects}
      {buildProps}
      bind:fromProject
      bind:toProject
      bind:buildConfig
      bind:selectedFramework
      bind:noRestore
      bind:cleanBeforeBuild
      bind:summarizeWarnings
      bind:msbuildProps
      onpickPath={pickPath}
    />

    <BuildOutputPanel
      {commandPreview}
      {isRunning}
      {progress}
      {progressLabel}
      {progressBarColor}
      {projectsBuilt}
      {projectsTotal}
      filteredProjectsCount={filteredProjects.length}
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
