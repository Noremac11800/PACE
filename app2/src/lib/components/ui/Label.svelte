<script lang="ts">
    import type { ClassValue } from "svelte/elements";
    import Icon from "./Icon.svelte";

    interface Props {
        label: string;
        /** id of the control this labels */
        for?: string;
        /** id for the element, so groups can reference it with aria-labelledby */
        id?: string;
        required?: boolean;
        /** Description or hint, shown with a guidance icon */
        hint?: string;
        hintId?: string;
        readOnly?: boolean;
        /** form = survey question (BodyLarge), general = compact (BodySmall) */
        variant?: "form" | "general";
        class?: ClassValue;
    }

    let {
        label,
        for: htmlFor,
        id,
        required = false,
        hint,
        hintId,
        readOnly = false,
        variant = "form",
        class: className,
    }: Props = $props();
</script>

<div class={["flex flex-col items-start gap-1", className]}>
    <svelte:element
        this={htmlFor ? "label" : "span"}
        for={htmlFor}
        {id}
        class={variant === "form"
            ? "text-body-large text-text-primary"
            : "text-body-small text-text-secondary"}
    >
        {label}{#if required}<span
                class="ms-0.5 text-status-danger"
                aria-hidden="true">*</span
            ><span class="sr-only"> required</span>{/if}
    </svelte:element>
    {#if hint}
        <p
            id={hintId}
            class="flex items-center gap-1.5 text-body-small text-text-secondary"
        >
            <Icon name="information" size={16} class="text-brand" />{hint}
        </p>
    {/if}
    {#if readOnly}
        <span
            class="inline-flex items-center gap-1 rounded-full bg-foreground-tertiary px-2 py-0.5 text-caption text-text-secondary"
        >
            <Icon name="lock" size={12} />Read only
        </span>
    {/if}
</div>
