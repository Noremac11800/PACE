<script lang="ts">
  import { Check, X, Loader } from "@lucide/svelte";
  import type { Snippet } from "svelte";

  let {
    name,
    found,
    statusText,
    border = true,
    icon,
    action,
  }: {
    name: string;
    found: boolean | undefined;
    statusText: string;
    border?: boolean;
    icon: Snippet;
    action?: Snippet;
  } = $props();
</script>

<div
  class="flex items-center justify-between py-2"
  class:border-b={border}
  class:border-surface-200-800={border}
>
  <div class="flex items-center gap-3">
    <div class="ig-cell preset-tonal p-2 rounded">
      {@render icon()}
    </div>
    <div>
      <p class="font-medium">{name}</p>
      <p class="text-xs text-surface-700-300">{statusText}</p>
    </div>
  </div>
  <div>
    {#if found === undefined}
      <Loader size={20} class="animate-spin text-surface-500" />
    {:else if found}
      <span class="chip preset-filled-success-500 flex items-center gap-1">
        <Check size={16} />
        Ready
      </span>
    {:else}
      <div class="flex items-center gap-2">
        <span class="chip preset-filled-error-500 flex items-center gap-1">
          <X size={16} />
          Missing
        </span>
        {#if action}
          {@render action()}
        {/if}
      </div>
    {/if}
  </div>
</div>
