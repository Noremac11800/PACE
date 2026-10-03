<script lang="ts">
    import type { Snippet } from "svelte";
    let {
        eyebrow = "Workspace",
        title,
        description,
        actions,
    }: {
        eyebrow?: string;
        title: string;
        description: string;
        actions?: Snippet;
    } = $props();
</script>

<div class="mb-7 flex flex-wrap items-end justify-between gap-4">
    <div class="min-w-0">
        <p class="eyebrow mb-2">{eyebrow}</p>
        <h1 class="text-headline-large">{title}</h1>
        <p
            class="mt-2 max-w-3xl text-body-small leading-relaxed text-text-secondary"
        >
            {description}
        </p>
    </div>
    {#if actions}<div class="flex items-center gap-2">
            {@render actions()}
        </div>{/if}
</div>
