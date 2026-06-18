<script lang="ts">
  import { Check, FolderOpen } from "@lucide/svelte";
  import type { PackageFile } from "./types";
  import { getPlatformIcon, getApiPlatform } from "./platform";

  let {
    pkg,
    selected,
    ontoggle,
    onreveal,
  }: {
    pkg: PackageFile;
    selected: boolean;
    ontoggle: () => void;
    onreveal: () => void;
  } = $props();

  const Icon = $derived(getPlatformIcon(pkg.platform));
</script>

<div
  class="flex items-center gap-3 p-3 rounded border transition-colors {selected
    ? 'bg-primary-500/10 border-primary-500'
    : 'bg-surface-100-900 border-surface-300-700 hover:border-primary-500/50'}"
>
  <button
    type="button"
    onclick={ontoggle}
    class="flex items-center gap-3 flex-1 min-w-0 text-left"
  >
    <div
      class="flex items-center justify-center w-5 h-5 rounded border shrink-0 {selected
        ? 'bg-primary-500 border-primary-500'
        : 'border-surface-500'}"
    >
      {#if selected}
        <Check size={12} class="text-white" />
      {/if}
    </div>
    <Icon
      size={16}
      class={selected ? "text-primary-500" : "text-surface-500-400"}
    />
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium text-surface-900-100 truncate">
        {pkg.name}
      </div>
      <div class="text-xs text-surface-500-400">
        {getApiPlatform(pkg.platform)} • {pkg.buildConfig}
      </div>
      <div
        class="text-xs text-surface-500-400 truncate"
        style="direction: rtl; text-align: left;"
        title={pkg.path}
      >
        {pkg.path}
      </div>
    </div>
  </button>
  <button
    type="button"
    onclick={onreveal}
    class="p-1.5 rounded hover:bg-surface-200-800 text-surface-500-400 hover:text-primary-500 transition-colors shrink-0"
    title="Show in folder"
  >
    <FolderOpen size={14} />
  </button>
</div>
