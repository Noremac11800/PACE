<script lang="ts">
  import {
    Plus,
    Check,
    FileCode,
    Copy,
    Folder,
    Save,
    FolderOpen,
    Loader,
  } from "@lucide/svelte";
  import {
    readTextFile,
    writeTextFile,
    exists,
    mkdir,
  } from "@tauri-apps/plugin-fs";
  import { open } from "@tauri-apps/plugin-dialog";
  import { onMount } from "svelte";
  import type { BuildProp } from "$lib/panels/directory-build-props/types.ts";
  import AddPropertyForm from "$lib/panels/directory-build-props/AddPropertyForm.svelte";
  import PropertyList from "$lib/panels/directory-build-props/PropertyList.svelte";

  let props: BuildProp[] = $state([]);
  let newName = $state("");
  let newValue = $state("");
  let isAdding = $state(false);
  let addError = $state("");
  let copiedId = $state("");
  let searchQuery = $state("");
  let editDraft: { id: string; name: string; value: string } | null =
    $state(null);
  let targetDir = $state("/tmp/PACE");
  let isSaving = $state(false);
  let isLoading = $state(false);
  let saveResult = $state("");
  let loadResult = $state("");

  let saveIsError = $derived(saveResult.startsWith("Error"));
  let loadIsError = $derived(
    loadResult.startsWith("Error") ||
      loadResult.startsWith("File not") ||
      loadResult.startsWith("Invalid"),
  );

  function generateId(): string {
    return crypto.randomUUID();
  }

  function addProp() {
    const trimmedName = newName.trim();
    const trimmedValue = newValue.trim();

    if (!trimmedName) {
      addError = "Property name is required.";
      return;
    }

    if (props.some((p) => p.name === trimmedName)) {
      addError = `Property "${trimmedName}" already exists.`;
      return;
    }

    props.push({
      id: generateId(),
      name: trimmedName,
      value: trimmedValue,
      editing: false,
    });
    newName = "";
    newValue = "";
    isAdding = false;
    addError = "";
    saveFile();
  }

  function removeProp(id: string) {
    props = props.filter((p) => p.id !== id);
  }

  function startEdit(id: string) {
    const target = props.find((p) => p.id === id);
    if (!target) return;
    editDraft = { id, name: target.name, value: target.value };
    props = props.map((p) => ({
      ...p,
      editing: p.id === id,
    }));
  }

  function cancelEdit(id: string) {
    editDraft = null;
    props = props.map((p) => ({
      ...p,
      editing: false,
    }));
  }

  function saveEdit(id: string) {
    if (!editDraft || editDraft.id !== id) return;
    const trimmed = editDraft.name.trim();
    if (!trimmed) return;

    const duplicate = props.some((p) => p.id !== id && p.name === trimmed);
    if (duplicate) return;

    props = props.map((p) =>
      p.id === id
        ? {
            ...p,
            name: trimmed,
            value: editDraft!.value.trim(),
            editing: false,
          }
        : p,
    );
    editDraft = null;
  }

  async function copyXml() {
    const xml = generateXml();
    await navigator.clipboard.writeText(xml);
    copiedId = "xml";
    setTimeout(() => (copiedId = ""), 2000);
  }

  function generateXml(): string {
    if (props.length === 0) {
      return `<Project>\n  <PropertyGroup>\n    <!-- No properties defined -->\n  </PropertyGroup>\n</Project>`;
    }
    const entries = props
      .map((p) => `    <${p.name}>${p.value}</${p.name}>`)
      .join("\n");
    return `<Project>\n  <PropertyGroup>\n${entries}\n  </PropertyGroup>\n</Project>`;
  }

  function getFilePath(): string {
    const dir = targetDir.endsWith("/") ? targetDir.slice(0, -1) : targetDir;
    return `${dir}/Directory.Build.props`;
  }

  async function saveFile() {
    isSaving = true;
    saveResult = "";
    loadResult = "";
    try {
      const dirExists = await exists(targetDir);
      if (!dirExists) {
        await mkdir(targetDir, { recursive: true });
      }
      const xml = generateXml();
      await writeTextFile(getFilePath(), xml);
      saveResult = `Saved to ${getFilePath()}`;
      setTimeout(() => (saveResult = ""), 3000);
    } catch (error) {
      saveResult = `Error: ${error}`;
    } finally {
      isSaving = false;
    }
  }

  async function loadFile() {
    isLoading = true;
    loadResult = "";
    saveResult = "";
    try {
      const filePath = getFilePath();
      const fileExists = await exists(filePath);
      if (!fileExists) {
        loadResult = `File not found: ${filePath}`;
        return;
      }
      const content = await readTextFile(filePath);
      parseXmlToProps(content);
      loadResult = `Loaded from ${filePath}`;
      setTimeout(() => (loadResult = ""), 3000);
    } catch (error) {
      loadResult = `Error: ${error}`;
    } finally {
      isLoading = false;
    }
  }

  function parseXmlToProps(xml: string) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xml, "text/xml");
    const propertyGroup = doc.querySelector("PropertyGroup");
    if (!propertyGroup) {
      loadResult = "Invalid file: no PropertyGroup found.";
      return;
    }
    const newProps: BuildProp[] = [];
    for (const child of Array.from(propertyGroup.children)) {
      newProps.push({
        id: generateId(),
        name: child.tagName,
        value: child.textContent ?? "",
        editing: false,
      });
    }
    props = newProps;
  }

  onMount(() => {
    loadFile();
  });

  let filteredProps = $derived(
    searchQuery.trim()
      ? props.filter(
          (p) =>
            p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            p.value.toLowerCase().includes(searchQuery.toLowerCase()),
        )
      : props,
  );
