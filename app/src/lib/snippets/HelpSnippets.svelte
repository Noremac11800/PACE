<script module lang="ts">
  import CopyButton from "$lib/components/CopyButton.svelte";

  export { CodeBlock, RefTable, KeyHint };
</script>

{#snippet CodeBlock(code: string)}
  <div class="relative group my-2">
    <pre
      class="bg-surface-900-100 text-surface-100-900 p-3 pr-12 rounded-lg text-sm font-mono overflow-x-auto whitespace-pre border border-surface-200-800">{code}</pre>
    <div
      class="absolute top-2 right-2 opacity-60 group-hover:opacity-100 transition-opacity"
    >
      <CopyButton text={code} size={14} />
    </div>
  </div>
{/snippet}

{#snippet RefTable(
  headers: string[],
  rows: {
    cells: { text: string; mono?: boolean; accent?: boolean }[];
  }[],
)}
  <div class="overflow-x-auto rounded-lg border border-surface-200-800">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-surface-100-900/60">
          {#each headers as h}
            <th
              class="text-left py-2.5 px-4 text-surface-500 font-semibold text-xs uppercase tracking-wide"
              >{h}</th
            >
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as row, i}
          <tr
            class={i < rows.length - 1
              ? "border-b border-surface-200-800"
              : ""}
          >
            {#each row.cells as cell}
              <td
                class="py-2.5 px-4 align-top {cell.mono
                  ? 'font-mono text-[13px]'
                  : ''} {cell.accent
                  ? 'text-primary-500'
                  : 'text-surface-700-300'}"
              >
                {cell.text}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/snippet}

{#snippet KeyHint(keys: string[])}
  <span class="inline-flex items-center gap-1">
    {#each keys as key}
      <kbd
        class="px-1.5 py-0.5 rounded bg-surface-200-800 border border-surface-300-700 text-xs font-mono text-surface-700-300"
        >{key}</kbd
      >
    {/each}
  </span>
{/snippet}
