<script lang="ts">
  import { Terminal } from "@lucide/svelte";
  import CopyButton from "$lib/components/CopyButton.svelte";

  let {
    commandPreview,
    isRunning,
    progress,
    progressLabel,
    progressBarColor,
    projectsBuilt,
    projectsTotal,
    filteredProjectsCount,
    elapsedSeconds,
    outputLines,
    outputRef = $bindable(),
  }: {
    commandPreview: string;
    isRunning: boolean;
    progress: number;
    progressLabel: string;
    progressBarColor: string;
    projectsBuilt: number;
    projectsTotal: number;
    filteredProjectsCount: number;
    elapsedSeconds: number;
    outputLines: { text: string; type: "out" | "err" }[];
    outputRef?: HTMLDivElement;
  } = $props();

  function formatElapsed(s: number): string {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec.toString().padStart(2, "0")}s` : `${sec}s`;
  }

  let total = $derived(projectsTotal || filteredProjectsCount);
</script>

<!-- Command preview -->
<div class="card bg-surface-50-950 p-4">
  <div class="flex items-center justify-between gap-2 mb-2">
    <div class="flex items-center gap-2">
      <Terminal size={16} class="text-primary-500 shrink-0" />
      <span
        class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
        >Command Preview</span
      >
    </div>
    <CopyButton text={commandPreview} />
  </div>
  <code
    class="block text-sm font-mono bg-surface-200-800 px-3 py-2 rounded break-all whitespace-pre-wrap text-surface-900-100"
  >
    {commandPreview}
  </code>
</div>

<!-- Progress -->
{#if isRunning || progress > 0}
  <div class="card bg-surface-50-950 p-4 flex flex-col gap-3">
    <!-- Label + project counter + timer -->
    <div class="flex items-center justify-between gap-2 text-xs">
      <span class="text-surface-600-400 truncate">{progressLabel}</span>
      <span
        class="font-mono text-surface-600-400 shrink-0 flex items-center gap-2"
      >
        {#if total > 0 && progress > 0 && progress < 100}
          <span>{projectsBuilt} / {total} projects</span>
        {:else}
          <span>{progress}%</span>
        {/if}
        <span class="text-surface-400-500">·</span>
        <span>{formatElapsed(elapsedSeconds)}</span>
      </span>
    </div>

    <!-- Progress bar -->
    <div class="w-full h-2 bg-surface-200-800 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300 {progressBarColor}"
        style="width: {progress}%"
      ></div>
    </div>

    <!-- Per-project segment strip (when we know the total) -->
    {#if total > 0 && total <= 50 && progress > 0 && progress < 100}
      <div class="flex gap-0.5">
        {#each { length: total } as _, i (i)}
          <div
            class="h-1.5 flex-1 rounded-full transition-colors duration-200 {i <
            projectsBuilt
              ? progressBarColor
              : 'bg-surface-200-800'}"
          ></div>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<!-- Output log -->
{#if outputLines.length > 0}
  <div class="card bg-surface-50-950 p-4 flex flex-col gap-2">
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
          class="whitespace-pre {line.type === 'err'
            ? 'text-red-500'
            : 'text-surface-900-100'}"
        >
          {line.text}
        </div>
      {/each}
    </div>
  </div>
{/if}
