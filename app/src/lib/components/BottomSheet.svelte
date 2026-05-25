<script lang="ts">
  import { XIcon } from "@lucide/svelte";
  import { Dialog, Portal } from "@skeletonlabs/skeleton-svelte";
  import type { Snippet } from "svelte";

  let {
    trigger,
    title,
    content,
  }: { trigger?: Snippet; title?: string; content?: Snippet } = $props();

  const animBackdrop =
    "transition transition-discrete opacity-0 starting:data-[state=open]:opacity-0 data-[state=open]:opacity-100";

  // slide up from bottom
  const animModal =
    "transition transition-discrete opacity-0 translate-y-full starting:data-[state=open]:opacity-0 starting:data-[state=open]:translate-y-full data-[state=open]:opacity-100 data-[state=open]:translate-y-0";
</script>

<Dialog>
  <Dialog.Trigger>
    {#snippet element(attributes)}
      <button {...attributes}>
        {@render trigger?.()}
      </button>
    {/snippet}
  </Dialog.Trigger>

  <Portal>
    <Dialog.Backdrop
      class="fixed inset-0 z-50 bg-surface-50-950/50 {animBackdrop}"
    />
    <Dialog.Positioner class="fixed inset-0 z-50 flex items-end justify-center">
      <Dialog.Content
        class="w-full max-w-md h-[50vh] flex flex-col gap-4 bg-surface-50-950 p-4 shadow-2xl rounded-none rounded-t-2xl {animModal}"
      >
        <header class="flex justify-between items-center">
          <Dialog.Title>
            {#snippet element(attributes)}
              <h6 class="h6" {...attributes}>
                {title}
              </h6>
            {/snippet}
          </Dialog.Title>
          <Dialog.CloseTrigger class="btn-icon hover:preset-tonal">
            <XIcon />
          </Dialog.CloseTrigger>
        </header>

        <main class="flex-1 overflow-y-auto">
          {@render content?.()}
        </main>
      </Dialog.Content>
    </Dialog.Positioner>
  </Portal>
</Dialog>
