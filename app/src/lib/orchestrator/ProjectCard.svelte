<script lang="ts">
  import { ChevronDown, ChevronUp, Trash2, X } from "@lucide/svelte";
  import type { PaceProject } from "$lib/pace-config";

  let {
    project,
    groups,
    allProjects,
    expanded,
    dropdownOpen,
    onToggle,
    onRemove,
    onToggleDropdown,
    onUpdate,
  }: {
    project: PaceProject;
    groups: string[];
    allProjects: PaceProject[];
    expanded: boolean;
    dropdownOpen: boolean;
    onToggle: () => void;
    onRemove: () => void;
    onToggleDropdown: () => void;
    onUpdate: (patch: Partial<PaceProject>) => void;
  } = $props();

  function updateExplicitFrameworks(value: string): void {
    onUpdate({
      explicit_frameworks: value
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    });
  }

  function getAvailableProjects(): string[] {
    return allProjects
      .filter((p) => p.name !== project.name)
      .map((p) => p.name);
  }

  function toggleDependency(depName: string): void {
    const current = project.depends_on ?? [];
    const idx = current.indexOf(depName);
    onUpdate({
      depends_on:
        idx >= 0 ? current.filter((_, i) => i !== idx) : [...current, depName],
    });
  }
</script>

<div class="border border-surface-200-800 rounded-lg overflow-hidden">
  <div
    class="flex items-center gap-2 px-3 py-2.5 bg-surface-100-900/50 hover:bg-surface-100-900 transition-colors"
  >
    <button
      class="flex-1 text-left text-sm font-medium text-surface-900-100 truncate"
      onclick={onToggle}
    >
      {project.name || "Unnamed project"}
    </button>
    <div class="flex items-center gap-1 shrink-0">
      <button
        class="btn p-1 text-error-500 hover:text-error-400"
        onclick={onRemove}
        title="Remove project"
      >
        <Trash2 size={14} />
      </button>
      <button
        class="btn p-1 text-surface-400-600 hover:text-surface-900-100"
        onclick={onToggle}
      >
        {#if expanded}
          <ChevronUp size={14} />
        {:else}
          <ChevronDown size={14} />
        {/if}
      </button>
    </div>
  </div>

  {#if expanded}
    <div class="p-4 grid grid-cols-2 gap-4 border-t border-surface-200-800">
      <!-- Name -->
      <div class="col-span-2 sm:col-span-1">
        <label class="block text-xs font-semibold text-surface-700-300 mb-1">
          Name <span class="text-error-500">*</span>
          <input
            class="mt-1 w-full px-3 py-2 rounded-lg bg-surface-100-900 border border-surface-300-700 text-sm text-surface-900-50 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 font-normal"
            type="text"
            placeholder="my-project"
            value={project.name}
            oninput={(e) => onUpdate({ name: e.currentTarget.value })}
          />
        </label>
      </div>

      <!-- SLN Group -->
      <div class="col-span-2 sm:col-span-1">
        <label class="block text-xs font-semibold text-surface-700-300 mb-1">
          Solution group <span class="text-error-500">*</span>
          <select
            class="mt-1 w-full px-3 py-2 rounded-lg bg-surface-100-900 border border-surface-300-700 text-sm text-surface-900-50 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 font-normal"
            value={project.sln_group}
            onchange={(e) => onUpdate({ sln_group: e.currentTarget.value })}
          >
            {#each groups as g}
              <option value={g}>{g}</option>
            {/each}
          </select>
        </label>
      </div>

      <!-- csproj_path -->
      <div class="col-span-2">
        <label class="block text-xs font-semibold text-surface-700-300 mb-1">
          .csproj Path <span class="text-error-500">*</span>
          <input
            class="mt-1 w-full px-3 py-2 rounded-lg bg-surface-100-900 border border-surface-300-700 text-sm font-mono text-surface-900-50 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 font-normal"
            type="text"
            placeholder="src/My.Project/My.Project.csproj"
            value={project.csproj_path}
            oninput={(e) => onUpdate({ csproj_path: e.currentTarget.value })}
          />
        </label>
      </div>

      <!-- Repo URL -->
      <div class="col-span-2">
        <label class="block text-xs font-semibold text-surface-700-300 mb-1">
          Repo URL
          <input
            class="mt-1 w-full px-3 py-2 rounded-lg bg-surface-100-900 border border-surface-300-700 text-sm font-mono text-surface-900-50 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 font-normal"
            type="text"
            placeholder="git@github.com:org/repo.git"
            value={project.repo_url}
            oninput={(e) => onUpdate({ repo_url: e.currentTarget.value })}
          />
        </label>
      </div>

      <!-- Depends On -->
      <div class="col-span-2 sm:col-span-1">
        <label
          class="block text-xs font-semibold text-surface-700-300 mb-1"
          for="depends-on-{project.name}"
        >
          Depends on
        </label>
        <div class="relative mt-1.5">
          <button
            id="depends-on-{project.name}"
            class="w-full px-3 py-2 rounded-lg bg-surface-100-900 border border-surface-300-700 text-sm text-surface-900-50 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 font-normal text-left flex items-center justify-between"
            onclick={onToggleDropdown}
          >
            <span class="truncate">
              {project.depends_on?.length
                ? project.depends_on.join(", ")
                : "Select dependencies..."}
            </span>
            <ChevronDown size={14} class="shrink-0 ml-2" />
          </button>

          {#if dropdownOpen}
            <div
              class="absolute z-30 w-full max-h-48 overflow-y-auto rounded-lg border border-surface-200-800 bg-surface-50-950 shadow-xl"
              style="bottom: calc(100% + 4px);"
            >
              {#each getAvailableProjects() as availableProject}
                <label
                  class="flex items-center gap-2 px-3 py-2 text-sm text-surface-900-50 hover:bg-surface-200-800 cursor-pointer border-b border-surface-200-800 last:border-b-0"
                >
                  <input
                    type="checkbox"
                    checked={project.depends_on?.includes(availableProject)}
                    onchange={() => toggleDependency(availableProject)}
                    class="rounded border-surface-300-700 text-primary-500 focus:ring-primary-500"
                  />
                  <span>{availableProject}</span>
                </label>
              {/each}
              {#if getAvailableProjects().length === 0}
                <div class="px-3 py-2 text-sm text-surface-500-400">
                  No other projects available
                </div>
              {/if}
            </div>
          {/if}
        </div>
      </div>

      <!-- Explicit Frameworks -->
      <div class="col-span-2 sm:col-span-1">
        <label class="block text-xs font-semibold text-surface-700-300 mb-1">
          Explicit Frameworks
          <p class="text-xs text-surface-500-400 mt-0.5 mb-1.5 font-normal">
            Comma-separated framework monikers
          </p>
          <input
            class="w-full px-3 py-2 rounded-lg bg-surface-100-900 border border-surface-300-700 text-sm text-surface-900-50 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 font-normal"
            type="text"
            placeholder="net8.0-ios, net8.0-android"
            value={project.explicit_frameworks?.join(", ") ?? ""}
            oninput={(e) => updateExplicitFrameworks(e.currentTarget.value)}
          />
        </label>
        {#if project.explicit_frameworks?.length}
          <div class="flex flex-wrap gap-1 mt-2">
            {#each project.explicit_frameworks as fw}
              <span
                class="inline-flex items-center gap-1 text-xs bg-secondary-500/15 text-secondary-400 px-2 py-0.5 rounded-full"
              >
                {fw}
                <button
                  class="hover:text-secondary-200"
                  onclick={() =>
                    onUpdate({
                      explicit_frameworks: project.explicit_frameworks.filter(
                        (f) => f !== fw,
                      ),
                    })}
                >
                  <X size={10} />
                </button>
              </span>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
