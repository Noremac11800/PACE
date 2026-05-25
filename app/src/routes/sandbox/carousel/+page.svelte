<script lang="ts">
  import { getContext, onMount } from "svelte";
  import type { LayoutProps } from "../+layout.svelte";

  const data = getContext<LayoutProps>("data");

  onMount(() => {
    data.title = "Carousel";
  });
</script>

<main class="flex flex-col gap-4 p-8">
  <p>Carousel demo coming soon.</p>
</main>
