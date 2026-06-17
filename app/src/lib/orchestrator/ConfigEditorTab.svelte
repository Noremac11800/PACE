<script lang="ts">
  import {
    Plus,
    Trash2,
    FolderOpen,
    ChevronDown,
    ChevronUp,
    Layers,
    Settings2,
  } from "@lucide/svelte";
  import { open } from "@tauri-apps/plugin-dialog";
  import {
    configStore,
    saveConfig,
    emptyProject,
  } from "$lib/config-store.svelte";
  import type {
    PaceConfig,
    PaceProject,
    PaceBuildProp,
  } from "$lib/pace-config";
  import ProjectCard from "$lib/orchestrator/ProjectCard.svelte";

  type PropType = "string" | "boolean" | "path";

  let expandedProjects = $state<Set<number>>(new Set());
  let collapsedGroups = $state<Set<string>>(new Set());
  let dependsOnDropdownOpen = $state<Set<number>>(new Set());

  function snapshotConfig(): PaceConfig {
    const snap = $state.snapshot(configStore.activeConfig);
    return structuredClone(
      snap ?? { repodir: "", projects: [], build_props: [] },
    ) as PaceConfig;
  }

  let draft = $state<PaceConfig>(snapshotConfig());

  function deriveGroups(projects: PaceProject[]): string[] {
    const seen = new Set<string>();
    const result: string[] = [];
    for (const p of projects) {
      if (p.sln_group && !seen.has(p.sln_group)) {
        seen.add(p.sln_group);
        result.push(p.sln_group);
      }
    }
    return result;
  }

  let groups = $state<string[]>([]);
  let lastSyncedConfigName = $state<string | null>(null);

  $effect(() => {
    const name = configStore.activeConfigName;
    const snap = $state.snapshot(configStore.activeConfig);
    if (name !== lastSyncedConfigName) {
      lastSyncedConfigName = name;
      if (snap) {
        draft = structuredClone(snap) as PaceConfig;
        groups = deriveGroups(draft.projects);
      } else {
        draft = { repodir: "", projects: [], build_props: [] };
        groups = [];
      }
      expandedProjects = new Set();
      collapsedGroups = new Set(groups);
    }
  });

  function getProjectsByGroup(group: string): PaceProject[] {
    return draft.projects.filter((p) => p.sln_group === group);
  }

  function getUngrouped(): PaceProject[] {
    return draft.projects.filter((p) => !p.sln_group);
  }

  function projectIndex(project: PaceProject): number {
    return draft.projects.indexOf(project);
  }

  function addSolutionGroup(): void {
    const name = `Group ${groups.length + 1}`;
    groups = [...groups, name];
  }

  function renameGroup(oldName: string, newName: string): void {
    if (!newName.trim() || newName === oldName) return;
    groups = groups.map((g) => (g === oldName ? newName : g));
    for (const p of draft.projects) {
      if (p.sln_group === oldName) p.sln_group = newName;
    }
    if (collapsedGroups.has(oldName)) {
      const next = new Set(collapsedGroups);
      next.delete(oldName);
      next.add(newName);
      collapsedGroups = next;
    }
  }

  function deleteGroup(name: string): void {
    groups = groups.filter((g) => g !== name);
    draft.projects = draft.projects.filter((p) => p.sln_group !== name);
  }

  function toggleGroup(name: string): void {
    const next = new Set(collapsedGroups);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    collapsedGroups = next;
  }

  function addProjectToGroup(group: string): void {
    const p = emptyProject();
    p.sln_group = group;
    draft.projects = [...draft.projects, p];
    expandedProjects = new Set([
      ...expandedProjects,
      draft.projects.length - 1,
    ]);
  }

  async function pickDirectory(): Promise<void> {
    const selected = await open({ directory: true, multiple: false });
    if (selected && typeof selected === "string") {
      draft.repodir = selected;
    }
  }

  async function pickNugetCachePath(): Promise<void> {
    const selected = await open({ directory: true, multiple: false });
    if (selected && typeof selected === "string") {
      draft.nuget_cache_path = selected;
    }
  }

  function removeProject(index: number): void {
    draft.projects = draft.projects.filter((_, i) => i !== index);
    const next = new Set<number>();
    for (const idx of expandedProjects) {
      if (idx < index) next.add(idx);
      else if (idx > index) next.add(idx - 1);
    }
    expandedProjects = next;
  }

  function toggleProject(index: number): void {
    const next = new Set(expandedProjects);
    if (next.has(index)) next.delete(index);
    else next.add(index);
    expandedProjects = next;
  }

  function updateDependsOn(project: PaceProject, value: string): void {
    project.depends_on = value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  // Build Props Management
  function addBuildProp(): void {
    const newProp: PaceBuildProp = {
      name: "",
      datatype: "string",
      default: "",
    };
    draft.build_props = [...(draft.build_props ?? []), newProp];
  }

  function removeBuildProp(index: number): void {
    draft.build_props = draft.build_props?.filter((_, i) => i !== index) ?? [];
  }

  function updateBuildPropName(index: number, name: string): void {
    if (!draft.build_props) return;
    draft.build_props[index] = { ...draft.build_props[index], name };
  }

  function updateBuildPropDatatype(index: number, datatype: PropType): void {
    if (!draft.build_props) return;
    const prop = draft.build_props[index];
    let defaultValue: string | boolean = "";
    if (datatype === "boolean") {
      defaultValue = false;
    }
    draft.build_props[index] = { ...prop, datatype, default: defaultValue };
  }

  function updateBuildPropDefault(
    index: number,
    value: string | boolean,
  ): void {
    if (!draft.build_props) return;
    draft.build_props[index] = { ...draft.build_props[index], default: value };
  }

  async function pickPropDefaultPath(index: number): Promise<void> {
    const selected = await open({ directory: true, multiple: false });
    if (selected && typeof selected === "string") {
      updateBuildPropDefault(index, selected);
    }
  }

  // Auto-save whenever draft changes
  $effect(() => {
    const snap = $state.snapshot(draft);
    if (!configStore.activeConfigName) return;
    // Fire and forget save
    saveConfig(configStore.activeConfigName, snap as PaceConfig)
      .then(() => {
        configStore.activeConfig = snap as PaceConfig;
      })
      .catch((e) => {
        console.error("Auto-save failed:", e);
      });
  });
</script>

<div class="flex flex-col gap-4 pb-8">
  <!-- Repo Directory -->
  <div class="card bg-surface-50-950 p-4">
    <span class="block text-sm font-semibold text-surface-900-100 mb-2"
      >Repository Directory</span
    >
    <p class="text-xs text-surface-500-400 mb-3">
      Base directory where all project repos are cloned.
    </p>
    <div class="input-group grid grid-cols-[1fr_auto]">
      <input
        class="ig-input font-mono text-sm"
        type="text"
        placeholder="/path/to/repos"
        bind:value={draft.repodir}
      />
      <button
        class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
        type="button"
        onclick={pickDirectory}
        title="Browse"
      >
        <FolderOpen size={16} />
      </button>
    </div>
  </div>

  <!-- NuGet Cache Path -->
  <div class="card bg-surface-50-950 p-4">
    <span class="block text-sm font-semibold text-surface-900-100 mb-2"
      >NuGet Cache Path</span
    >
    <p class="text-xs text-surface-500-400 mb-3">
      Optional path to a local NuGet package cache directory. When set, this is
      used in the Packages tab.
    </p>
    <div class="input-group grid grid-cols-[1fr_auto_auto]">
      <input
        class="ig-input font-mono text-sm"
        type="text"
        placeholder="/path/to/nuget/packages"
        bind:value={draft.nuget_cache_path}
      />
      <button
        class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
        type="button"
        onclick={pickNugetCachePath}
        title="Browse"
      >
        <FolderOpen size={16} />
      </button>
      <button
        class="ig-cell btn preset-tonal hover:text-error-500 transition-colors"
        type="button"
        onclick={() => (draft.nuget_cache_path = undefined)}
        title="Clear"
        disabled={!draft.nuget_cache_path}
      >
        <Trash2 size={16} />
      </button>
    </div>
  </div>

  <!-- MSBuild Properties -->
  <div class="card bg-surface-50-950 p-4">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <Settings2 size={18} class="text-primary-500" />
        <span class="font-semibold text-surface-900-100"
          >MSBuild Properties</span
        >
        <span class="text-xs text-surface-500-400"
          >({draft.build_props?.length ?? 0})</span
        >
      </div>
      <button
        class="btn preset-tonal text-sm flex items-center gap-1.5 hover:preset-filled-primary-500 transition-colors"
        onclick={addBuildProp}
      >
        <Plus size={14} />
        Add property
      </button>
    </div>

    <div class="flex flex-col gap-3">
      {#each draft.build_props ?? [] as prop, index (index)}
        <div class="flex items-start gap-2 p-3 bg-surface-100-900/50 rounded">
          <!-- Prop Name -->
          <div class="flex-1 min-w-0">
            <label
              for="prop-name-{index}"
              class="block text-xs font-medium text-surface-600-400 mb-1"
            >
              Property Name
            </label>
            <input
              id="prop-name-{index}"
              class="input font-mono text-sm w-full"
              type="text"
              placeholder="e.g., MyProperty"
              value={prop.name}
              oninput={(e) =>
                updateBuildPropName(
                  index,
                  (e.target as HTMLInputElement).value,
                )}
            />
          </div>

          <!-- Datatype -->
          <div class="w-28 shrink-0">
            <label
              for="prop-type-{index}"
              class="block text-xs font-medium text-surface-600-400 mb-1"
            >
              Type
            </label>
            <select
              id="prop-type-{index}"
              class="select text-sm w-full"
              value={prop.datatype}
              onchange={(e) =>
                updateBuildPropDatatype(
                  index,
                  (e.target as HTMLSelectElement).value as PropType,
                )}
            >
              <option value="string">string</option>
              <option value="boolean">boolean</option>
              <option value="path">path</option>
            </select>
          </div>

          <!-- Default Value -->
          <div class="flex-1 min-w-0">
            <span class="block text-xs font-medium text-surface-600-400 mb-1">
              Default Value
            </span>
            {#if prop.datatype === "boolean"}
              {@const boolVal =
                prop.default === true || prop.default === "true"}
              <div class="flex items-center gap-3 cursor-pointer h-9">
                <div
                  role="checkbox"
                  aria-checked={boolVal}
                  tabindex="0"
                  class="w-9 h-5 rounded-full transition-colors flex items-center px-0.5 shrink-0 {boolVal
                    ? 'bg-primary-500'
                    : 'bg-surface-300-700'}"
                  onclick={() =>
                    updateBuildPropDefault(index, boolVal ? "false" : "true")}
                  onkeydown={(e) =>
                    e.key === " " &&
                    updateBuildPropDefault(index, boolVal ? "false" : "true")}
                >
                  <div
                    class="w-4 h-4 rounded-full bg-white shadow transition-transform {boolVal
                      ? 'translate-x-4'
                      : 'translate-x-0'}"
                  ></div>
                </div>
                <span class="text-sm text-surface-900-100"
                  >{boolVal ? "true" : "false"}</span
                >
              </div>
            {:else if prop.datatype === "path"}
              <div class="input-group grid grid-cols-[1fr_auto]">
                <input
                  class="ig-input font-mono text-sm"
                  type="text"
                  placeholder="/path/to/dir"
                  value={prop.default}
                  oninput={(e) =>
                    updateBuildPropDefault(
                      index,
                      (e.target as HTMLInputElement).value,
                    )}
                />
                <button
                  class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
                  type="button"
                  onclick={() => pickPropDefaultPath(index)}
                  title="Browse"
                >
                  <FolderOpen size={16} />
                </button>
              </div>
            {:else}
              <input
                class="input font-mono text-sm w-full"
                type="text"
                placeholder="default value"
                value={prop.default}
                oninput={(e) =>
                  updateBuildPropDefault(
                    index,
                    (e.target as HTMLInputElement).value,
                  )}
              />
            {/if}
          </div>

          <!-- Remove Button -->
          <button
            class="btn preset-tonal mt-5 hover:text-error-500 transition-colors shrink-0"
            onclick={() => removeBuildProp(index)}
            title="Remove property"
          >
            <Trash2 size={16} />
          </button>
        </div>
      {/each}

      {#if (draft.build_props?.length ?? 0) === 0}
        <div
          class="bg-surface-100-900/50 p-6 text-center text-surface-500-400 text-sm rounded"
        >
          No MSBuild properties configured. Click
          <span class="font-semibold">Add property</span>
          to define custom build properties.
        </div>
      {/if}
    </div>
  </div>

  <!-- Projects -->
  <div class="card bg-surface-50-950 p-4">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span class="font-semibold text-surface-900-100">Projects</span>
        <span class="text-xs text-surface-500-400"
          >({draft.projects.length})</span
        >
      </div>
      <button
        class="btn preset-tonal text-sm flex items-center gap-1.5 hover:preset-filled-primary-500 transition-colors"
        onclick={addSolutionGroup}
      >
        <Plus size={14} />
        Add solution group
      </button>
    </div>

    <div class="flex flex-col gap-4">
      {#each groups as group (group)}
        {@const collapsed = collapsedGroups.has(group)}
        {@const groupProjects = getProjectsByGroup(group)}
        <div class="card bg-surface-100-900/50 p-4">
          <!-- Group Header -->
          <div class="flex items-center gap-2 mb-3">
            <button
              class="btn p-1 text-surface-400-600 hover:text-surface-900-100 shrink-0"
              onclick={() => toggleGroup(group)}
              title={collapsed ? "Expand" : "Collapse"}
            >
              {#if collapsed}
                <ChevronDown size={16} />
              {:else}
                <ChevronUp size={16} />
              {/if}
            </button>
            <Layers size={16} class="text-primary-500 shrink-0" />
            <input
              class="flex-1 min-w-0 px-2 py-1 rounded bg-transparent border border-transparent hover:border-surface-300-700 focus:border-primary-500 focus:outline-none text-sm font-semibold text-surface-900-100 transition-colors"
              type="text"
              value={group}
              onblur={(e) => renameGroup(group, e.currentTarget.value)}
              onkeydown={(e) => e.key === "Enter" && e.currentTarget.blur()}
            />
            <span class="text-xs text-surface-500-400 shrink-0"
              >({groupProjects.length})</span
            >
            <button
              class="btn preset-tonal text-xs flex items-center gap-1 hover:preset-filled-primary-500 transition-colors shrink-0"
              onclick={() => addProjectToGroup(group)}
            >
              <Plus size={12} />
              Add
            </button>
            <button
              class="btn p-1 text-error-500 hover:text-error-400 shrink-0"
              onclick={() => deleteGroup(group)}
              title="Delete group and its projects"
            >
              <Trash2 size={14} />
            </button>
          </div>

          {#if !collapsed}
            <div class="flex flex-col gap-2">
              {#each groupProjects as project}
                {@const index = projectIndex(project)}
                <ProjectCard
                  {project}
                  {groups}
                  allProjects={draft.projects}
                  expanded={expandedProjects.has(index)}
                  dropdownOpen={dependsOnDropdownOpen.has(index)}
                  onToggle={() => toggleProject(index)}
                  onRemove={() => removeProject(index)}
                  onToggleDropdown={() => {
                    const next = new Set(dependsOnDropdownOpen);
                    if (next.has(index)) next.delete(index);
                    else next.add(index);
                    dependsOnDropdownOpen = next;
                  }}
                  onUpdate={(patch) =>
                    Object.assign(draft.projects[index], patch)}
                />
              {/each}
              {#if groupProjects.length === 0}
                <p class="text-xs text-surface-500-400 text-center py-3">
                  No projects in this group yet.
                </p>
              {/if}
            </div>
          {/if}
        </div>
      {/each}

      {#if groups.length === 0}
        <div
          class="bg-surface-100-900/50 p-8 text-center text-surface-500-400 text-sm rounded"
        >
          No solution groups yet. Click <span class="font-semibold"
            >Add solution group</span
          > to get started.
        </div>
      {/if}
    </div>
  </div>
</div>
