<script lang="ts">
  import {
    Plus,
    Trash2,
    Pencil,
    Check,
    X,
    FileCode,
    Copy,
    TriangleAlert,
  } from "@lucide/svelte";

  interface BuildProp {
    id: string;
    name: string;
    value: string;
    editing: boolean;
  }

  let props: BuildProp[] = $state([]);
  let newName = $state("");
  let newValue = $state("");
  let isAdding = $state(false);
  let addError = $state("");
  let copiedId = $state("");
  let searchQuery = $state("");
  let editDraft: { id: string; name: string; value: string } | null =
    $state(null);

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

<div class="h-full flex flex-col p-4 gap-4 overflow-auto">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <h2 class="h3 text-primary-500 flex items-center gap-2">
      <FileCode size={24} />
      Directory.Build.props Editor
    </h2>
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
    <div class="card bg-surface-50-950 shadow-md p-4">
      <h4 class="text-sm font-semibold text-surface-700-300 mb-3">
        New Property
      </h4>
      <div class="flex flex-col gap-3">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label
              for="new-prop-name"
              class="block text-xs text-surface-700-300 mb-1">Name</label
            >
            <input
              id="new-prop-name"
              class="input text-sm"
              type="text"
              placeholder="e.g. TargetFramework"
              bind:value={newName}
              onkeydown={(e) => e.key === "Enter" && addProp()}
            />
          </div>
          <div>
            <label
              for="new-prop-value"
              class="block text-xs text-surface-700-300 mb-1">Value</label
            >
            <input
              id="new-prop-value"
              class="input text-sm"
              type="text"
              placeholder="e.g. net8.0"
              bind:value={newValue}
              onkeydown={(e) => e.key === "Enter" && addProp()}
            />
          </div>
        </div>
        {#if addError}
          <p class="text-xs text-error-500 flex items-center gap-1">
            <TriangleAlert size={14} />
            {addError}
          </p>
        {/if}
        <div class="flex items-center gap-2 justify-end">
          <button
            class="btn preset-tonal text-sm flex items-center gap-1"
            onclick={() => {
              isAdding = false;
              addError = "";
              newName = "";
              newValue = "";
            }}
          >
            <X size={16} />
            Cancel
          </button>
          <button
            class="btn preset-filled-primary-500 text-sm flex items-center gap-1"
            onclick={addProp}
          >
            <Check size={16} />
            Add
          </button>
        </div>
      </div>
    </div>
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
    <div class="flex flex-col gap-2">
      {#each filteredProps as prop (prop.id)}
        <div
          class="card bg-surface-50-950 shadow-sm p-3 flex items-center gap-3"
        >
          {#if prop.editing && editDraft}
            <div class="flex-1 grid grid-cols-2 gap-3">
              <input
                class="input text-sm"
                type="text"
                bind:value={editDraft.name}
                onkeydown={(e) => e.key === "Enter" && saveEdit(prop.id)}
              />
              <input
                class="input text-sm"
                type="text"
                bind:value={editDraft.value}
                onkeydown={(e) => e.key === "Enter" && saveEdit(prop.id)}
              />
            </div>
            <button
              class="btn preset-filled-primary-500 p-2"
              onclick={() => saveEdit(prop.id)}
              title="Save"
            >
              <Check size={16} />
            </button>
            <button
              class="btn preset-tonal p-2"
              onclick={() => cancelEdit(prop.id)}
              title="Cancel"
            >
              <X size={16} />
            </button>
          {:else}
            <div class="flex-1 grid grid-cols-2 gap-3">
              <div>
                <p class="text-xs text-surface-500">Name</p>
                <p class="font-mono text-sm font-medium">{prop.name}</p>
              </div>
              <div>
                <p class="text-xs text-surface-500">Value</p>
                <p class="font-mono text-sm">{prop.value || "—"}</p>
              </div>
            </div>
            <button
              class="btn preset-tonal p-2"
              onclick={() => startEdit(prop.id)}
              title="Edit"
            >
              <Pencil size={16} />
            </button>
            <button
              class="btn preset-filled-error-500 p-2"
              onclick={() => removeProp(prop.id)}
              title="Delete"
            >
              <Trash2 size={16} />
            </button>
          {/if}
        </div>
      {/each}

      {#if searchQuery && filteredProps.length === 0}
        <p class="text-center text-surface-500 text-sm py-4">
          No properties match "{searchQuery}"
        </p>
      {/if}
    </div>

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
        class="bg-surface-950-50 text-surface-50-950 p-3 rounded text-xs overflow-auto max-h-48 font-mono">{generateXml()}</pre>
    </div>
  {/if}
</div>
