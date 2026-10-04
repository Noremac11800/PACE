<script lang="ts">
    import { tick } from "svelte";
    import { app } from "$lib/state/app.svelte";
    import Button from "./ui/Button.svelte";

    let {
        text,
        running = false,
        truncated = false,
        title = "Command output",
        empty = "Run a command to see its output here.",
    }: {
        text: string;
        running?: boolean;
        truncated?: boolean;
        title?: string;
        empty?: string;
    } = $props();
    let output = $state<HTMLDivElement>();
    let follow = $state(true);
    $effect(() => {
        text;
        if (follow)
            tick().then(() => {
                if (output) output.scrollTop = output.scrollHeight;
            });
    });
    async function copy() {
        try {
            await navigator.clipboard.writeText(text);
            app.notify("Command output copied.", "success");
        } catch (error) {
            app.error(error);
        }
    }
</script>

<section class="min-w-0 overflow-hidden">
    <div
        class="flex flex-wrap items-center justify-between gap-2 border-b border-border-tertiary px-4 py-2"
    >
        <h3 class="text-label-small">{title}</h3>
        <div class="flex gap-1">
            <Button
                scale="xs"
                kind="neutral"
                appearance="transparent"
                aria-pressed={follow}
                onclick={() => (follow = !follow)}>Follow output</Button
            >
            <Button
                scale="xs"
                kind="neutral"
                appearance="transparent"
                iconStart="copy"
                disabled={!text}
                onclick={copy}>Copy output</Button
            >
        </div>
    </div>
    {#if truncated}
        <p class="bg-warning-background px-4 py-2 text-caption">
            Earlier output was trimmed. Showing the retained tail.
        </p>
    {/if}
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard users need access to the scrollable output.) -->
    <div
        bind:this={output}
        role="region"
        tabindex="0"
        aria-label={title}
        onscroll={() => {
            if (output)
                follow =
                    output.scrollHeight -
                        output.scrollTop -
                        output.clientHeight <
                    40;
        }}
        class="h-64 overflow-auto bg-foreground-secondary p-4"
    >
        <pre
            class="whitespace-pre-wrap break-all text-caption leading-relaxed">{text ||
                (running ? "Waiting for output..." : empty)}</pre>
    </div>
</section>
