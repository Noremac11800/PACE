<script lang="ts">
    import type { ClassValue } from "svelte/elements";

    interface Props {
        checked?: boolean;
        label?: string;
        /** Hide the label visually but keep it as the accessible name */
        hideLabel?: boolean;
        disabled?: boolean;
        onchange?: (checked: boolean) => void;
        class?: ClassValue;
    }

    let {
        checked = $bindable(false),
        label,
        hideLabel = false,
        disabled = false,
        onchange,
        class: className,
    }: Props = $props();

    function toggle() {
        checked = !checked;
        onchange?.(checked);
    }
</script>

<button
    type="button"
    role="switch"
    aria-checked={checked}
    aria-label={hideLabel ? label : undefined}
    {disabled}
    onclick={toggle}
    class={[
        "group inline-flex items-center gap-3 text-body-medium text-text-primary disabled:cursor-not-allowed disabled:opacity-50",
        className,
    ]}
>
    <span
        class={[
            "relative h-6 w-12 shrink-0 rounded-full border transition-colors",
            checked
                ? "border-brand-hover bg-brand group-hover:bg-brand-hover group-active:bg-brand-press"
                : "border-border-input bg-border-input group-hover:bg-text-tertiary",
        ]}
    >
        <span
            class={[
                "absolute top-1/2 size-5.5 -translate-y-1/2 rounded-full border bg-border-white shadow-sm transition-[inset-inline-start,border-color]",
                checked
                    ? "start-[calc(100%-1.4375rem)] border-brand"
                    : "start-px border-border-input",
            ]}
        ></span>
    </span>
    {#if label && !hideLabel}<span>{label}</span>{/if}
</button>
