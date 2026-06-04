<script lang="ts">
  import { Copy, Check } from "@lucide/svelte";

  interface Props {
    text: string;
    size?: number;
    class?: string;
  }

  let { text, size = 16, class: className = "" }: Props = $props();

  let copied = $state(false);
  let copyTimeout: ReturnType<typeof setTimeout> | null = null;

  async function copyToClipboard(): Promise<void> {
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
      if (copyTimeout) clearTimeout(copyTimeout);
      copyTimeout = setTimeout(() => (copied = false), 2000);
    } catch (e) {
      console.error("Failed to copy to clipboard:", e);
    }
  }
</script>

<button
  class="btn preset-tonal p-2 {className}"
  onclick={copyToClipboard}
  title={copied ? "Copied!" : "Copy to clipboard"}
>
  {#if copied}
    <Check {size} class="text-success-500" />
  {:else}
    <Copy {size} />
  {/if}
</button>
