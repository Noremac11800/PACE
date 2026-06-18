<script lang="ts">
  import { Plus, Trash2, Eye, EyeOff } from "@lucide/svelte";
  import type { CodesigningData } from "./types.ts";

  let {
    config = $bindable(),
    keys,
    onsave,
    onadd,
    onremove,
    onrename,
  }: {
    config: CodesigningData;
    keys: string[];
    onsave: () => void;
    onadd: () => void;
    onremove: (key: string) => void;
    onrename: (oldKey: string, newKey: string) => void;
  } = $props();

  let showThumbprint = $state<Record<string, boolean>>({});
</script>

<p class="text-sm text-surface-600-400">
  Configure code signing settings for Windows apps using certificate
  thumbprint. The "*" entry is used as the default.
</p>
{#each keys as key (key)}
  <div
    class="flex flex-col gap-3 border-b border-surface-200-800 pb-4 last:border-0"
  >
    <div class="flex items-center gap-2">
      <span
        class="text-xs font-medium text-surface-600-400 uppercase tracking-wide"
        >Certificate Name</span
      >
      {#if key !== "*"}
        <button
          class="ml-auto btn-icon text-error-500 hover:text-error-600 transition-colors"
          onclick={() => onremove(key)}
          title="Remove certificate"><Trash2 size={14} /></button
        >
      {/if}
    </div>
    <input
      type="text"
      class="input font-mono text-sm"
      value={key}
      disabled={key === "*"}
      placeholder="cert-name"
      onchange={(e) => onrename(key, (e.target as HTMLInputElement).value)}
    />
    <div class="flex flex-col gap-1">
      <div class="flex items-center justify-between">
        <label
          for="thumbprint-{key}"
          class="text-xs font-medium text-surface-600-400"
          >Package Certificate Thumbprint</label
        >
        <button
          class="btn-icon text-surface-500-400 hover:text-surface-700-300"
          onclick={() => (showThumbprint[key] = !showThumbprint[key])}
          title={showThumbprint[key] ? "Hide" : "Show"}
        >
          {#if showThumbprint[key]}<EyeOff size={14} />{:else}<Eye
              size={14}
            />{/if}
        </button>
      </div>
      <input
        id="thumbprint-{key}"
        type={showThumbprint[key] ? "text" : "password"}
        class="input font-mono text-sm"
        placeholder="Certificate thumbprint hash"
        value={config.windows[key]?.PackageCertificateThumbprint || ""}
        oninput={(e) => {
          config.windows[key].PackageCertificateThumbprint = (
            e.target as HTMLInputElement
          ).value;
          config = { ...config };
          onsave();
        }}
      />
    </div>
  </div>
{/each}
<button
  class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2 self-start"
  onclick={onadd}
>
  <Plus size={14} /> Add Certificate
</button>
