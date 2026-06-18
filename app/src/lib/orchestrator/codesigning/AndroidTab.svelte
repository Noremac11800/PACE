<script lang="ts">
  import { Plus, Trash2, FolderOpen } from "@lucide/svelte";
  import type { AndroidConfig, CodesigningData } from "./types.ts";

  let {
    config = $bindable(),
    keys,
    onsave,
    onadd,
    onremove,
    onrename,
    onpickFile,
  }: {
    config: CodesigningData;
    keys: string[];
    onsave: () => void;
    onadd: () => void;
    onremove: (key: string) => void;
    onrename: (oldKey: string, newKey: string) => void;
    onpickFile: (field: keyof AndroidConfig, target: string) => void;
  } = $props();
</script>

<p class="text-sm text-surface-600-400">
  Configure code signing settings for Android apps using keystore files. The "*"
  entry is used as the default.
</p>
{#each keys as key (key)}
  <div
    class="flex flex-col gap-3 border-b border-surface-200-800 pb-4 last:border-0"
  >
    <div class="flex items-center gap-2">
      <span
        class="text-xs font-medium text-surface-600-400 uppercase tracking-wide"
        >Keystore Name</span
      >
      {#if key !== "*"}
        <button
          class="ml-auto btn-icon text-error-500 hover:text-error-600 transition-colors"
          onclick={() => onremove(key)}
          title="Remove keystore"><Trash2 size={14} /></button
        >
      {/if}
    </div>
    <input
      type="text"
      class="input font-mono text-sm"
      value={key}
      disabled={key === "*"}
      placeholder="keystore-name"
      onchange={(e) => onrename(key, (e.target as HTMLInputElement).value)}
    />
    <div class="flex flex-col gap-1">
      <label for="keystore-{key}" class="text-xs font-medium text-surface-600-400"
        >Keystore Path</label
      >
      <div class="input-group grid grid-cols-[1fr_auto]">
        <input
          id="keystore-{key}"
          type="text"
          class="ig-input font-mono text-sm"
          placeholder="$HOME/Certificates/myapp.keystore"
          value={config.android[key]?.KeystorePath || ""}
          oninput={(e) => {
            config.android[key].KeystorePath = (
              e.target as HTMLInputElement
            ).value;
            config = { ...config };
            onsave();
          }}
        />
        <button
          class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
          type="button"
          onclick={() => onpickFile("KeystorePath", key)}
          title="Browse for keystore file"><FolderOpen size={16} /></button
        >
      </div>
    </div>
    <div class="flex flex-col gap-1">
      <label
        for="codesigninfo-{key}"
        class="text-xs font-medium text-surface-600-400"
        >Codesign Info Text Path</label
      >
      <div class="input-group grid grid-cols-[1fr_auto]">
        <input
          id="codesigninfo-{key}"
          type="text"
          class="ig-input font-mono text-sm"
          placeholder="$HOME/Certificates/myapp.txt"
          value={config.android[key]?.CodesignInfoTxtPath || ""}
          oninput={(e) => {
            config.android[key].CodesignInfoTxtPath = (
              e.target as HTMLInputElement
            ).value;
            config = { ...config };
            onsave();
          }}
        />
        <button
          class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
          type="button"
          onclick={() => onpickFile("CodesignInfoTxtPath", key)}
          title="Browse for codesign info file"><FolderOpen size={16} /></button
        >
      </div>
      <p class="text-xs text-surface-500-400 mt-1">
        Text file containing keystore password and key alias information.
      </p>
    </div>
  </div>
{/each}
<button
  class="btn preset-tonal flex items-center gap-1.5 text-xs py-1 px-2 self-start"
  onclick={onadd}
>
  <Plus size={14} /> Add Keystore
</button>
