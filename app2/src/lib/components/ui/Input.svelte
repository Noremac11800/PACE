<script lang="ts" module>
    export type InputStatus = "idle" | "invalid" | "warning" | "success";
</script>

<script lang="ts">
    import type { ClassValue, HTMLInputAttributes } from "svelte/elements";
    import Icon from "./Icon.svelte";
    import Label from "./Label.svelte";
    import type { IconName } from "./icons";

    type Props = {
        label: string;
        value?: string;
        /**
         * form: survey question — 48px box, BodyLarge, validation wraps the whole question.
         * general: search boxes and entries outside a form — 40px box, BodyMedium, message below.
         */
        variant?: "form" | "general";
        status?: InputStatus;
        message?: string;
        hint?: string;
        required?: boolean;
        readOnly?: boolean;
        iconStart?: IconName;
        clearable?: boolean;
        multiline?: boolean;
        /** Hide the label visually (e.g. a search box with a visible icon) */
        hideLabel?: boolean;
        class?: ClassValue;
    } & Omit<HTMLInputAttributes, "value" | "class" | "readonly" | "size">;

    let {
        label,
        value = $bindable(""),
        variant = "form",
        status = "idle",
        message,
        hint,
        required = false,
        readOnly = false,
        iconStart,
        clearable = true,
        multiline = false,
        hideLabel = false,
        maxlength,
        class: className,
        ...rest
    }: Props = $props();

    const uid = $props.id();
    let focused = $state(false);
    let field = $state<HTMLInputElement | HTMLTextAreaElement>();

    let form = $derived(variant === "form");
    let describedBy = $derived(
        [hint && `${uid}-hint`, message && `${uid}-message`]
            .filter(Boolean)
            .join(" ") || undefined,
    );
    let showClear = $derived(
        clearable && !readOnly && !multiline && value.length > 0,
    );

    const messageIcon: Record<InputStatus, { name: IconName; class: string }> =
        {
            idle: { name: "information", class: "text-text-tertiary" },
            invalid: {
                name: "exclamation-mark-triangle",
                class: "text-status-danger",
            },
            warning: {
                name: "exclamation-mark-triangle",
                class: "text-status-warning",
            },
            success: { name: "check-circle-f", class: "text-status-success" },
        };

    function clear() {
        value = "";
        field?.focus();
    }
</script>

{#snippet statusMessage()}
    {#if message}
        <p
            id="{uid}-message"
            class="flex items-center gap-1.5 text-caption text-text-primary"
        >
            <Icon
                name={messageIcon[status].name}
                size={16}
                class={messageIcon[status].class}
            />{message}
        </p>
    {/if}
{/snippet}

<div
    class={[
        "flex flex-col gap-2",
        form &&
            status === "invalid" &&
            "rounded border border-status-danger bg-required-background p-2",
        form &&
            status === "warning" &&
            "rounded border border-status-warning bg-warning-background p-2",
        className,
    ]}
>
    <Label
        {label}
        for="{uid}-field"
        {required}
        {hint}
        hintId="{uid}-hint"
        {readOnly}
        {variant}
        class={hideLabel ? "sr-only" : undefined}
    />
    {#if form}{@render statusMessage()}{/if}

    <div
        class={[
            "flex items-center gap-2 rounded-[2px] border px-3 transition-colors",
            form ? "text-body-large" : "text-body-medium",
            multiline ? "items-start py-2.5" : form ? "h-12" : "h-10",
            readOnly ? "bg-foreground-secondary" : "bg-foreground-primary",
            !form && status === "invalid"
                ? "border-status-danger"
                : !form && status === "success"
                  ? "border-status-success"
                  : "border-border-input",
            !readOnly &&
                "focus-within:border-brand focus-within:inset-ring focus-within:inset-ring-brand",
        ]}
    >
        {#if iconStart}<Icon
                name={iconStart}
                size={16}
                class="text-text-tertiary"
            />{/if}
        {#if multiline}
            <textarea
                bind:this={field}
                id="{uid}-field"
                bind:value
                rows="3"
                readonly={readOnly}
                {required}
                {maxlength}
                aria-invalid={status === "invalid" || undefined}
                aria-describedby={describedBy}
                onfocus={() => (focused = true)}
                onblur={() => (focused = false)}
                class="w-full min-w-0 flex-1 resize-y bg-transparent text-text-primary outline-none placeholder:text-text-tertiary"
                {...rest as Record<string, unknown>}></textarea>
        {:else}
            <input
                bind:this={field}
                id="{uid}-field"
                bind:value
                readonly={readOnly}
                {required}
                {maxlength}
                aria-invalid={status === "invalid" || undefined}
                aria-describedby={describedBy}
                onfocus={() => (focused = true)}
                onblur={() => (focused = false)}
                class={[
                    "w-full min-w-0 flex-1 bg-transparent text-text-primary outline-none placeholder:text-text-tertiary",
                    readOnly && "font-medium",
                ]}
                {...rest}
            />
        {/if}
        {#if showClear}
            <button
                type="button"
                aria-label={`Clear ${label}`}
                onclick={clear}
                class="-me-1 rounded-full p-1 text-text-tertiary hover:bg-transparent-hover hover:text-text-primary active:bg-transparent-press"
            >
                <Icon name="x-circle" size={16} />
            </button>
        {/if}
    </div>

    {#if maxlength && focused}
        <p
            class="-mt-1 text-end text-caption text-text-tertiary"
            aria-live="polite"
        >
            <span aria-hidden="true">{Number(maxlength) - value.length}</span
            ><span class="sr-only"
                >{Number(maxlength) - value.length} characters remaining</span
            >
        </p>
    {/if}
    {#if !form}{@render statusMessage()}{/if}
</div>
