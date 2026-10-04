<script lang="ts">
    import type { Snippet } from "svelte";
    let {
        eyebrow = "Workspace",
        title,
        description,
        actions,
        compact = false,
    }: {
        eyebrow?: string;
        title: string;
        description: string;
        actions?: Snippet;
        compact?: boolean;
    } = $props();
</script>

<div
    class={[
        compact ? "mb-4 items-center" : "mb-7 items-end",
        "flex flex-wrap justify-between gap-4",
    ]}
>
    <div class="min-w-0">
        {#if !compact}<p class="eyebrow mb-2">{eyebrow}</p>{/if}
        <h1 class={compact ? "text-title-large" : "text-headline-large"}>
            {title}
        </h1>
        <p
            class={[
                compact
                    ? "mt-1 max-w-md text-caption"
                    : "mt-2 max-w-3xl text-body-small",
                "leading-relaxed text-text-secondary",
            ]}
        >
            {description}
        </p>
    </div>
    {#if actions}<div class="flex items-center gap-2">
            {@render actions()}
        </div>{/if}
</div>
