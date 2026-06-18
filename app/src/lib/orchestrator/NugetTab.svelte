<script lang="ts">
  import { onMount } from "svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import { readDir } from "@tauri-apps/plugin-fs";
  import { homeDir, join } from "@tauri-apps/api/path";
  import { open } from "@tauri-apps/plugin-dialog";
  import { openPath } from "@tauri-apps/plugin-opener";
  import {
    configStore,
    saveConfig,
    paceArgs,
  } from "$lib/state/config-store.svelte";
  import type {
    NugetSource,
    CachedPackage,
  } from "$lib/orchestrator/nuget-tab/types.ts";
  import NugetSourcesPanel from "$lib/orchestrator/nuget-tab/NugetSourcesPanel.svelte";
  import DefaultCachePanel from "$lib/orchestrator/nuget-tab/DefaultCachePanel.svelte";
  import CustomCachePanel from "$lib/orchestrator/nuget-tab/CustomCachePanel.svelte";

  let sources = $state<NugetSource[]>([]);
  let sourcesLoading = $state(false);
  let sourcesError = $state<string | null>(null);

  let defaultCachePackages = $state<CachedPackage[]>([]);
  let defaultCacheLoading = $state(false);
  let defaultCacheError = $state<string | null>(null);
  let defaultCachePath = $state<string>("");

  let customCachePath = $state<string>("");
  let customCachePackages = $state<CachedPackage[]>([]);
  let customCacheLoading = $state(false);
  let customCacheError = $state<string | null>(null);

  // Cleaning state
  let defaultCacheCleaning = $state(false);
  let customCacheCleaning = $state(false);

  let nugetConfigDir = $state<string>("");

  let localSourcePackages = $state<Map<string, CachedPackage[]>>(new Map());
  let localSourceLoading = $state<Set<string>>(new Set());
  let localSourceErrors = $state<Map<string, string>>(new Map());

  const projects = $derived(configStore.activeConfig?.projects ?? []);

  const configNugetCachePath = $derived(
    configStore.activeConfig?.nuget_cache_path ?? "",
  );

  $effect(() => {
    const path = configNugetCachePath;
    customCachePackages = [];
    customCacheError = null;
    customCachePath = path;
    if (path) {
      loadCustomCachePackages();
    }
  });

  const csprojStems = $derived(
    new Set(
      projects.map((p) => {
        const filename =
          p.csproj_path.replace(/\\/g, "/").split("/").pop() ?? "";
        return filename.replace(/\.csproj$/i, "").toLowerCase();
      }),
    ),
  );

  function isLocalSource(url: string): boolean {
    return !url.startsWith("http://") && !url.startsWith("https://");
  }

  async function readLocalSourceDir(dirPath: string): Promise<CachedPackage[]> {
    const entries = await readDir(dirPath);
    const byName = new Map<string, string[]>();
    for (const entry of entries) {
      if (!entry.name || !entry.name.toLowerCase().endsWith(".nupkg")) continue;
      // Filename: PackageName.Version.nupkg
      // Version segments are purely numeric/pre-release: split on last segment
      // that looks like a semver start (digit)
      const stem = entry.name.slice(0, -".nupkg".length);
      // Split on dots, find the first segment starting with a digit —
      // that marks the start of the version (e.g. "2" in "Company.Toolkit.Lib.Core.2.1.0-alpha.15")
      const parts = stem.split(".");
      const versionIdx = parts.findIndex((p) => /^\d/.test(p));
      if (versionIdx <= 0) continue;
      const name = parts.slice(0, versionIdx).join(".");
      const version = parts.slice(versionIdx).join(".");
      const existing = byName.get(name) ?? [];
      existing.push(version);
      byName.set(name, existing);
    }
    return Array.from(byName.entries())
      .map(([name, versions]) => ({ name, versions: versions.sort() }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  async function loadLocalSource(source: NugetSource) {
    const key = source.name;
    localSourceLoading = new Set([...localSourceLoading, key]);
    localSourceErrors = new Map(localSourceErrors);
    localSourceErrors.delete(key);
    try {
      const pkgs = await readLocalSourceDir(source.url);
      localSourcePackages = new Map([...localSourcePackages, [key, pkgs]]);
    } catch (e) {
      localSourceErrors = new Map([
        ...localSourceErrors,
        [key, e instanceof Error ? e.message : String(e)],
      ]);
    } finally {
      const next = new Set(localSourceLoading);
      next.delete(key);
      localSourceLoading = next;
    }
  }

  function matchesProject(pkgName: string): boolean {
    if (csprojStems.size === 0) return true;
    const lower = pkgName.toLowerCase();
    for (const stem of csprojStems) {
      if (
        lower === stem ||
        lower.startsWith(stem + ".") ||
        stem.startsWith(lower + ".")
      )
        return true;
    }
    return false;
  }

  const filteredDefaultPackages = $derived(
    defaultCachePackages.filter((p) => matchesProject(p.name)),
  );

  const filteredCustomPackages = $derived(
    customCachePackages.filter((p) => matchesProject(p.name)),
  );

  async function loadSources() {
    sourcesLoading = true;
    sourcesError = null;
    sources = [];
    localSourcePackages = new Map();
    localSourceErrors = new Map();
    try {
      const cmd = Command.create("dotnet", ["nuget", "list", "source"]);
      const result = await cmd.execute();
      const output = result.stdout || result.stderr || "";
      sources = parseNugetSources(output);
      for (const source of sources) {
        if (isLocalSource(source.url)) {
          loadLocalSource(source);
        }
      }
    } catch (e) {
      sourcesError = e instanceof Error ? e.message : String(e);
    } finally {
      sourcesLoading = false;
    }
  }

  function parseNugetSources(output: string): NugetSource[] {
    const parsed: NugetSource[] = [];
    const lines = output.split("\n").map((l) => l.trimEnd());
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // Lines look like:  "  1.  nuget.org [Enabled]"
      // followed by       "      https://api.nuget.org/v3/index.json"
      const headerMatch = line.match(
        /^\s+\d+\.\s+(.+?)\s+\[(Enabled|Disabled)\]/i,
      );
      if (headerMatch) {
        const name = headerMatch[1].trim();
        const enabled = headerMatch[2].toLowerCase() === "enabled";
        let url = "";
        if (i + 1 < lines.length) {
          url = lines[i + 1].trim();
          i++;
        }
        parsed.push({ name, url, enabled });
      }
    }
    return parsed;
  }

  async function loadDefaultCachePackages() {
    defaultCacheLoading = true;
    defaultCacheError = null;
    defaultCachePackages = [];
    try {
      const home = await homeDir();
      const cachePath = await join(home, ".nuget", "packages");
      defaultCachePath = cachePath;
      defaultCachePackages = await readCacheDir(cachePath);
    } catch (e) {
      defaultCacheError = e instanceof Error ? e.message : String(e);
    } finally {
      defaultCacheLoading = false;
    }
  }

  async function readCacheDir(cachePath: string): Promise<CachedPackage[]> {
    const entries = await readDir(cachePath);
    const packages: CachedPackage[] = [];
    for (const entry of entries) {
      if (!entry.name) continue;
      try {
        const versionEntries = await readDir(await join(cachePath, entry.name));
        const versions = versionEntries
          .filter((v) => v.name)
          .map((v) => v.name!);
        packages.push({ name: entry.name, versions });
      } catch {
        packages.push({ name: entry.name, versions: [] });
      }
    }
    return packages.sort((a, b) => a.name.localeCompare(b.name));
  }

  async function persistNugetCachePath(path: string) {
    if (!configStore.activeConfig || !configStore.activeConfigName) return;
    if ((configStore.activeConfig.nuget_cache_path ?? "") === path) return;
    const updated = {
      ...configStore.activeConfig,
      nuget_cache_path: path || undefined,
    };
    configStore.activeConfig = updated;
    await saveConfig(configStore.activeConfigName, updated);
  }

  async function pickCustomCachePath() {
    const selected = await open({ directory: true, multiple: false });
    if (selected && typeof selected === "string") {
      customCachePath = selected;
      await persistNugetCachePath(selected);
      await loadCustomCachePackages();
    }
  }

  async function loadCustomCachePackages() {
    if (!customCachePath) return;
    await persistNugetCachePath(customCachePath);
    customCacheLoading = true;
    customCacheError = null;
    customCachePackages = [];
    try {
      customCachePackages = await readLocalSourceDir(customCachePath);
    } catch (e) {
      customCacheError = e instanceof Error ? e.message : String(e);
    } finally {
      customCacheLoading = false;
    }
  }

  async function cleanDefaultCache() {
    if (defaultCacheCleaning) return;
    defaultCacheCleaning = true;
    defaultCacheError = null;
    try {
      const args = await paceArgs(["clean", "--cache"]);
      const cmd = Command.create("pace", args);
      const result = await cmd.execute();
      if (result.code !== 0) {
        defaultCacheError = result.stderr || `Exit code ${result.code}`;
      }
      await loadDefaultCachePackages();
    } catch (e) {
      defaultCacheError = e instanceof Error ? e.message : String(e);
      console.error("Failed to clean default cache:", e);
    } finally {
      defaultCacheCleaning = false;
    }
  }

  async function cleanCustomCache() {
    if (customCacheCleaning || !customCachePath) return;
    customCacheCleaning = true;
    customCacheError = null;
    try {
      const args = await paceArgs(["clean", "--custom-cache"]);
      const cmd = Command.create("pace", args);
      const result = await cmd.execute();
      if (result.code !== 0) {
        customCacheError = result.stderr || `Exit code ${result.code}`;
      }
      await loadCustomCachePackages();
    } catch (e) {
      customCacheError = e instanceof Error ? e.message : String(e);
      console.error("Failed to clean custom cache:", e);
    } finally {
      customCacheCleaning = false;
    }
  }

  onMount(async () => {
    loadSources();
    loadDefaultCachePackages();
    try {
      const cmd = Command.create("dotnet", ["nuget", "config", "paths"]);
      const result = await cmd.execute();
      const output = (result.stdout || result.stderr || "").trim();
      const firstLine = output
        .split("\n")
        .map((l) => l.trim())
        .find((l) => l.length > 0);
      if (firstLine) {
        // firstLine is the full path to NuGet.Config; take its parent directory
        const normalized = firstLine.replace(/\\/g, "/");
        nugetConfigDir = normalized.substring(0, normalized.lastIndexOf("/"));
      }
    } catch (e) {
      console.error("Failed to resolve NuGet config dir:", e);
    }
  });
</script>

<div class="flex flex-col gap-4">
  <NugetSourcesPanel
    {sources}
    loading={sourcesLoading}
    error={sourcesError}
    configDir={nugetConfigDir}
    onrefresh={loadSources}
    onopenConfig={() => openPath(nugetConfigDir)}
  />

  <DefaultCachePanel
    path={defaultCachePath}
    loading={defaultCacheLoading}
    cleaning={defaultCacheCleaning}
    error={defaultCacheError}
    packages={defaultCachePackages}
    filtered={filteredDefaultPackages}
    projectsCount={projects.length}
    onrefresh={loadDefaultCachePackages}
    onclean={cleanDefaultCache}
    onopenFolder={() => openPath(defaultCachePath)}
  />

  <CustomCachePanel
    bind:path={customCachePath}
    loading={customCacheLoading}
    cleaning={customCacheCleaning}
    error={customCacheError}
    packages={customCachePackages}
    filtered={filteredCustomPackages}
    onrefresh={loadCustomCachePackages}
    onclean={cleanCustomCache}
    onopenFolder={() => openPath(customCachePath)}
    onbrowse={pickCustomCachePath}
    oninput={() => {
      customCachePackages = [];
      customCacheError = null;
    }}
  />
</div>