</script>

<div class="h-full flex flex-col overflow-auto">
  <!-- Header -->
  <div
    class="flex items-center gap-2 p-4 bg-surface-50-950 border-b border-surface-200-800"
  >
    <FileCode size={24} class="text-primary-500" />
    <h2 class="h3 text-primary-500">Directory.Build.props editor</h2>
  </div>

  <div class="flex flex-col p-4 gap-4">
    <!-- Target Directory -->
    <div class="card bg-surface-50-950 p-4 gap-2 shadow-md mb-4">
      <label for="target-dir" class="block text-sm text-surface-700-300 mb-1">
        Target directory
      </label>
      <p class="text-xs text-warning-500 mb-2">
        Note: This directory and/or its subdirectories, etc, should contain the
        .NET projects to be affected by the props file
      </p>
      <div class="input-group grid grid-cols-[auto_1fr] mb-1">
        <button
          class="ig-cell preset-tonal cursor-pointer"
          onclick={async () => {
            const selected = await open({ directory: true });
            if (selected) {
              targetDir = selected as string;
            }
          }}
          title="Select directory"
        >
          <Folder size={18} />
        </button>
        <input
          id="target-dir"
          class="ig-input"
          type="text"
          placeholder="Directory path"
          bind:value={targetDir}
        />
      </div>
      <div class="flex items-center gap-2">
        <button
          class="btn preset-filled-primary-500 flex items-center gap-1 text-sm"
          onclick={saveFile}
          disabled={isSaving || props.length === 0}
        >
          {#if isSaving}
            <Loader size={16} class="animate-spin" />
            Saving...
          {:else}
            <Save size={16} />
            Save
          {/if}
        </button>
        <button
          class="btn preset-tonal flex items-center gap-1 text-sm"
          onclick={loadFile}
          disabled={isLoading}
        >
          {#if isLoading}
            <Loader size={16} class="animate-spin" />
            Loading...
          {:else}
            <FolderOpen size={16} />
            Load
          {/if}
        </button>
        {#if saveResult}
          <span
            class="text-xs {saveIsError
              ? 'text-error-500'
              : 'text-success-500'}"
          >
            {saveResult}
          </span>
        {/if}
        {#if loadResult}
          <span
            class="text-xs {loadIsError
              ? 'text-error-500'
              : 'text-success-500'}"
          >
            {loadResult}
          </span>
        {/if}
      </div>
    </div>

    <!-- Search & Add bar -->
    <div class="flex items-center gap-2">
      <input
        class="input text-sm flex-1"
        type="text"
        placeholder="Search properties..."
        bind:value={searchQuery}
      />
      <button
        class="btn preset-filled-primary-500 flex items-center gap-1 text-sm"
        onclick={() => {
          isAdding = true;
          addError = "";
        }}
        disabled={isAdding}
      >
        <Plus size={16} />
        Add Property
      </button>
    </div>

    <!-- Add new property form -->
    {#if isAdding}
      <AddPropertyForm
        bind:newName
        bind:newValue
        {addError}
        onadd={addProp}
        oncancel={() => {
          isAdding = false;
          addError = "";
          newName = "";
          newValue = "";
        }}
      />
    {/if}

    <!-- Properties list -->
    {#if props.length === 0}
      <div
        class="flex-1 flex flex-col items-center justify-center text-surface-500"
      >
        <FileCode size={48} class="mb-4 opacity-50" />
        <p class="text-lg font-medium">No properties defined</p>
        <p class="text-sm">
          Click <strong>Add Property</strong> to create your first Directory.Build.props
          variable.
        </p>
      </div>
    {:else}
      <PropertyList
        {filteredProps}
        bind:editDraft
        {searchQuery}
        onstartEdit={startEdit}
        oncancelEdit={cancelEdit}
        onsaveEdit={saveEdit}
        onremove={removeProp}
      />

      <!-- XML Preview -->
      <div class="card bg-surface-50-950 shadow-md p-4 mt-2">
        <div class="flex items-center justify-between mb-2">
          <h4
            class="text-sm font-semibold text-surface-700-300 flex items-center gap-2"
          >
            <FileCode size={16} />
            XML Preview
          </h4>
          <button
            class="btn preset-tonal flex items-center gap-1 text-xs px-2 py-1"
            onclick={copyXml}
            title="Copy XML to clipboard"
          >
            {#if copiedId === "xml"}
              <Check size={14} />
              Copied
            {:else}
              <Copy size={14} />
              Copy XML
            {/if}
          </button>
        </div>
        <pre
          class="bg-surface-800-200 text-surface-200-800 p-3 rounded text-xs overflow-auto max-h-48 font-mono">{generateXml()}</pre>
      </div>
    {/if}
  </div>
</div>
