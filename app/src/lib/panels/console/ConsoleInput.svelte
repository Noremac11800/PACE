<script lang="ts">
  import { Play, Square } from "@lucide/svelte";

  let {
    commandInput = $bindable(""),
    inputRef = $bindable(),
    isRunning,
    workingDirectory,
    historyCount,
    onkeydown,
    oncancel,
    onrun,
  }: {
    commandInput?: string;
    inputRef?: HTMLInputElement;
    isRunning: boolean;
    workingDirectory: string;
    historyCount: number;
    onkeydown: (e: KeyboardEvent) => void;
    oncancel: () => void;
    onrun: () => void;
  } = $props();
</script>

<div class="p-3 bg-surface-200-800 border-t border-surface-300-700">
  <div class="flex items-center gap-2">
    <span class="text-primary-500 font-mono text-sm font-bold">$</span>
    <input
      bind:this={inputRef}
      bind:value={commandInput}
      {onkeydown}
      placeholder={isRunning
        ? "Running... (Ctrl+C to cancel)"
        : "Type a command..."}
      disabled={isRunning}
      class="flex-1 bg-transparent border-none outline-none font-mono text-sm text-surface-900-100 placeholder:text-surface-500-600"
      spellcheck="false"
      autocomplete="off"
    />

    {#if isRunning}
      <button
        class="btn preset-filled-error-500 p-2"
        onclick={oncancel}
        title="Cancel command"
      >
        <Square size={16} />
      </button>
    {:else}
      <button
        class="btn preset-filled-primary-500 p-2"
        onclick={onrun}
        disabled={!commandInput.trim()}
        title="Run command"
      >
        <Play size={16} />
      </button>
    {/if}
  </div>

  <!-- Status Bar -->
  <div class="flex items-center justify-between mt-2 text-xs text-surface-500">
    <span class="font-mono">{workingDirectory}</span>
    <span>
      {isRunning ? "Running..." : "Ready"}
      {#if historyCount > 0}
        • {historyCount} in history
      {/if}
    </span>
  </div>
</div>
