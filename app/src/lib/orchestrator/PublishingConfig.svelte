<script lang="ts">
  import { Globe } from "@lucide/svelte";
</script>

<div class="h-full flex flex-col p-4">
  <div class="flex items-center gap-2 mb-4">
    <Globe size={18} class="text-primary-500" />
    <span class="font-semibold text-surface-900-100"
      >Publishing Configuration</span
    >
  </div>
  <div class="card bg-surface-50-950 p-6 flex flex-col gap-4">
    <p class="text-sm text-surface-600-400">
      Configure app store publishing settings.
    </p>
    <div class="flex flex-col gap-3">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-600-400"
          >App Store Connect API Key</label
        >
        <input type="text" class="input text-sm" placeholder="API Key ID" />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-600-400"
          >Google Play Service Account</label
        >
        <input
          type="text"
          class="input text-sm"
          placeholder="Service account JSON path"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-surface-600-400"
          >Microsoft Store Partner Center</label
        >
        <input type="text" class="input text-sm" placeholder="Tenant ID" />
      </div>
    </div>
  </div>
</div>
