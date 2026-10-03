<script lang="ts" module>
    import type { IconName } from "./icons";

    export type TabColor = "brand" | "inbox" | "draft" | "outbox" | "sent";

    export interface Tab {
        value: string;
        label: string;
        icon?: IconName;
        /** Count shown in a badge on the icon */
        badge?: number;
        /** Accent for icon tabs (Survey123 folders) */
        color?: TabColor;
    }
</script>

<script lang="ts">
    import type { Snippet } from "svelte";
    import type { ClassValue } from "svelte/elements";
    import Icon from "./Icon.svelte";

    interface Props {
        tabs: Tab[];
        value?: string;
        label: string;
        /** default = equal-width with underline, filled = solid brand blocks, scrollable = hug content and scroll */
        appearance?: "default" | "filled" | "scrollable";
        /** Content for the active tab */
        panel?: Snippet<[string]>;
        class?: ClassValue;
    }

    let {
        tabs,
        value = $bindable(tabs[0]?.value),
        label,
        appearance = "default",
        panel,
        class: className,
    }: Props = $props();

    const uid = $props.id();

    const accents: Record<
        TabColor,
        { text: string; bar: string; badge: string }
    > = {
        brand: { text: "text-brand", bar: "bg-brand", badge: "bg-brand" },
        inbox: {
            text: "text-inbox-blue",
            bar: "bg-inbox-blue",
            badge: "bg-inbox-blue",
        },
        draft: {
            text: "text-draft-orange",
            bar: "bg-draft-orange",
            badge: "bg-draft-orange",
        },
        outbox: {
            text: "text-outbox-teal",
            bar: "bg-outbox-teal",
            badge: "bg-outbox-teal",
        },
        sent: {
            text: "text-sent-grey",
            bar: "bg-sent-grey",
            badge: "bg-sent-grey",
        },
    };

    function onkeydown(event: KeyboardEvent) {
        const index = tabs.findIndex((t) => t.value === value);
        // Arrows follow what's on screen, so in right-to-left layouts left is next
        const rtl =
            getComputedStyle(event.currentTarget as Element).direction ===
            "rtl";
        const next = (index + 1) % tabs.length;
        const previous = (index - 1 + tabs.length) % tabs.length;
        const moves: Record<string, number> = {
            ArrowRight: rtl ? previous : next,
            ArrowLeft: rtl ? next : previous,
            Home: 0,
            End: tabs.length - 1,
        };
        if (!(event.key in moves)) return;
        event.preventDefault();
        value = tabs[moves[event.key]].value;
        document.getElementById(`${uid}-tab-${value}`)?.focus();
    }
</script>

<div class={["flex flex-col", className]}>
    <div
        role="tablist"
        aria-label={label}
        tabindex="-1"
        {onkeydown}
        class={[
            "flex",
            appearance !== "filled" && "border-b-2 border-border-tertiary",
            appearance === "scrollable" &&
                "overflow-x-auto [scrollbar-width:thin]",
        ]}
    >
        {#each tabs as tab (tab.value)}
            {@const active = tab.value === value}
            {@const accent = accents[tab.color ?? "brand"]}
            <button
                type="button"
                role="tab"
                id="{uid}-tab-{tab.value}"
                aria-selected={active}
                aria-controls={panel ? `${uid}-panel` : undefined}
                tabindex={active ? 0 : -1}
                onclick={() => (value = tab.value)}
                class={[
                    "relative flex items-center justify-center transition-colors outline-offset-[-2px]",
                    appearance === "scrollable"
                        ? "flex-none px-4"
                        : "min-w-0 flex-1 px-3",
                    tab.icon
                        ? "h-14 flex-col gap-0.5 text-label-small"
                        : "h-12 text-label-large",
                    appearance === "filled"
                        ? [
                              // Active: white in both themes. Inactive: white in light,
                              // black in dark, where the brand green is too bright for white.
                              active
                                  ? "bg-brand-press text-text-white"
                                  : "bg-brand text-text-inverse hover:bg-brand-hover active:bg-brand-press",
                          ]
                        : [
                              "active:bg-foreground-tertiary",
                              active
                                  ? "text-text-primary"
                                  : "text-text-tertiary hover:text-text-secondary",
                              tab.icon && !active && "opacity-60",
                          ],
                ]}
            >
                {#if tab.icon}
                    <span class="relative">
                        <Icon
                            name={tab.icon}
                            class={tab.color ? accent.text : ""}
                        />
                        {#if tab.badge !== undefined}
                            <span
                                class="absolute -end-2 -top-1.5 grid h-4 min-w-4 place-items-center rounded-full px-1 text-[0.625rem] leading-none font-medium text-text-inverse {accent.badge}"
                            >
                                {tab.badge}
                            </span>
                        {/if}
                    </span>
                {/if}
                <span class="max-w-full truncate">{tab.label}</span>
                {#if active && appearance !== "filled"}
                    <span
                        class="absolute inset-x-0 -bottom-0.5 h-[3px] {accent.bar}"
                    ></span>
                {/if}
            </button>
        {/each}
    </div>
    {#if panel && value}
        <div
            id="{uid}-panel"
            role="tabpanel"
            aria-labelledby="{uid}-tab-{value}"
            tabindex="0"
            class="pt-4"
        >
            {@render panel(value)}
        </div>
    {/if}
</div>
