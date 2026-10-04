<script lang="ts">
    import type { Snippet } from "svelte";
    import type { ClassValue } from "svelte/elements";
    import Icon from "./Icon.svelte";
    import type { IconName } from "./icons";

    interface Props {
        open?: boolean;
        heading?: string;
        description?: string;
        /** Accessible name when there's no visible heading */
        label?: string;
        icon?: IconName;
        tone?: "default" | "danger";
        /** vertical stacks full-width buttons (use for 2–3 long labels) */
        actionsLayout?: "horizontal" | "vertical";
        /** Long content scrolls between a fixed header and footer */
        scrollable?: boolean;
        /** default suits short messages; wide gives detail views and code room */
        width?: "default" | "wide";
        dismissible?: boolean;
        actions?: Snippet;
        children?: Snippet;
        onclose?: () => void;
        class?: ClassValue;
    }

    let {
        open = $bindable(false),
        heading,
        description,
        label,
        icon,
        tone = "default",
        actionsLayout = "horizontal",
        scrollable = false,
        width = "default",
        dismissible = true,
        actions,
        children,
        onclose,
        class: className,
    }: Props = $props();

    const uid = $props.id();
    let dialog = $state<HTMLDialogElement>();

    $effect(() => {
        if (!dialog) return;
        if (open && !dialog.open) dialog.showModal();
        if (!open && dialog.open) dialog.close();
    });
</script>

<dialog
    bind:this={dialog}
    aria-labelledby={heading ? `${uid}-heading` : undefined}
    aria-label={heading ? undefined : label}
    aria-describedby={description ? `${uid}-description` : undefined}
    onclose={() => ((open = false), onclose?.())}
    onclick={(e) => dismissible && e.target === dialog && (open = false)}
    oncancel={(event) => {
        if (!dismissible) event.preventDefault();
    }}
    class={[
        "m-auto flex-col overflow-hidden rounded-lg bg-foreground-primary p-0 text-text-primary shadow-xl open:flex",
        width === "wide"
            ? "w-[min(100%-2rem,36rem)]"
            : "w-[min(100%-2rem,22rem)]",
        // Grows to fit its content, up to the viewport; beyond that the body scrolls
        "max-h-[calc(100dvh_-_2rem_-_var(--safe-top)_-_var(--safe-bottom))]",
        "backdrop:bg-transparent-scrim",
        // Animates in only. Closing is instant: holding display through an exit
        // transition needs `overlay` to keep the dialog in the top layer, which WebKit
        // lacks, so the closing dialog would flash at its in-page position.
        "transition-[opacity,scale] duration-150 starting:open:scale-95 starting:open:opacity-0",
        className,
    ]}
>
    <header
        class={[
            "flex shrink-0 flex-col gap-2 px-5 pt-5",
            icon && "items-center text-center",
            !heading && !description && "pt-0",
        ]}
    >
        {#if icon}
            <Icon
                name={icon}
                size={24}
                class={tone === "danger" ? "text-status-danger" : "text-brand"}
            />
        {/if}
        {#if heading}<h2 id="{uid}-heading" class="text-title-large">
                {heading}
            </h2>{/if}
        {#if description}
            <p
                id="{uid}-description"
                class="self-stretch text-start text-body-small text-text-secondary"
            >
                {description}
            </p>
        {/if}
    </header>

    {#if children}
        <!--
            Scrollable bodies start at their content's height and only shrink, then
            scroll, once the dialog reaches its max height. Not flex-1: a 0% basis in
            an auto-height dialog collapses the body to nothing in WebKit (Tauri on
            Linux and macOS), where Chromium falls back to the content height.
        -->
        <div
            class={[
                "px-5 pt-3",
                scrollable &&
                    "min-h-0 overflow-y-auto pb-4 text-body-small text-text-secondary",
            ]}
        >
            {@render children()}
        </div>
    {/if}

    {#if actions}
        <footer
            class={[
                "flex shrink-0 gap-2 px-5 pt-4 pb-5",
                actionsLayout === "vertical" ? "flex-col" : "justify-end",
                scrollable && "border-t border-border-tertiary pt-4",
            ]}
        >
            {@render actions()}
        </footer>
    {/if}
</dialog>
