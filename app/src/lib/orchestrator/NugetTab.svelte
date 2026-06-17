<script lang="ts">
  import { onMount } from "svelte";
  import { Command } from "@tauri-apps/plugin-shell";
  import { readDir } from "@tauri-apps/plugin-fs";
  import { homeDir, join } from "@tauri-apps/api/path";
  import { open } from "@tauri-apps/plugin-dialog";
  import { openPath } from "@tauri-apps/plugin-opener";
  import {
    Package,
    RefreshCw,
    FolderOpen,
    Server,
    CircleCheckBig,
    CircleX,
    CircleAlert,
    Loader,
    Trash2,
  } from "@lucide/svelte";
  import { configStore, saveConfig, paceArgs } from "$lib/config-store.svelte";

  interface NugetSource {
    name: string;
    url: string;
    enabled: boolean;
  }

  interface CachedPackage {
    name: string;
    versions: string[];
  }

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
  <!-- NuGet Sources -->
  <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Server size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100">NuGet Sources</span>
      </div>
      <div class="flex items-center gap-2">
        {#if nugetConfigDir}
          <button
            class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
            onclick={() => openPath(nugetConfigDir)}
            title="Open NuGet config folder"
          >
            <FolderOpen size={14} />
          </button>
        {/if}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
          onclick={loadSources}
          disabled={sourcesLoading}
          title="Refresh sources"
        >
          <RefreshCw size={14} class={sourcesLoading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>
    </div>

    {#if nugetConfigDir}
      <code class="text-xs text-surface-500-400">{nugetConfigDir}</code>
    {/if}

    {#if sourcesLoading}
      <div class="flex items-center gap-2 text-sm text-surface-500-400 py-2">
        <Loader size={16} class="animate-spin" />
        Running dotnet nuget list source...
      </div>
    {:else if sourcesError}
      <div
        class="flex items-center gap-2 text-sm text-error-500 bg-error-500/10 rounded p-3"
      >
        <CircleAlert size={16} class="shrink-0" />
        <span class="break-all">{sourcesError}</span>
      </div>
    {:else if sources.length === 0}
      <p class="text-sm text-surface-500-400">No sources found.</p>
    {:else}
      <div class="flex flex-col gap-2">
        {#each sources as source}
          <div class="flex flex-col bg-surface-100-900/50 rounded">
            <div class="flex items-start gap-3 p-3">
              {#if source.enabled}
                <CircleCheckBig
                  size={16}
                  class="text-success-500 mt-0.5 shrink-0"
                />
              {:else}
                <CircleX size={16} class="text-error-500 mt-0.5 shrink-0" />
              {/if}
              <div class="flex flex-col gap-0.5 min-w-0 flex-1">
                <span class="text-sm font-medium text-surface-900-100"
                  >{source.name}</span
                >
                <code class="text-xs text-surface-500-400 break-all"
                  >{source.url}</code
                >
              </div>
              <span
                class="ml-auto text-xs shrink-0 px-2 py-0.5 rounded-full {source.enabled
                  ? 'bg-success-500/15 text-success-500'
                  : 'bg-surface-300-700/30 text-surface-500-400'}"
              >
                {source.enabled ? "Enabled" : "Disabled"}
              </span>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Default NuGet Cache -->
  <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Package size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100"
          >Default NuGet Cache</span
        >
      </div>
      <div class="flex items-center gap-2">
        {#if !defaultCacheLoading && defaultCachePath}
          <button
            class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
            onclick={() => openPath(defaultCachePath)}
            title="Open folder"
          >
            <FolderOpen size={14} />
          </button>
        {/if}
        <button
          class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
          onclick={loadDefaultCachePackages}
          disabled={defaultCacheLoading || defaultCacheCleaning}
          title="Refresh packages"
        >
          <RefreshCw
            size={14}
            class={defaultCacheLoading ? "animate-spin" : ""}
          />
          Refresh
        </button>
        <button
          class="btn preset-filled-error-500 flex items-center gap-1.5 text-xs py-1 px-2"
          onclick={cleanDefaultCache}
          disabled={defaultCacheCleaning || defaultCacheLoading}
          title="Clean default cache"
        >
          {#if defaultCacheCleaning}
            <Loader size={14} class="animate-spin" />
            Cleaning...
          {:else}
            <Trash2 size={14} />
            Clean
          {/if}
        </button>
      </div>
    </div>

    {#if !defaultCacheLoading && defaultCachePath}
      <code class="text-xs text-surface-500-400">{defaultCachePath}</code>
    {/if}

    {#if projects.length > 0}
      <p class="text-xs text-surface-500-400">
        Showing packages matching {projects.length} project{projects.length ===
        1
          ? ""
          : "s"} from the active config.
      </p>
    {/if}

    {#if defaultCacheLoading}
      <div class="flex items-center gap-2 text-sm text-surface-500-400 py-2">
        <Loader size={16} class="animate-spin" />
        Scanning cache directory...
      </div>
    {:else if defaultCacheError}
      <div
        class="flex items-center gap-2 text-sm text-error-500 bg-error-500/10 rounded p-3"
      >
        <CircleAlert size={16} class="shrink-0" />
        <span class="break-all">{defaultCacheError}</span>
      </div>
    {:else if defaultCachePackages.length > 0}
      {@const filtered = filteredDefaultPackages}
      <div class="text-xs text-surface-500-400">
        {filtered.length} matching package{filtered.length === 1 ? "" : "s"} (of
        {defaultCachePackages.length} total)
      </div>
      {#if filtered.length === 0}
        <div
          class="flex items-center gap-2 text-sm text-surface-500-400 bg-surface-100-900/40 rounded p-3"
        >
          <CircleAlert size={16} class="shrink-0" />
          No packages matched the projects in the active config.
        </div>
      {:else}
        <div class="flex flex-col gap-0.5 max-h-72 overflow-y-auto">
          {#each filtered as pkg}
            <div
              class="flex items-center gap-2 px-2 py-1.5 rounded bg-surface-100-900/40"
            >
              <span
                class="font-mono text-xs text-surface-900-100 flex-1 truncate"
                >{pkg.name}</span
              >
              <div class="flex flex-wrap gap-1 shrink-0">
                {#each pkg.versions as ver}
                  <span
                    class="text-xs font-mono px-1.5 py-0.5 rounded bg-surface-200-800 text-surface-700-300"
                    >{ver}</span
                  >
                {/each}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {:else if !defaultCacheLoading}
      <div
        class="flex items-center gap-2 text-sm text-surface-500-400 bg-surface-100-900/40 rounded p-3"
      >
        <CircleAlert size={16} class="shrink-0" />
        No packages found in the default cache directory.
      </div>
    {/if}
  </div>

  <!-- Custom NuGet Cache -->
  <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <FolderOpen size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100">Custom Cache Path</span
        >
      </div>
      <div class="flex items-center gap-2">
        {#if customCachePath}
          <button
            class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
            onclick={() => openPath(customCachePath)}
            title="Open folder"
          >
            <FolderOpen size={14} />
          </button>
          <button
            class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2"
            onclick={loadCustomCachePackages}
            disabled={customCacheLoading || customCacheCleaning}
            title="Refresh packages"
          >
            <RefreshCw
              size={14}
              class={customCacheLoading ? "animate-spin" : ""}
            />
            Refresh
          </button>
          <button
            class="btn preset-filled-error-500 flex items-center gap-1.5 text-xs py-1 px-2"
            onclick={cleanCustomCache}
            disabled={customCacheCleaning ||
              customCacheLoading ||
              !customCachePath}
            title="Clean custom cache"
          >
            {#if customCacheCleaning}
              <Loader size={14} class="animate-spin" />
              Cleaning...
            {:else}
              <Trash2 size={14} />
              Clean
            {/if}
          </button>
        {/if}
      </div>
    </div>

    <div class="input-group grid grid-cols-[1fr_auto]">
      <input
        class="ig-input font-mono text-sm"
        type="text"
        placeholder="/path/to/nuget/packages"
        bind:value={customCachePath}
        oninput={() => {
          customCachePackages = [];
          customCacheError = null;
        }}
      />
      <button
        class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
        type="button"
        onclick={pickCustomCachePath}
        title="Browse"
      >
        <FolderOpen size={16} />
      </button>
    </div>

    {#if customCacheLoading}
      <div class="flex items-center gap-2 text-sm text-surface-500-400 py-2">
        <Loader size={16} class="animate-spin" />
        Scanning custom cache directory...
      </div>
    {:else if customCacheError}
      <div
        class="flex items-center gap-2 text-sm text-error-500 bg-error-500/10 rounded p-3"
      >
        <CircleAlert size={16} class="shrink-0" />
        <span class="break-all">{customCacheError}</span>
      </div>
    {:else if customCachePackages.length > 0}
      {@const filtered = filteredCustomPackages}
      <div class="text-xs text-surface-500-400">
        {filtered.length} matching package{filtered.length === 1 ? "" : "s"} (of
        {customCachePackages.length} total)
      </div>
      {#if filtered.length === 0}
        <div
          class="flex items-center gap-2 text-sm text-surface-500-400 bg-surface-100-900/40 rounded p-3"
        >
          <CircleAlert size={16} class="shrink-0" />
          No packages matched the projects in the active config.
        </div>
      {:else}
        <div class="flex flex-col gap-0.5 max-h-72 overflow-y-auto">
          {#each filtered as pkg}
            <div
              class="flex items-center gap-2 px-2 py-1.5 rounded bg-surface-100-900/40"
            >
              <span
                class="font-mono text-xs text-surface-900-100 flex-1 truncate"
                >{pkg.name}</span
              >
              <div class="flex flex-wrap gap-1 shrink-0">
                {#each pkg.versions as ver}
                  <span
                    class="text-xs font-mono px-1.5 py-0.5 rounded bg-surface-200-800 text-surface-700-300"
                    >{ver}</span
                  >
                {/each}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {:else if customCachePath && !customCacheLoading}
      <div
        class="flex items-center gap-2 text-sm text-surface-500-400 bg-surface-100-900/40 rounded p-3"
      >
        <CircleAlert size={16} class="shrink-0" />
        No .nupkg files found in this directory.
      </div>
    {:else if !customCachePath}
      <p class="text-sm text-surface-500-400">
        Select a folder to load packages from a custom NuGet cache location.
      </p>
    {/if}
  </div>
</div>
