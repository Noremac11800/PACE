<script lang="ts">
  import {
    Database,
    ExternalLink,
    TriangleAlert,
    Check,
    Trash2,
    LoaderCircle,
  } from "@lucide/svelte";
  import { openUrl } from "@tauri-apps/plugin-opener";
  import { BaseDirectory, exists, remove } from "@tauri-apps/plugin-fs";
  import { confirm } from "@tauri-apps/plugin-dialog";
  import { homeDir, join } from "@tauri-apps/api/path";
  import { settings } from "$lib/state/settings.svelte";

  const CACHE_RELATIVE_PATH = ".pace/cache";

  let clearingCache = $state(false);
  let cacheStatus = $state<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  let cachePath = $state("");

  $effect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const resolved = await join(await homeDir(), ".pace", "cache");
        if (!cancelled) cachePath = resolved;
      } catch (e) {
        console.error("Failed to resolve cache path:", e);
      }
    })();
    return () => {
      cancelled = true;
    };
  });

  async function clearCache() {
    const confirmed = await confirm(
      `Delete the cache directory at ${cachePath || "~/.pace/cache"}? This cannot be undone.`,
      { title: "Clear cache", kind: "warning" },
    );
    if (!confirmed) return;

    clearingCache = true;
    cacheStatus = null;
    try {
      const cacheExists = await exists(CACHE_RELATIVE_PATH, {
        baseDir: BaseDirectory.Home,
      });
      if (!cacheExists) {
        cacheStatus = { type: "success", message: "Cache is already empty" };
        return;
      }
      await remove(CACHE_RELATIVE_PATH, {
        baseDir: BaseDirectory.Home,
        recursive: true,
      });
      cacheStatus = { type: "success", message: "Cache cleared" };
    } catch (e) {
      console.error("Failed to clear cache:", e);
      cacheStatus = { type: "error", message: `Failed to clear cache: ${e}` };
    } finally {
      clearingCache = false;
    }
  }

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

    <!-- Clear cache -->
    <div
      class="py-4 px-4 rounded-lg hover:bg-surface-100-900/50 transition-colors"
    >
      <span class="block text-sm font-semibold text-surface-900-50 mb-2"
        >Clear cache</span
      >
      <p class="text-xs text-surface-600-300 mb-3 leading-relaxed">
        Permanently delete the PACE cache directory
        <code class="text-xs">{cachePath || "~/.pace/cache"}</code>
      </p>
      <button
        type="button"
        class="btn preset-filled-error-500 flex items-center gap-2 text-sm"
        disabled={clearingCache}
        onclick={clearCache}
      >
        {#if clearingCache}
          <LoaderCircle size={16} class="animate-spin" />
          Clearing...
        {:else}
          <Trash2 size={16} />
          Clear cache
        {/if}
      </button>
      {#if cacheStatus}
        <div
          class="flex items-center gap-1.5 mt-2 text-xs {cacheStatus.type ===
          'success'
            ? 'text-success-600-400'
            : 'text-error-600-400'}"
        >
          {#if cacheStatus.type === "success"}
            <Check size={12} />
          {:else}
            <TriangleAlert size={12} />
          {/if}
          <span>{cacheStatus.message}</span>
        </div>
      {/if}
    </div>
  </div>
</section>
