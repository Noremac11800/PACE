<script lang="ts">
    import type { Snippet } from "svelte";
    import Icon from "./ui/Icon.svelte";
    import type { IconName } from "./ui/icons";
    let {
        icon = "folder-open",
        title,
        description,
        actions,
    }: {
        icon?: IconName;
        title: string;
        description: string;
        actions?: Snippet;
    } = $props();
</script>

<div class="panel flex flex-col items-center px-8 py-14 text-center">
    <div
        class="mb-5 grid size-14 place-items-center rounded-full bg-foreground-current text-brand"
    >
        <Icon name={icon} size={24} />
    </div>
    <h2 class="text-title-medium">{title}</h2>
    <p
        class="mt-2 max-w-lg text-body-small leading-relaxed text-text-secondary"
    >
        {description}
    </p>
    {#if actions}<div class="mt-6 flex gap-2">{@render actions()}</div>{/if}
</div>
