<script lang="ts">
  import { Download, ArrowRight } from "@lucide/svelte";
  import AnimatedBackground from "./AnimatedBackground.svelte";
  import { updateStatus } from "$lib/update-status.svelte";
  import { View } from "./view-types";

  interface Props {
    onGoToPanel?: (view: View) => void;
  }

  let { onGoToPanel }: Props = $props();

  let hasUpdates = $derived(
    updateStatus.cli.updateAvailable || updateStatus.app.updateAvailable,
  );
</script>

<div class="relative min-h-full flex items-center justify-center">
  <AnimatedBackground />
  <div
    class="card bg-surface-50-950/90 shadow-md p-8 text-center max-w-md relative z-10"
  >
    <img src="/appicon.svg" alt="PACE" class="h-16 w-16 mx-auto mb-4" />
    <h1 class="h1 text-primary-500 mb-2">Welcome to PACE</h1>
    <p class="text-surface-700-300 mb-4">
      Project Automation and Configuration Engine
    </p>
    <p class="text-sm text-surface-700-300">
      Use the sidebar to navigate between views.
    </p>

    {#if hasUpdates}
      <button
        class="mt-4 w-full flex items-center justify-between gap-2 rounded-lg bg-warning-500/10 border border-warning-500/30 px-4 py-3 text-sm text-warning-500 hover:bg-warning-500/20 transition-colors"
        onclick={() => onGoToPanel?.(View.UPDATES)}
      >
        <span class="flex items-center gap-2">
          <Download size={16} />
          Updates available
        </span>
        <ArrowRight size={16} />
      </button>
    {/if}
  </div>
</div>
