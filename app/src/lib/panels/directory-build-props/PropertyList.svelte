<script lang="ts">
  import { Pencil, Trash2, Check, X } from "@lucide/svelte";
  import type { BuildProp, EditDraft } from "./types.ts";

  let {
    filteredProps,
    editDraft = $bindable(),
    searchQuery,
    onstartEdit,
    oncancelEdit,
    onsaveEdit,
    onremove,
  }: {
    filteredProps: BuildProp[];
    editDraft?: EditDraft | null;
    searchQuery: string;
    onstartEdit: (id: string) => void;
    oncancelEdit: (id: string) => void;
    onsaveEdit: (id: string) => void;
    onremove: (id: string) => void;
  } = $props();
</script>

<div class="flex flex-col gap-2">
  {#each filteredProps as prop (prop.id)}
    <div class="card bg-surface-50-950 shadow-sm p-3 flex items-center gap-3">
      {#if prop.editing && editDraft}
        <div class="flex-1 grid grid-cols-2 gap-3">
          <input
            class="input text-sm"
            type="text"
            bind:value={editDraft.name}
            onkeydown={(e) => e.key === "Enter" && onsaveEdit(prop.id)}
          />
          <input
            class="input text-sm"
            type="text"
            bind:value={editDraft.value}
            onkeydown={(e) => e.key === "Enter" && onsaveEdit(prop.id)}
          />
        </div>
        <button
          class="btn preset-filled-primary-500 p-2"
          onclick={() => onsaveEdit(prop.id)}
          title="Save"
        >
          <Check size={16} />
        </button>
        <button
          class="btn preset-tonal p-2"
          onclick={() => oncancelEdit(prop.id)}
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
          onclick={() => onstartEdit(prop.id)}
          title="Edit"
        >
          <Pencil size={16} />
        </button>
        <button
          class="btn preset-filled-error-500 p-2"
          onclick={() => onremove(prop.id)}
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
