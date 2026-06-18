<script lang="ts">
  import { Database, ExternalLink, TriangleAlert, Check } from "@lucide/svelte";
  import { openUrl } from "@tauri-apps/plugin-opener";
  import { settings } from "$lib/settings.svelte";

  const endpointUrl = $derived(settings.general.storageEndpointUrl);
  const endpointUrlValid = $derived(
    !endpointUrl ||
      endpointUrl.startsWith("http://") ||
      endpointUrl.startsWith("https://"),
  );

  async function openEndpoint() {
    let url = settings.general.storageEndpointUrl;
    if (!url) return;
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = "https://" + url;
    }
    try {
      await openUrl(url);
    } catch (e) {
      console.error("Failed to open URL:", e);
    }
  }
</script>

<section id="storage" class="pb-8">
  <h2 class="h2 text-primary-500 mb-4 flex items-center gap-2">
    <Database size={24} class="text-primary-500" />
    Storage
  </h2>
  <div class="space-y-1">
    <!-- Storage Endpoint URL Input with Open Button -->
    <div
      class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
    >
      <label
        class="block text-sm font-semibold text-surface-900-50 mb-2"
        for="storage-endpoint-url">Application storage endpoint URL</label
      >
      <p class="text-xs text-surface-600-300 mb-2 leading-relaxed">
        Configure the endpoint URL for application storage uploads
      </p>
      <div class="input-group grid grid-cols-[1fr_auto]">
        <input
          id="storage-endpoint-url"
          type="text"
          class="ig-input {endpointUrl && !endpointUrlValid
            ? 'border-warning-500 focus:border-warning-500'
            : ''}"
          placeholder="https://company.storage.com"
          bind:value={settings.general.storageEndpointUrl}
        />
        <button
          class="ig-cell btn preset-tonal hover:preset-filled-primary-500 transition-colors"
          type="button"
          title="Open in browser"
          onclick={openEndpoint}
        >
          <ExternalLink size={16} />
        </button>
      </div>
      {#if endpointUrl && !endpointUrlValid}
        <div
          class="flex items-center gap-1.5 mt-2 text-xs text-warning-600-400"
        >
          <TriangleAlert size={12} />
          <span>URL must start with http:// or https://</span>
        </div>
      {:else if endpointUrl && endpointUrlValid}
        <div
          class="flex items-center gap-1.5 mt-2 text-xs text-success-600-400"
        >
          <Check size={12} />
          <span>Valid URL format</span>
        </div>
      {/if}
    </div>
  </div>
</section>
