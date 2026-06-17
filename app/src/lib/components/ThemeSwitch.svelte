<script lang="ts">
  import { Switch } from "@skeletonlabs/skeleton-svelte";
  import { theme } from "$lib/theme.svelte";
  import { settings } from "$lib/settings.svelte";
  import { Sun, Moon } from "@lucide/svelte";

  let { class: classname }: { class?: string } = $props();

  let checked = $derived(theme.current === "dark");

  const onCheckedChange = (event: { checked: boolean }) => {
    const mode = event.checked ? "dark" : "light";
    theme.set(mode);
    settings.general.theme = mode;
  };
</script>

<svelte:head>
  <script>
    document.documentElement.setAttribute(
      "data-mode",
      localStorage.getItem("mode") || "dark",
    );
  </script>
</svelte:head>

<div class="flex items-center gap-2 {classname}">
  {#if theme.current === "light"}
    <Sun class="w-5 h-5" />
  {:else}
    <Moon class="w-5 h-5" />
  {/if}
  <Switch {checked} {onCheckedChange}>
    <Switch.Control>
      <Switch.Thumb />
    </Switch.Control>
    <Switch.HiddenInput />
  </Switch>
</div>
