<script lang="ts" module>
    export type ButtonKind = "product" | "neutral" | "danger";
    export type ButtonAppearance =
        "solid" | "outline-fill" | "outline" | "transparent";
    export type ButtonScale = "xs" | "s" | "m";
</script>

<script lang="ts">
    import type { Snippet } from "svelte";
    import type {
        ClassValue,
        HTMLAnchorAttributes,
        HTMLButtonAttributes,
    } from "svelte/elements";
    import Icon from "./Icon.svelte";
    import type { IconName } from "./icons";

    type Props = {
        kind?: ButtonKind;
        appearance?: ButtonAppearance;
        /** m = 44px (default), s = 32px (dialogs, toolbars), xs = 24px (inline status pills) */
        scale?: ButtonScale;
        iconStart?: IconName;
        iconEnd?: IconName;
        /** Render a circular icon-only button. `label` becomes its accessible name. */
        icon?: IconName;
        label?: string;
        /** Fill the width of the container (Button full width) */
        width?: "auto" | "full";
        /** Fully rounded ends, used for status pills */
        round?: boolean;
        href?: string;
        class?: ClassValue;
        children?: Snippet;
    } & Omit<HTMLButtonAttributes & HTMLAnchorAttributes, "class" | "children">;

    let {
        kind = "product",
        appearance = "solid",
        scale = "m",
        iconStart,
        iconEnd,
        icon,
        label,
        width = "auto",
        round = false,
        href,
        type = "button",
        class: className,
        children,
        ...rest
    }: Props = $props();

    // Each kind supplies idle/hover/press colours; appearances decide where they're applied.
    const kinds: Record<Exclude<ButtonKind, "neutral">, string> = {
        product:
            "[--c:var(--brand-color)] [--c-hover:var(--brand-hover-color)] [--c-press:var(--brand-press-color)]",
        danger: "[--c:var(--status-danger-color)] [--c-hover:var(--status-danger-hover-color)] [--c-press:var(--status-danger-press-color)]",
    };

    const appearances: Record<ButtonAppearance, string> = {
        solid: "bg-(--c) text-text-inverse hover:bg-(--c-hover) active:bg-(--c-press)",
        "outline-fill":
            "bg-foreground-primary text-(--c) inset-ring inset-ring-(--c) hover:inset-ring-2 hover:inset-ring-(--c-hover) hover:text-(--c-hover) active:inset-ring-3 active:inset-ring-(--c-press) active:text-(--c-press)",
        outline:
            "text-(--c) inset-ring inset-ring-(--c) hover:inset-ring-2 hover:inset-ring-(--c-hover) hover:text-(--c-hover) active:inset-ring-3 active:inset-ring-(--c-press) active:text-(--c-press)",
        transparent:
            "text-(--c) hover:bg-transparent-hover active:bg-transparent-press active:text-(--c-press)",
    };

    const neutral: Record<ButtonAppearance, string> = {
        solid: "bg-foreground-tertiary text-text-primary hover:bg-foreground-secondary active:bg-foreground-primary",
        "outline-fill":
            "bg-foreground-primary text-text-primary inset-ring inset-ring-border-primary hover:inset-ring-2 active:inset-ring-3",
        outline:
            "text-text-primary inset-ring inset-ring-border-primary hover:inset-ring-2 active:inset-ring-3",
        transparent:
            "text-text-primary hover:bg-transparent-hover active:bg-transparent-press",
    };

    const scales: Record<
        ButtonScale,
        { box: string; iconOnly: string; icon: number }
    > = {
        m: {
            box: "h-11 gap-2 px-4 text-label-large",
            iconOnly: "size-11",
            icon: 20,
        },
        s: {
            box: "h-8 gap-1.5 px-3 text-label-medium",
            iconOnly: "size-8",
            icon: 16,
        },
        xs: {
            box: "h-6 gap-1 px-2.5 text-label-small",
            iconOnly: "size-6",
            icon: 14,
        },
    };

    let s = $derived(scales[scale]);
    let classes = $derived([
        "inline-flex shrink-0 items-center justify-center whitespace-nowrap no-underline transition-[color,background-color,box-shadow] select-none hover:no-underline",
        "aria-disabled:pointer-events-none aria-disabled:opacity-50 disabled:pointer-events-none disabled:opacity-50",
        kind === "neutral"
            ? neutral[appearance]
            : [kinds[kind], appearances[appearance]],
        icon
            ? [s.iconOnly, "rounded-full"]
            : [s.box, round ? "rounded-full" : "rounded"],
        width === "full" && !icon && "w-full",
        className,
    ]);
</script>

{#snippet content()}
    {#if icon}
        <Icon name={icon} size={s.icon} />
    {:else}
        {#if iconStart}<Icon name={iconStart} size={s.icon} />{/if}
        {#if children}{@render children()}{:else}{label}{/if}
        {#if iconEnd}<Icon name={iconEnd} size={s.icon} />{/if}
    {/if}
{/snippet}

{#if href}
    <a {href} class={classes} aria-label={icon ? label : undefined} {...rest}
        >{@render content()}</a
    >
{:else}
    <button
        {type}
        class={classes}
        aria-label={icon ? label : undefined}
        {...rest}>{@render content()}</button
    >
{/if}
