<script lang="ts">
  import { Plus, Trash2, Eye, EyeOff } from "@lucide/svelte";
  import type { CodesigningData } from "./types.ts";

  let {
    config = $bindable(),
    bundleIds,
    onsave,
    onadd,
    onremove,
    onrename,
  }: {
    config: CodesigningData;
    bundleIds: string[];
    onsave: () => void;
    onadd: () => void;
    onremove: (bundleId: string) => void;
    onrename: (oldId: string, newId: string) => void;
  } = $props();

  let showProvision = $state<Record<string, boolean>>({});
</script>

<p class="text-sm text-surface-600-400">
  Configure code signing settings for iOS apps. The "*" entry is used as the
  default for all bundle IDs.
</p>
{#each bundleIds as bundleId (bundleId)}
  <div
    class="flex flex-col gap-3 border-b border-surface-200-800 pb-4 last:border-0"
  >
    <div class="flex items-center gap-2">
      <span
        class="text-xs font-medium text-surface-600-400 uppercase tracking-wide"
        >Bundle ID</span
      >
      {#if bundleId !== "*"}
        <button
          class="ml-auto btn-icon text-error-500 hover:text-error-600 transition-colors"
          onclick={() => onremove(bundleId)}
          title="Remove bundle ID"><Trash2 size={14} /></button
        >
      {/if}
    </div>
    <input
      type="text"
      class="input font-mono text-sm"
      value={bundleId}
      disabled={bundleId === "*"}
      placeholder="com.example.app"
      onchange={(e) => onrename(bundleId, (e.target as HTMLInputElement).value)}
    />
    <div class="flex flex-col gap-1">
      <label
        for="codesign-key-{bundleId}"
        class="text-xs font-medium text-surface-600-400">Codesign Key</label
      >
      <input
        id="codesign-key-{bundleId}"
        type="text"
        class="input text-sm"
        placeholder="iPhone Distribution: Company Name"
        value={config.ios[bundleId]?.CodesignKey || ""}
        oninput={(e) => {
          config.ios[bundleId].CodesignKey = (
            e.target as HTMLInputElement
          ).value;
          config = { ...config };
          onsave();
        }}
      />
    </div>
    <div class="flex flex-col gap-1">
      <div class="flex items-center justify-between">
        <label
          for="codesign-provision-{bundleId}"
          class="text-xs font-medium text-surface-600-400"
          >Codesign Provision</label
        >
        <button
          class="btn-icon text-surface-500-400 hover:text-surface-700-300"
          onclick={() => (showProvision[bundleId] = !showProvision[bundleId])}
          title={showProvision[bundleId] ? "Hide" : "Show"}
        >
          {#if showProvision[bundleId]}<EyeOff size={14} />{:else}<Eye
              size={14}
            />{/if}
        </button>
      </div>
      <input
        id="codesign-provision-{bundleId}"
        type={showProvision[bundleId] ? "text" : "password"}
        class="input text-sm"
        placeholder="Provisioning profile identifier"
        value={config.ios[bundleId]?.CodesignProvision || ""}
        oninput={(e) => {
          config.ios[bundleId].CodesignProvision = (
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
  <Plus size={14} /> Add Bundle ID
</button>
