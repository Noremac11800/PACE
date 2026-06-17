<script lang="ts">
  import { open, confirm } from "@tauri-apps/plugin-dialog";
  import {
    FileCode,
    ChevronDown,
    Check,
    Copy,
    Pen,
    Trash2,
    Upload,
    FilePlus,
  } from "@lucide/svelte";
  import {
    configStore,
    loadAvailableConfigs,
    loadConfig,
    createNewConfig,
    duplicateConfig,
    renameConfig,
    deleteConfig,
    importConfig,
  } from "$lib/config-store.svelte";

  let configPickerOpen = $state(false);
  let newConfigName = $state("");
  let creatingNew = $state(false);
  let showNewInput = $state(false);
  let duplicating = $state(false);
  let duplicateSource = $state<string | null>(null);
  let duplicateName = $state("");
  let renaming = $state(false);
  let renameSource = $state<string | null>(null);
  let renameName = $state("");
  let importing = $state(false);
  let showImportNameInput = $state(false);
  let importName = $state("");
  let importError = $state<string | null>(null);
  let selectedFilePath = $state<string | null>(null);

  async function switchConfig(filename: string): Promise<void> {
    configPickerOpen = false;
    await loadConfig(filename);
  }

  async function handleCreateNew(): Promise<void> {
    if (!newConfigName.trim()) return;
    creatingNew = true;
    try {
      await createNewConfig(newConfigName.trim());
      newConfigName = "";
      showNewInput = false;
      configPickerOpen = false;
    } finally {
      creatingNew = false;
    }
  }

  function startDuplicate(filename: string): void {
    duplicateSource = filename;
    duplicateName = filename.replace(/\.toml$/, "-copy");
    showNewInput = false;
  }

  async function handleDuplicate(): Promise<void> {
    if (!duplicateSource || !duplicateName.trim()) return;
    duplicating = true;
    try {
      await duplicateConfig(duplicateSource, duplicateName.trim());
      duplicateSource = null;
      duplicateName = "";
      configPickerOpen = false;
    } finally {
      duplicating = false;
    }
  }

  function cancelDuplicate(): void {
    duplicateSource = null;
    duplicateName = "";
  }

  function startRename(filename: string): void {
    renameSource = filename;
    renameName = filename.replace(/\.toml$/, "");
    showNewInput = false;
  }

  async function handleRename(): Promise<void> {
    if (!renameSource || !renameName.trim()) return;
    renaming = true;
    try {
      await renameConfig(renameSource, renameName.trim());
      renameSource = null;
      renameName = "";
      configPickerOpen = false;
    } finally {
      renaming = false;
    }
  }

  function cancelRename(): void {
    renameSource = null;
    renameName = "";
  }

  async function handleDelete(filename: string): Promise<void> {
    const confirmed = await confirm(
      "Are you sure you want to delete this config?",
      { title: "Delete Config", kind: "warning" },
    );
    if (!confirmed) return;
    await deleteConfig(filename);
  }

  async function startImport(): Promise<void> {
    importError = null;
    showNewInput = false;

    const selected = await open({
      multiple: false,
      filters: [{ name: "TOML Config", extensions: ["toml"] }],
    });

    if (!selected || typeof selected !== "string") {
      return;
    }

    selectedFilePath = selected;
    const pathParts = selected.split(/[/\\]/);
    const filename = pathParts[pathParts.length - 1] || "imported-config";
    importName = filename.replace(/\.toml$/, "");
    showImportNameInput = true;
  }

  async function handleImport(): Promise<void> {
    if (!importName.trim() || !selectedFilePath) return;
    importing = true;
    importError = null;
    try {
      const result = await importConfig(selectedFilePath, importName.trim());
      if (result.success) {
        importName = "";
        selectedFilePath = null;
        showImportNameInput = false;
        configPickerOpen = false;
      } else {
        importError = result.error || "Failed to import config";
      }
    } finally {
      importing = false;
    }
  }

  function focusOnMount(node: HTMLElement): void {
    node.focus();
  }

  function cancelImport(): void {
    importName = "";
    importError = null;
    selectedFilePath = null;
    importing = false;
    showImportNameInput = false;
  }
</script>

