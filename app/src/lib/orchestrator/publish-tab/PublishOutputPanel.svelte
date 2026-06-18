<script lang="ts">
  import { Check, X, Loader } from "@lucide/svelte";
  import { PLATFORMS, type Platform, type BuildStatus } from "./platforms";

  let {
    isRunning,
    buildStatuses,
    orderedSelectedPlatforms,
    progress,
    progressLabel,
    progressBarColor,
    elapsedSeconds,
    outputLines,
    outputRef = $bindable(),
  }: {
    isRunning: boolean;
    buildStatuses: Record<string, BuildStatus>;
    orderedSelectedPlatforms: Platform[];
    progress: number;
    progressLabel: string;
    progressBarColor: string;
    elapsedSeconds: number;
    outputLines: { text: string; type: "out" | "err" }[];
    outputRef?: HTMLDivElement;
  } = $props();

  function formatElapsed(s: number): string {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec.toString().padStart(2, "0")}s` : `${sec}s`;
  }
</script>

<!-- Build Status -->
{#if isRunning || Object.keys(buildStatuses).length > 0}
  <div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <span
        class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
      >
        Build Status
      </span>
      <span
        class="font-mono text-xs text-surface-600-400 flex items-center gap-2"
      >
        <span>{progress}%</span>
        <span class="text-surface-400-500">·</span>
        <span>{formatElapsed(elapsedSeconds)}</span>
      </span>
    </div>

    <div class="w-full h-2 bg-surface-200-800 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300 {progressBarColor}"
        style="width: {progress}%"
      ></div>
    </div>

    <div class="flex flex-col gap-2">
      {#each orderedSelectedPlatforms as platform (platform)}
        {@const platformConfig = PLATFORMS.find((p) => p.id === platform)}
        {@const Icon = platformConfig?.icon}
        {@const status = buildStatuses[platform] || "pending"}
        <div
          class="flex items-center gap-3 p-2 rounded bg-surface-100-900 border border-surface-300-700"
        >
          <div
            class="flex items-center justify-center w-8 h-8 rounded-full shrink-0 {status ===
            'success'
              ? 'bg-success-500/20'
              : status === 'error'
                ? 'bg-error-500/20'
                : status === 'building'
                  ? 'bg-primary-500/20'
                  : 'bg-surface-300-700/50'}"
          >
            {#if status === "success"}
              <Check size={16} class="text-success-500" />
            {:else if status === "error"}
              <X size={16} class="text-error-500" />
            {:else if status === "building"}
              <Loader size={16} class="animate-spin text-primary-500" />
            {:else}
              <div class="w-4 h-4 rounded-full bg-surface-500-400"></div>
            {/if}
          </div>
          <div class="flex-1 min-w-0">
            <div
              class="text-sm font-medium text-surface-900-100 flex items-center gap-2"
            >
              {#if Icon}
                <Icon size={14} />
              {/if}
              <span>{platformConfig?.label || platform}</span>
            </div>
          </div>
          <div
            class="text-xs font-medium uppercase {status === 'success'
              ? 'text-success-500'
              : status === 'error'
                ? 'text-error-500'
                : status === 'building'
                  ? 'text-primary-500'
                  : 'text-surface-500-400'}"
          >
            {status}
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<!-- Output log -->
{#if outputLines.length > 0}
  <div class="card bg-surface-50-950 p-3 flex flex-col gap-2">
    <span
      class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
      >Output</span
    >
    <div
      bind:this={outputRef}
      class="h-60 overflow-auto bg-surface-200-800 rounded p-3 font-mono text-xs leading-relaxed"
    >
      {#each outputLines as line, i (i)}
        <div
          class="{line.type === 'err'
            ? 'text-error-400'
            : 'text-surface-900-100'} wrap-break-word"
        >
          {line.text}
        </div>
      {/each}
    </div>
  </div>
{/if}
