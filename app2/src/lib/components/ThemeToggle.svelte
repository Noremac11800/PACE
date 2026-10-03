<script lang="ts">
    import { onMount } from "svelte";
    import type { ClassValue } from "svelte/elements";
    import Icon from "$lib/components/ui/Icon.svelte";
    import type { IconName } from "$lib/components/ui/icons";
    import { theme, type ThemePreference } from "$lib/theme.svelte";

    interface Props {
        /** Show text labels beside the icons; otherwise they're for screen readers only */
        labelled?: boolean;
        class?: ClassValue;
    }

    let { labelled = true, class: className }: Props = $props();

    const options: { value: ThemePreference; icon: IconName; label: string }[] =
        [
            { value: "system", icon: "desktop", label: "System" },
            { value: "light", icon: "brightness", label: "Light" },
            { value: "dark", icon: "moon", label: "Dark" },
        ];

    onMount(() => theme.restore());
</script>

<div
    role="radiogroup"
    aria-label="Appearance"
    class={[
        "flex shrink-0 rounded-md border border-border-input bg-foreground-secondary p-0.5",
        className,
    ]}
>
    {#each options as { value, icon, label } (value)}
        {@const selected = theme.preference === value}
        <button
            type="button"
            role="radio"
            aria-checked={selected}
            title={label}
            tabindex={selected ? 0 : -1}
            onkeydown={(event) => {
                const index = options.findIndex(
                    (option) => option.value === value,
                );
                const moves: Record<string, number> = {
                    ArrowRight: (index + 1) % 3,
                    ArrowDown: (index + 1) % 3,
                    ArrowLeft: (index + 2) % 3,
                    ArrowUp: (index + 2) % 3,
                    Home: 0,
                    End: 2,
                };
                if (!(event.key in moves)) return;
                event.preventDefault();
                theme.set(options[moves[event.key]].value);
                event.currentTarget.parentElement
                    ?.querySelectorAll("button")
                    [moves[event.key]].focus();
            }}
            onclick={() => theme.set(value)}
            class={[
                // Same height labelled or not, so the header row doesn't jump when it switches
                "flex items-center gap-1.5 rounded py-2 text-label-medium transition-colors",
                labelled ? "px-3" : "px-2.5",
                selected
                    ? "bg-foreground-primary text-text-primary shadow-sm"
                    : "text-text-secondary hover:bg-transparent-hover active:bg-transparent-press",
            ]}
        >
            <Icon name={icon} size={16} />
            <span class={[!labelled && "sr-only"]}>{label}</span>
        </button>
    {/each}
</div>