<div class="relative">
  <button
    class="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-surface-300-700 bg-surface-100-900 text-sm hover:border-primary-500 transition-colors"
    onclick={() => (configPickerOpen = !configPickerOpen)}
  >
    <FileCode size={14} class="text-primary-500 shrink-0" />
    <span class="max-w-[160px] truncate text-surface-900-100">
      {configStore.activeConfigName?.replace(/\.toml$/, "") ??
        "No config loaded"}
    </span>
    <ChevronDown size={14} class="text-surface-500-400 shrink-0" />
  </button>

  {#if configPickerOpen}
    <button
      class="fixed inset-0 z-10 cursor-default"
      aria-label="Close config picker"
      onclick={() => {
        configPickerOpen = false;
        showNewInput = false;
      }}
    ></button>
    <div
      class="fixed z-20 right-4 top-18 w-auto min-w-64 max-w-none rounded-lg border border-surface-200-800 bg-surface-50-950 shadow-xl"
    >
      {#if configStore.availableConfigs.length > 0}
        <div
          class="px-3 pt-2 pb-1 text-xs font-semibold text-surface-500-400 uppercase tracking-wide"
        >
          Available Configs
        </div>
        {#each configStore.availableConfigs as entry}
          <div class="flex items-center gap-1">
            <button
              class="flex-1 flex items-center justify-between px-3 py-2 text-sm hover:bg-surface-100-900 transition-colors text-left rounded-l-lg"
              onclick={() => switchConfig(entry.filename)}
            >
              <span class="truncate">{entry.displayName}</span>
              {#if configStore.activeConfigName === entry.filename}
                <Check size={14} class="text-primary-500 shrink-0" />
              {/if}
            </button>
            <button
              class="p-2 text-surface-400-600 hover:text-primary-500 hover:bg-surface-100-900 transition-colors"
              onclick={() => startRename(entry.filename)}
              title="Rename config"
            >
              <Pen size={14} />
            </button>
            <button
              class="p-2 text-surface-400-600 hover:text-primary-500 hover:bg-surface-100-900 transition-colors"
              onclick={() => startDuplicate(entry.filename)}
              title="Duplicate config"
            >
              <Copy size={14} />
            </button>
            <button
              class="p-2 text-surface-400-600 hover:text-error-500 hover:bg-surface-100-900 transition-colors rounded-r-lg"
              onclick={() => handleDelete(entry.filename)}
              title="Delete config"
            >
              <Trash2 size={14} />
            </button>
          </div>
        {/each}
        <div class="border-t border-surface-200-800 my-1"></div>
      {/if}

      {#if renameSource}
        <div class="px-3 py-2 flex gap-2">
          <input
            class="flex-1 px-2 py-1.5 rounded border border-surface-300-700 bg-surface-100-900 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
            type="text"
            placeholder="new-name"
            bind:value={renameName}
            onkeydown={(e) => e.key === "Enter" && handleRename()}
            use:focusOnMount
          />
          <button
            class="btn preset-tonal text-xs px-2 py-1"
            onclick={cancelRename}
          >
            Cancel
          </button>
          <button
            class="btn preset-filled-primary-500 text-xs px-2 py-1"
            onclick={handleRename}
            disabled={renaming || !renameName.trim()}
          >
            {renaming ? "…" : "Rename"}
          </button>
        </div>
      {:else if duplicateSource}
        <div class="px-3 py-2 flex gap-2">
          <input
            class="flex-1 px-2 py-1.5 rounded border border-surface-300-700 bg-surface-100-900 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
            type="text"
            placeholder="new-config-name"
            bind:value={duplicateName}
            onkeydown={(e) => e.key === "Enter" && handleDuplicate()}
            use:focusOnMount
          />
          <button
            class="btn preset-tonal text-xs px-2 py-1"
            onclick={cancelDuplicate}
          >
            Cancel
          </button>
          <button
            class="btn preset-filled-primary-500 text-xs px-2 py-1"
            onclick={handleDuplicate}
            disabled={duplicating || !duplicateName.trim()}
          >
            {duplicating ? "…" : "Duplicate"}
          </button>
        </div>
      {:else if showNewInput}
        <div class="px-3 py-2 flex gap-2">
          <input
            class="flex-1 px-2 py-1.5 rounded border border-surface-300-700 bg-surface-100-900 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
            type="text"
            placeholder="config-name"
            bind:value={newConfigName}
            onkeydown={(e) => e.key === "Enter" && handleCreateNew()}
            use:focusOnMount
          />
          <button
            class="btn preset-tonal text-xs px-2 py-1"
            onclick={() => (showNewInput = false)}
          >
            Cancel
          </button>
          <button
            class="btn preset-filled-primary-500 text-xs px-2 py-1"
            onclick={handleCreateNew}
            disabled={creatingNew || !newConfigName.trim()}
          >
            {creatingNew ? "…" : "Create"}
          </button>
        </div>
      {:else if showImportNameInput}
        <div class="px-3 py-2 flex gap-2">
          <input
            class="flex-1 px-2 py-1.5 rounded border border-surface-300-700 bg-surface-100-900 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
            type="text"
            placeholder="config-name"
            bind:value={importName}
            onkeydown={(e) => e.key === "Enter" && handleImport()}
            use:focusOnMount
          />
          <button
            class="btn preset-tonal text-xs px-2 py-1"
            onclick={cancelImport}
          >
            Cancel
          </button>
          <button
            class="btn preset-filled-primary-500 text-xs px-2 py-1"
            onclick={handleImport}
            disabled={importing || !importName.trim()}
          >
            {importing ? "…" : "Import"}
          </button>
        </div>
        {#if importError}
          <div class="px-3 pb-2 text-xs text-error-500">{importError}</div>
        {/if}
      {:else}
        <button
          class="w-full flex items-center gap-2 px-3 py-2 text-sm text-primary-500 hover:bg-surface-100-900 transition-colors text-left"
          onclick={() => (showNewInput = true)}
        >
          <FilePlus size={14} />
          New config…
        </button>
        <button
          class="w-full flex items-center gap-2 px-3 py-2 text-sm text-primary-500 hover:bg-surface-100-900 transition-colors text-left"
          onclick={startImport}
        >
          <Upload size={14} />
          Import config…
        </button>
      {/if}
    </div>
  {/if}
</div>
