<script lang="ts">
    import type { ClassValue } from "svelte/elements";
    import Spinner from "./Spinner.svelte";

    interface Props {
        src?: string;
        alt?: string;
        /** Covers the image with a scrim and spinner */
        loading?: boolean;
        class?: ClassValue;
    }

    let { src, alt = "", loading = false, class: className }: Props = $props();
</script>

<div
    class={[
        "bg-checker relative shrink-0 overflow-hidden rounded border border-border-tertiary",
        className,
    ]}
>
    {#if src}<img {src} {alt} class="size-full object-cover" />{/if}
    {#if loading}
        <div
            class="absolute inset-0 grid place-items-center bg-transparent-scrim"
        >
            <Spinner
                inverse
                scale="l"
                class="max-h-[70%] max-w-[70%] [&_svg]:size-full"
            />
        </div>
    {/if}
</div>
