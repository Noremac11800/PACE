<script lang="ts">
  import { getContext, onMount } from "svelte";
  import type { LayoutProps } from "../+layout.svelte";
  import { createToaster } from "@skeletonlabs/skeleton-svelte";
  import { Info } from "@lucide/svelte";

  const data = getContext<LayoutProps>("data");
  const toaster = getContext<ReturnType<typeof createToaster>>("toaster");

  onMount(() => {
    data.title = "Toast";
  });
</script>

{#snippet toastIcon()}
  <Info />
{/snippet}

<main class="flex flex-col items-center gap-4 p-8">
  <button
    class="btn preset-filled-primary-500"
    onclick={() => toaster?.info({ title: "Toast title" })}
  >
    Toast w/ title only
  </button>

  <button
    class="btn preset-filled-primary-500"
    onclick={() =>
      toaster?.info({
        description:
          "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis deserunt voluptatum doloremque.",
      })}
  >
    Toast w/ description only
  </button>

  <button
    class="btn preset-filled-primary-500"
    onclick={() =>
      toaster?.info({
        title: "Toast title",
        description:
          "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis deserunt voluptatum doloremque.",
      })}
  >
    Toast w/ title and description
  </button>

  <button
    class="btn preset-filled-primary-500"
    onclick={() =>
      toaster?.info({
        title: "Toast message",
        description:
          "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Tempora ad quis deserunt voluptatum doloremque.",
        meta: { icon: toastIcon },
      })}
  >
    Toast w/ icon
  </button>
</main>
