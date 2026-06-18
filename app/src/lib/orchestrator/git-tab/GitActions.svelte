<script lang="ts">
  import {
    RefreshCw,
    Download,
    ArrowDownFromLine,
    Loader,
  } from "@lucide/svelte";

  let {
    cloning,
    pulling,
    refreshing,
    disabled,
    onclone,
    onpull,
    onrefresh,
  }: {
    cloning: boolean;
    pulling: boolean;
    refreshing: boolean;
    disabled: boolean;
    onclone: () => void;
    onpull: () => void;
    onrefresh: () => void;
  } = $props();
</script>

<div class="flex items-center gap-2">
  <button
    class="btn preset-tonal flex items-center gap-2 px-3 py-2 hover:preset-filled-primary-500 transition-colors"
    onclick={onclone}
    disabled={cloning || pulling || disabled}
    title="Clone all missing repositories"
  >
    {#if cloning}
      <Loader size={16} class="animate-spin" />
      <span class="text-sm">Cloning...</span>
    {:else}
      <Download size={16} />
      <span class="text-sm">Clone</span>
    {/if}
  </button>
  <button
    class="btn preset-tonal flex items-center gap-2 px-3 py-2 hover:preset-filled-primary-500 transition-colors"
    onclick={onpull}
    disabled={cloning || pulling || disabled}
    title="Pull all repositories"
  >
    {#if pulling}
      <Loader size={16} class="animate-spin" />
      <span class="text-sm">Pulling...</span>
    {:else}
      <ArrowDownFromLine size={16} />
      <span class="text-sm">Pull</span>
    {/if}
  </button>
  <button
    class="btn preset-tonal p-2 hover:preset-filled-primary-500 transition-colors"
    onclick={onrefresh}
    disabled={refreshing || cloning || pulling || disabled}
    title="Refresh all git statuses"
  >
    <RefreshCw size={16} class={refreshing ? "animate-spin" : ""} />
  </button>
</div>
