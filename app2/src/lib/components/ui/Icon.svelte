<script lang="ts">
    import type { ClassValue } from "svelte/elements";
    import {
        drawingFor,
        mirroredInRtl,
        symbolId,
        type IconName,
    } from "./icons";

    interface Props {
        /** Any Calcite UI icon name, e.g. "chevron-left" or "bell-f" */
        name: IconName;
        /** Pixel size of the square icon */
        size?: number;
        /** Accessible name. Omit for decorative icons (hidden from assistive tech). */
        label?: string;
        class?: ClassValue;
    }

    let { name, size = 20, label, class: className }: Props = $props();

    let drawing = $derived(drawingFor(size));
</script>

<svg
    viewBox="0 0 {drawing} {drawing}"
    width={size}
    height={size}
    fill="currentColor"
    class={[
        "shrink-0",
        mirroredInRtl.has(name) && "rtl:-scale-x-100",
        className,
    ]}
    role={label ? "img" : undefined}
    aria-label={label}
    aria-hidden={label ? undefined : true}
>
    <use href="#{symbolId(name, drawing)}" />
</svg>
