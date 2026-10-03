<script lang="ts" module>
    export type ChipAppearance = "light" | "none" | "dark";
    export type ChipTone = "blue" | "teal" | "red" | "yellow" | "green";
</script>

<script lang="ts">
    import type { ClassValue } from "svelte/elements";
    import Icon from "./Icon.svelte";
    import type { IconName } from "./icons";

    interface Props {
        label: string;
        /** Background: light (tinted), none (outlined) or dark (brand) */
        appearance?: ChipAppearance;
        /** Swap the light tint for an avatar hue, e.g. to tag content types */
        tone?: ChipTone;
        scale?: "s" | "m";
        iconStart?: IconName;
        iconEnd?: IconName;
        count?: number;
        /** Filter chip: makes the chip a toggle button */
        selected?: boolean;
        onclick?: () => void;
        /** Input chip: shows a remove button */
        onremove?: () => void;
        class?: ClassValue;
    }

    let {
        label,
        appearance = "light",
        tone,
        scale = "m",
        iconStart,
        iconEnd,
        count,
        selected = $bindable(),
        onclick,
        onremove,
        class: className,
    }: Props = $props();

    const tones: Record<ChipTone, string> = {
        blue: "bg-avatar-blue",
        teal: "bg-avatar-teal",
        red: "bg-avatar-red",
        yellow: "bg-avatar-yellow",
        green: "bg-avatar-green",
    };

    // A filter chip is outlined when idle and tinted with a check when selected.
    let isFilter = $derived(selected !== undefined);
    let look = $derived(isFilter ? (selected ? "light" : "none") : appearance);
    let startIcon = $derived(isFilter && selected ? "check" : iconStart);
    let iconSize = $derived(scale === "m" ? 16 : 12);

    let classes = $derived([
        "inline-flex shrink-0 items-center rounded-full whitespace-nowrap transition-colors",
        scale === "m"
            ? "h-8 gap-1.5 px-3 text-label-medium"
            : "h-6 gap-1 px-2 text-label-small",
        onremove && (scale === "m" ? "pe-1.5" : "pe-1"),
        look === "light" && [
            tone ? tones[tone] : "bg-foreground-current",
            "text-text-primary",
        ],
        look === "none" &&
            "text-text-primary inset-ring inset-ring-border-primary",
        look === "dark" && "bg-brand text-text-inverse",
        (onclick || isFilter) &&
            "cursor-pointer hover:brightness-95 active:brightness-90",
        className,
    ]);

    function handleClick() {
        if (isFilter) selected = !selected;
        onclick?.();
    }
</script>

{#snippet body()}
    {#if startIcon}<Icon name={startIcon} size={iconSize} />{/if}
    <span>{label}</span>
    {#if count !== undefined}<span class="opacity-75">{count}</span>{/if}
    {#if iconEnd}<Icon name={iconEnd} size={iconSize} />{/if}
{/snippet}

{#if onclick || isFilter}
    <button
        type="button"
        class={classes}
        aria-pressed={isFilter ? selected : undefined}
        onclick={handleClick}
    >
        {@render body()}
    </button>
{:else}
    <span class={classes}>
        {@render body()}
        {#if onremove}
            <button
                type="button"
                aria-label={`Remove ${label}`}
                onclick={onremove}
                class="grid place-items-center rounded-full p-0.5 hover:bg-transparent-hover active:bg-transparent-press"
            >
                <Icon name="x" size={iconSize} />
            </button>
        {/if}
    </span>
{/if}
