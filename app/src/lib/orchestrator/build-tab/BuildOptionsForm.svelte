<script lang="ts">
  import { Switch } from "@skeletonlabs/skeleton-svelte";
  import { Hammer, ChevronDown, FolderOpen } from "@lucide/svelte";
  import type { PaceProject, PaceBuildProp } from "$lib/pace-config";
  import { FRAMEWORKS, type Framework } from "./frameworks";

  let {
    projects,
    buildProps,
    fromProject = $bindable(""),
    toProject = $bindable(""),
    buildConfig = $bindable("Debug"),
    selectedFramework = $bindable(""),
    noRestore = $bindable(false),
    cleanBeforeBuild = $bindable(false),
    msbuildProps = $bindable({}),
    onpickPath,
  }: {
    projects: PaceProject[];
    buildProps: PaceBuildProp[];
    fromProject?: string;
    toProject?: string;
    buildConfig?: "Debug" | "Release";
    selectedFramework?: Framework | "";
    noRestore?: boolean;
    cleanBeforeBuild?: boolean;
    msbuildProps?: Record<string, string>;
    onpickPath: (propName: string) => void;
  } = $props();
</script>

<!-- Configuration -->
<div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
  <div class="flex items-center gap-2">
    <Hammer size={18} class="text-primary-500" />
    <span class="font-semibold text-surface-900-100">Build Configuration</span>
  </div>

  <!-- From / To project pickers -->
  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1">
      <label class="text-xs font-medium text-surface-600-400" for="from-picker">
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
          {#each projects as project (project.name)}
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
      <label class="text-xs font-medium text-surface-600-400" for="to-picker">
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
          {#each projects as project (project.name)}
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
    <span class="text-xs font-medium text-surface-600-400">Configuration</span>
    <div class="flex flex-wrap gap-2">
      {#each ["Debug", "Release"] as const as cfg (cfg)}
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
      {#each FRAMEWORKS as fw (fw.id)}
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
  <div class="flex items-center gap-3">
    <Switch
      checked={noRestore}
      onCheckedChange={(details) => (noRestore = details.checked)}
    >
      <Switch.Control><Switch.Thumb /></Switch.Control>
      <Switch.HiddenInput />
    </Switch>
    <span class="text-sm text-surface-900-100">Skip restore (--no-restore)</span
    >
  </div>

  <!-- Clean before build toggle -->
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

<!-- MSBuild Properties -->
{#if buildProps.length > 0}
  <div class="card bg-surface-50-950 p-4 flex flex-col gap-4">
    <span class="font-semibold text-surface-900-100">MSBuild Properties</span>

    {#each buildProps as prop (prop.name)}
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
            <Switch.Control><Switch.Thumb /></Switch.Control>
            <Switch.HiddenInput />
          </Switch>
          <span class="text-sm font-mono text-surface-900-100">{prop.name}</span
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
              placeholder="{String(prop.default) || '/path/to/dir'} (optional)"
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
              onclick={() => onpickPath(prop.name)}
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
