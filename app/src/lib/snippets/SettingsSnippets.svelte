<script module lang="ts">
  import { Switch } from "@skeletonlabs/skeleton-svelte";
  import { open } from "@tauri-apps/plugin-dialog";
  import { FolderOpen, FileText } from "@lucide/svelte";

  export {
    SettingSwitch,
    SettingInput,
    SettingFolderPicker,
    SettingFilePicker,
    SettingSelect,
    SettingRadioGroup,
  };
</script>

{#snippet SettingSwitch(
  label: string,
  description: string,
  value: boolean,
  onChange: (v: boolean) => void,
)}
  <div
    class="flex items-start justify-between py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
  >
    <div class="flex-1 pr-4">
      <label
        class="block text-sm font-semibold text-surface-900-50"
        for="setting-switch-{label}">{label}</label
      >
      {#if description}
        <p class="text-xs text-surface-600-300 mt-1 leading-relaxed">
          {description}
        </p>
      {/if}
    </div>
    <Switch
      checked={value}
      name="setting-switch-{label}"
      onCheckedChange={(details) => onChange(details.checked)}
    >
      <Switch.Control>
        <Switch.Thumb />
      </Switch.Control>
      <Switch.HiddenInput />
    </Switch>
  </div>
{/snippet}

{#snippet SettingInput(
  label: string,
  description: string,
  value: string,
  onChange: (v: string) => void,
  placeholder?: string,
)}
  <div
    class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
  >
    <label
      class="block text-sm font-semibold text-surface-900-50 mb-2"
      for="setting-input-{label}">{label}</label
    >
    {#if description}
      <p class="text-xs text-surface-600-300 mb-2 leading-relaxed">
        {description}
      </p>
    {/if}
    <input
      id="setting-input-{label}"
      type="text"
      class="w-full px-4 py-2.5 rounded-lg bg-surface-100-900 border border-surface-300-700 text-surface-900-50 focus:outline-none focus:ring-1 focus:ring-primary-500/50 focus:border-primary-500 transition-all duration-200"
      placeholder={placeholder || ""}
      {value}
      oninput={(e) => onChange(e.currentTarget.value)}
    />
  </div>
{/snippet}

{#snippet SettingFolderPicker(
  label: string,
  description: string,
  value: string,
  onChange: (v: string) => void,
)}
  <div
    class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
  >
    <label
      class="block text-sm font-semibold text-surface-900-50 mb-2"
      for="setting-folder-{label}">{label}</label
    >
    {#if description}
      <p class="text-xs text-surface-600-300 mb-2 leading-relaxed">
        {description}
      </p>
    {/if}
    <div class="input-group grid grid-cols-[1fr_auto]">
      <input
        id="setting-folder-{label}"
        class="ig-input"
        type="text"
        placeholder="Select a folder..."
        {value}
        oninput={(e) => onChange(e.currentTarget.value)}
      />
      <button
        class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
        type="button"
        title="Browse folders"
        onclick={async () => {
          const selected = await open({
            directory: true,
            multiple: false,
          });
          if (selected && typeof selected === "string") {
            onChange(selected);
          }
        }}
      >
        <FolderOpen size={16} />
      </button>
    </div>
  </div>
{/snippet}

{#snippet SettingFilePicker(
  label: string,
  description: string,
  value: string,
  onChange: (v: string) => void,
  filters?: Array<{ name: string; extensions: string[] }>,
)}
  <div
    class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
  >
    <label
      class="block text-sm font-semibold text-surface-900-50 mb-2"
      for="setting-file-{label}">{label}</label
    >
    {#if description}
      <p class="text-xs text-surface-600-300 mb-2 leading-relaxed">
        {description}
      </p>
    {/if}
    <div class="input-group grid grid-cols-[1fr_auto]">
      <input
        id="setting-file-{label}"
        class="ig-input"
        type="text"
        placeholder="Select a file..."
        {value}
        oninput={(e) => onChange(e.currentTarget.value)}
      />
      <button
        class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
        type="button"
        title="Browse files"
        onclick={async () => {
          const selected = await open({
            multiple: false,
            filters: filters || [],
          });
          if (selected && typeof selected === "string") {
            onChange(selected);
          }
        }}
      >
        <FileText size={16} />
      </button>
    </div>
  </div>
{/snippet}

{#snippet SettingSelect(
  label: string,
  description: string,
  value: string,
  onChange: (v: string) => void,
  options: Array<{ value: string; label: string }>,
)}
  <div
    class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
  >
    <label
      class="block text-sm font-semibold text-surface-900-50 mb-2"
      for="setting-select-{label}">{label}</label
    >
    {#if description}
      <p class="text-xs text-surface-600-300 mb-2 leading-relaxed">
        {description}
      </p>
    {/if}
    <select
      id="setting-select-{label}"
      class="select"
      {value}
      onchange={(e) => onChange(e.currentTarget.value)}
    >
      {#each options as option (option.value)}
        <option value={option.value}>{option.label}</option>
      {/each}
    </select>
  </div>
{/snippet}

{#snippet SettingRadioGroup(
  label: string,
  description: string,
  value: string,
  onChange: (v: string) => void,
  options: Array<{ value: string; label: string }>,
)}
  <div
    class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
  >
    <p class="block text-sm font-semibold text-surface-900-50 mb-2">{label}</p>
    {#if description}
      <p class="text-xs text-surface-600-300 mb-2 leading-relaxed">
        {description}
      </p>
    {/if}
    <div class="space-y-3">
      {#each options as option (option.value)}
        <label class="flex items-center gap-3 cursor-pointer group">
          <div class="relative">
            <input
              type="radio"
              name={label}
              value={option.value}
              checked={value === option.value}
              onchange={() => onChange(option.value)}
              class="peer sr-only"
            />
            <div
              class="w-5 h-5 rounded-full border-2 border-surface-300-700 peer-checked:border-primary-500 peer-checked:bg-primary-500 transition-all duration-200 flex items-center justify-center"
            >
              <div
                class="w-2.5 h-2.5 rounded-full bg-white opacity-0 peer-checked:opacity-100 transition-opacity duration-200"
              ></div>
            </div>
          </div>
          <span
            class="text-sm text-surface-900-50 group-hover:text-primary-500 transition-colors"
            >{option.label}</span
          >
        </label>
      {/each}
    </div>
  </div>
{/snippet}
