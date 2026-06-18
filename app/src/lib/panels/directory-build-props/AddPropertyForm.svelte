<script lang="ts">
  import { Check, X, TriangleAlert } from "@lucide/svelte";

  let {
    newName = $bindable(""),
    newValue = $bindable(""),
    addError,
    onadd,
    oncancel,
  }: {
    newName?: string;
    newValue?: string;
    addError: string;
    onadd: () => void;
    oncancel: () => void;
  } = $props();
</script>

<div class="card bg-surface-50-950 shadow-md p-4">
  <h4 class="text-sm font-semibold text-surface-700-300 mb-3">New Property</h4>
  <div class="flex flex-col gap-3">
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label for="new-prop-name" class="block text-xs text-surface-700-300 mb-1"
          >Name</label
        >
        <input
          id="new-prop-name"
          class="input text-sm"
          type="text"
          placeholder="e.g. TargetFramework"
          bind:value={newName}
          onkeydown={(e) => e.key === "Enter" && onadd()}
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
          onkeydown={(e) => e.key === "Enter" && onadd()}
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
        onclick={oncancel}
      >
        <X size={16} />
        Cancel
      </button>
      <button
        class="btn preset-filled-primary-500 text-sm flex items-center gap-1"
        onclick={onadd}
      >
        <Check size={16} />
        Add
      </button>
    </div>
  </div>
</div>
