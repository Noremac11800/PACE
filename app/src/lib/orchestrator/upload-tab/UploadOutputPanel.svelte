<script lang="ts">
  import { Check, X, Loader } from "@lucide/svelte";
  import type { PackageFile, UploadStatus } from "./types";

  let {
    selectedPackages,
    availablePackages,
    uploadStatuses,
    uploadProgress,
    isUploading,
    outputLines,
    outputRef = $bindable(),
  }: {
    selectedPackages: string[];
    availablePackages: PackageFile[];
    uploadStatuses: Record<string, UploadStatus>;
    uploadProgress: Record<string, string>;
    isUploading: boolean;
    outputLines: { type: "out" | "err"; text: string }[];
    outputRef?: HTMLDivElement | null;
  } = $props();
</script>

<!-- Upload Status -->
{#if isUploading || Object.keys(uploadStatuses).length > 0}
  <div class="card bg-surface-50-950 p-3 flex flex-col gap-3">
    <span
      class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
    >
      Upload Status
    </span>
    <div class="flex flex-col gap-2">
      {#each selectedPackages as packagePath (packagePath)}
        {@const pkg = availablePackages.find((p) => p.path === packagePath)}
        {#if pkg}
          {@const status = uploadStatuses[packagePath] || "pending"}
          {@const progress = uploadProgress[packagePath] || ""}
          <div
            class="flex items-center gap-3 p-2 rounded bg-surface-100-900 border border-surface-300-700"
          >
            <div
              class="flex items-center justify-center w-8 h-8 rounded-full shrink-0 {status ===
              'success'
                ? 'bg-success-500/20'
                : status === 'error'
                  ? 'bg-error-500/20'
                  : status === 'uploading'
                    ? 'bg-primary-500/20'
                    : 'bg-surface-300-700/50'}"
            >
              {#if status === "success"}
                <Check size={16} class="text-success-500" />
              {:else if status === "error"}
                <X size={16} class="text-error-500" />
              {:else if status === "uploading"}
                <Loader size={16} class="animate-spin text-primary-500" />
              {:else}
                <div class="w-4 h-4 rounded-full bg-surface-500-400"></div>
              {/if}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-surface-900-100 truncate">
                {pkg.name}
              </div>
              <div class="text-xs text-surface-500-400">
                {pkg.platform} • {pkg.buildConfig}
                {#if progress}
                  <span class="text-primary-500 ml-2">{progress}</span>
                {/if}
              </div>
            </div>
            <div
              class="text-xs font-medium uppercase {status === 'success'
                ? 'text-success-500'
                : status === 'error'
                  ? 'text-error-500'
                  : status === 'uploading'
                    ? 'text-primary-500'
                    : 'text-surface-500-400'}"
            >
              {status}
            </div>
          </div>
        {/if}
      {/each}
    </div>
  </div>
{/if}

<!-- Output -->
{#if outputLines.length > 0}
  <div class="card bg-surface-50-950 p-3 flex flex-col gap-2">
    <span
      class="text-xs font-semibold text-surface-600-400 uppercase tracking-wide"
      >Output</span
    >
    <div
      bind:this={outputRef}
      class="h-48 overflow-auto bg-surface-200-800 rounded p-3 font-mono text-xs leading-relaxed"
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
