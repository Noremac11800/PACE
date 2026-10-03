<script lang="ts" module>
    export type CardLayout = "list" | "grid" | "table";
</script>

<script lang="ts">
    import type { Snippet } from "svelte";
    import type { ClassValue } from "svelte/elements";
    import Button from "./Button.svelte";
    import Thumbnail from "./Thumbnail.svelte";

    interface Props {
        heading: string;
        description?: string;
        /** Secondary line such as a modified date */
        meta?: string;
        layout?: CardLayout;
        /** s = compact, l = shows the description and a larger thumbnail */
        size?: "s" | "l";
        thumbnail?: string | false;
        loading?: boolean;
        /** Selection underline */
        selected?: boolean;
        href?: string;
        onclick?: () => void;
        /** Adds a "More options" button; receives nothing and should open a menu */
        onmore?: () => void;
        /** Contextual control: footer start in list, next to the title in grid, row start in table */
        contextual?: Snippet;
        /** Status or action on the footer's trailing edge */
        status?: Snippet;
        class?: ClassValue;
    }

    let {
        heading,
        description,
        meta,
        layout = "list",
        size = "s",
        thumbnail,
        loading = false,
        selected = false,
        href,
        onclick,
        onmore,
        contextual,
        status,
        class: className,
    }: Props = $props();

    let interactive = $derived(Boolean(href || onclick));
    let showFooter = $derived(
        layout === "list" && Boolean(contextual || status || onmore),
    );
    let hasThumb = $derived(thumbnail !== false && layout !== "table");
</script>

{#snippet title(cls: string)}
    {#if href}
        <a
            {href}
            class="{cls} text-text-primary no-underline after:absolute after:inset-0 hover:no-underline"
            >{heading}</a
        >
    {:else if onclick}
        <button
            type="button"
            {onclick}
            class="{cls} text-start after:absolute after:inset-0"
            >{heading}</button
        >
    {:else}
        <span class={cls}>{heading}</span>
    {/if}
{/snippet}

{#snippet more()}
    {#if onmore}
        <Button
            icon="ellipsis"
            label={`More options for ${heading}`}
            kind="neutral"
            appearance="transparent"
            scale="xs"
            class="relative z-10"
            onclick={onmore}
        />
    {/if}
{/snippet}

<article
    class={[
        "relative flex overflow-hidden rounded border border-border-tertiary bg-foreground-primary text-text-primary transition-colors",
        layout === "grid"
            ? "flex-col"
            : layout === "list"
              ? "flex-col"
              : "items-center gap-3 px-3",
        layout === "table" && (size === "s" ? "min-h-11" : "min-h-12"),
        interactive &&
            "hover:bg-foreground-secondary has-[:is(a,button):active]:bg-foreground-tertiary",
        selected && "shadow-[inset_0_-3px_0_var(--brand-color)]",
        className,
    ]}
>
    {#if layout === "table"}
        {#if contextual}<div class="relative z-10 flex">
                {@render contextual()}
            </div>{/if}
        {@render title("min-w-0 flex-1 truncate text-body-medium")}
        {#if size === "l" && meta}<span class="text-caption text-text-tertiary"
                >{meta}</span
            >{/if}
        {#if status}<div class="relative z-10">{@render status()}</div>{/if}
        {@render more()}
    {:else if layout === "grid"}
        {#if hasThumb}
            <Thumbnail
                src={thumbnail || undefined}
                {loading}
                class="aspect-[16/10] w-full rounded-none border-0 border-b"
            />
        {/if}
        <div class="flex flex-1 flex-col gap-2 p-3">
            <div class="flex items-start gap-2">
                {@render title("min-w-0 flex-1 text-title-small line-clamp-2")}
                {#if contextual}<div class="relative z-10 flex">
                        {@render contextual()}
                    </div>{/if}
                {#if !meta && !status}{@render more()}{/if}
            </div>
            {#if meta || status}
                <div class="mt-auto flex items-center justify-between gap-2">
                    {#if meta}<span class="text-caption text-text-tertiary"
                            >{meta}</span
                        >{/if}
                    {#if status}<div class="relative z-10 ms-auto">
                            {@render status()}
                        </div>{/if}
                    {@render more()}
                </div>
            {/if}
        </div>
    {:else}
        <div class="flex gap-3 p-2">
            {#if hasThumb}
                <Thumbnail
                    src={thumbnail || undefined}
                    {loading}
                    class={size === "s" ? "h-13 w-20" : "h-22 w-33"}
                />
            {/if}
            <div class="flex min-w-0 flex-1 flex-col gap-1 py-0.5">
                {@render title("text-title-small line-clamp-2")}
                {#if size === "l" && description}
                    <p class="line-clamp-2 text-body-small text-text-secondary">
                        {description}
                    </p>
                {/if}
                {#if meta}<span class="text-caption text-text-tertiary"
                        >{meta}</span
                    >{/if}
            </div>
        </div>
        {#if showFooter}
            <footer
                class="flex min-h-9 items-center gap-2 border-t border-border-tertiary px-2 py-1"
            >
                {#if contextual}<div
                        class="relative z-10 flex items-center gap-2"
                    >
                        {@render contextual()}
                    </div>{/if}
                <div class="relative z-10 ms-auto flex items-center gap-1">
                    {#if status}{@render status()}{/if}
                    {@render more()}
                </div>
            </footer>
        {/if}
    {/if}
</article>
