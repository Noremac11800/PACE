<script lang="ts">
  import { getContext, onMount } from "svelte";
  import type { LayoutProps } from "../+layout.svelte";
  import { XIcon } from "@lucide/svelte";
  import { Dialog, Portal } from "@skeletonlabs/skeleton-svelte";
  import BottomSheet from "$lib/components/BottomSheet.svelte";

  const animBackdrop =
    "transition transition-discrete opacity-0 starting:data-[state=open]:opacity-0 data-[state=open]:opacity-100";

  // slide up from bottom
  const animModal =
    "transition transition-discrete opacity-0 translate-y-full starting:data-[state=open]:opacity-0 starting:data-[state=open]:translate-y-full data-[state=open]:opacity-100 data-[state=open]:translate-y-0";

  const data = getContext<LayoutProps>("data");

  onMount(() => {
    data.title = "Bottom Sheet";
  });
</script>

{#snippet buttonTrigger()}
  <button class="btn preset-filled-primary-500">Open bottom sheet</button>
{/snippet}

{#snippet bottomSheetContent()}
  <p>Bottom sheet content.</p>
{/snippet}

<main class="flex flex-col gap-4 p-8">
  <BottomSheet
    trigger={buttonTrigger}
    title="Bottom Sheet"
    content={bottomSheetContent}
  />
</main>
