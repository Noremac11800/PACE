<script lang="ts">
    import type { ClassValue } from "svelte/elements";
    import Icon from "./Icon.svelte";

    interface Props {
        /** 16, 32 or 60px */
        scale?: "s" | "m" | "l";
        /** White spinner for use over imagery and scrims */
        inverse?: boolean;
        label?: string;
        class?: ClassValue;
    }

    let {
        scale = "m",
        inverse = false,
        label,
        class: className,
    }: Props = $props();

    const sizes = { s: 16, m: 32, l: 60 };
</script>

<span role="status" class={["inline-grid", className]}>
    <Icon
        name="spinner"
        size={sizes[scale]}
        class={[
            "animate-spin motion-reduce:[animation-duration:3s]",
            inverse ? "text-border-white" : "text-brand",
        ]}
    />
    <span class="sr-only">{label ?? "Loading"}</span>
</span>
