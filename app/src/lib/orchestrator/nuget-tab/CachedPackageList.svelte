<script lang="ts">
  import { CircleAlert } from "@lucide/svelte";
  import type { CachedPackage } from "./types.ts";

  let {
    total,
    filtered,
  }: {
    total: CachedPackage[];
    filtered: CachedPackage[];
  } = $props();
</script>

<div class="text-xs text-surface-500-400">
  {filtered.length} matching package{filtered.length === 1 ? "" : "s"} (of
  {total.length} total)
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
    {#each filtered as pkg (pkg.name)}
      <div
        class="flex items-center gap-2 px-2 py-1.5 rounded bg-surface-100-900/40"
      >
        <span class="font-mono text-xs text-surface-900-100 flex-1 truncate"
          >{pkg.name}</span
        >
        <div class="flex flex-wrap gap-1 shrink-0">
          {#each pkg.versions as ver (ver)}
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
