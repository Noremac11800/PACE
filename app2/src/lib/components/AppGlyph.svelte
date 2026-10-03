<script lang="ts">
    import type { ClassValue } from "svelte/elements";
    import { theme } from "$lib/theme.svelte";

    let { class: className }: { class?: ClassValue } = $props();
</script>

<img
    src={theme.resolved === "dark" ? "/appglyph.svg" : "/appglyph-dark.svg"}
    alt=""
    aria-hidden="true"
    class={["shrink-0", className]}
/>
