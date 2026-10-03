<script lang="ts">
    import type { Snippet } from "svelte";
    import type { ClassValue, HTMLInputAttributes } from "svelte/elements";
    import Icon from "./Icon.svelte";

    type Props = {
        checked?: boolean;
        /** Partially selected, e.g. a parent with some children selected */
        indeterminate?: boolean;
        label?: string;
        /** Survey choice style: the whole option is a box that fills with brand when selected */
        boxed?: boolean;
        /** Shows the choice but can't change it; a selected box is outlined, not filled */
        readOnly?: boolean;
        class?: ClassValue;
        children?: Snippet;
    } & Omit<HTMLInputAttributes, "type" | "checked" | "class" | "children">;

    let {
        checked = $bindable(false),
        indeterminate = $bindable(false),
        label,
        boxed = false,
        readOnly = false,
        disabled,
        class: className,
        children,
        ...rest
    }: Props = $props();

    let on = $derived(checked || indeterminate);
</script>

<label
    class={[
        "inline-flex items-center gap-2 text-body-medium",
        disabled
            ? "cursor-not-allowed opacity-50"
            : readOnly
              ? "cursor-default"
              : "cursor-pointer",
        boxed &&
            readOnly && [
                "rounded border bg-background px-3 py-2.5",
                on ? "border-brand font-medium" : "border-border-input",
            ],
        boxed &&
            !readOnly && [
                "rounded border px-3 py-2.5 transition-colors",
                on
                    ? "border-brand bg-brand text-text-inverse hover:border-brand-hover hover:bg-brand-hover active:bg-brand-press"
                    : "border-border-input bg-foreground-tertiary hover:bg-foreground-secondary",
            ],
        className,
    ]}
>
    <span class="relative grid size-4 shrink-0 place-items-center">
        <input
            type="checkbox"
            bind:checked
            bind:indeterminate
            {disabled}
            aria-readonly={readOnly || undefined}
            onclick={(e) => readOnly && e.preventDefault()}
            class={[
                "size-4 cursor-[inherit] appearance-none rounded-[2px] border-[1.5px] transition-colors",
                readOnly && on
                    ? "border-brand bg-foreground-primary"
                    : boxed && on
                      ? "border-text-inverse bg-text-inverse"
                      : on
                        ? "border-brand bg-brand"
                        : "border-border-input bg-foreground-primary",
            ]}
            {...rest}
        />
        {#if on}
            <Icon
                name={indeterminate ? "minus" : "check"}
                size={16}
                class={[
                    "pointer-events-none absolute",
                    boxed || readOnly ? "text-brand" : "text-text-inverse",
                ]}
            />
        {/if}
    </span>
    {#if children}{@render children()}{:else if label}{label}{/if}
</label>
