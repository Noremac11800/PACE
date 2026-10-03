<script lang="ts">
    import { tick } from "svelte";
    import { app } from "$lib/state/app.svelte";
    import { desktop } from "$lib/services/desktop";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Chip from "$lib/components/ui/Chip.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import Spinner from "$lib/components/ui/Spinner.svelte";
    let tool = $state("--help");
    let output = $state<HTMLDivElement>();
    let follow = $state(true);
    const tools = [
        { value: "--help", label: "CLI help" },
        { value: "--version", label: "CLI version" },
        { value: "--print-config", label: "Print selected configuration" },
        { value: "--print-config-path", label: "Print configuration path" },
    ];
    $effect(() => {
        const text = app.selectedRun?.output;
        if (text && follow)
            tick().then(() => {
                if (output) output.scrollTop = output.scrollHeight;
            });
    });
    async function copy() {
        try {
            await navigator.clipboard.writeText(app.selectedRun?.output ?? "");
            app.notify("Command output copied.", "success");
        } catch (error) {
            app.error(error);
        }
    }
</script>

<PageHeader
    eyebrow="Operations"
    title="Command activity"
    description="Live output and results for this session. The last 20 commands are kept until you close the app."
>
    {#snippet actions()}<Button
            kind="neutral"
            appearance="outline-fill"
            scale="s"
            disabled={app.running || !app.runs.length}
            onclick={() => {
                app.runs = [];
                app.selectedRunId = null;
            }}>Clear history</Button
        >{/snippet}
</PageHeader>
<section
    class="panel mb-5 flex flex-wrap items-center gap-3 p-4"
    aria-label="CLI tools"
>
    <Icon name="console" size={20} class="text-brand" /><span
        class="text-label-medium">CLI tools</span
    >
    <select
        aria-label="CLI command"
        bind:value={tool}
        class="field-select max-w-72"
    >
        {#each tools as item}<option value={item.value}>{item.label}</option
            >{/each}
    </select>
    <Button
        scale="s"
        iconStart="play"
        disabled={!desktop ||
            app.locked ||
            app.filtering ||
            (tool.startsWith("--print") && (!app.workspace || app.dirty))}
        onclick={() =>
            app.run(
                [tool],
                tools.find((item) => item.value === tool)?.label ?? tool,
                tool.startsWith("--print"),
            )}>Run</Button
    >
    <span class="ml-auto text-caption text-text-tertiary"
        >Git commands are available in Git operations.</span
    >
</section>
<div
    class="panel grid min-h-[480px] overflow-hidden grid-cols-[210px_minmax(0,1fr)]"
>
    <aside
        class="border-r border-border-tertiary bg-foreground-primary"
        aria-label="Command history"
    >
        <div
            class="border-b border-border-tertiary px-4 py-4 text-label-small text-text-secondary"
        >
            THIS SESSION
        </div>
        <div class="max-h-[600px] overflow-y-auto">
            {#each app.runs as run}
                <button
                    onclick={() => {
                        app.selectedRunId = run.id;
                        follow = true;
                    }}
                    aria-current={app.selectedRunId === run.id
                        ? "true"
                        : undefined}
                    class={[
                        "flex w-full gap-2 border-b border-border-tertiary p-4 text-left",
                        app.selectedRunId === run.id
                            ? "bg-foreground-current"
                            : "hover:bg-transparent-hover",
                    ]}
                >
                    <Icon
                        name={run.status === "succeeded"
                            ? "check-circle"
                            : run.status === "running"
                              ? "clock"
                              : "exclamation-mark-triangle"}
                        size={16}
                        class={run.status === "failed"
                            ? "text-status-danger"
                            : "text-brand"}
                    />
                    <div class="min-w-0">
                        <p class="text-label-small leading-relaxed">
                            {run.label}
                        </p>
                        <p class="mt-1 text-caption text-text-tertiary">
                            {run.started.toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                            })} · {run.status}
                        </p>
                    </div>
                </button>
            {:else}<p
                    class="px-4 py-6 text-body-small leading-relaxed text-text-tertiary"
                >
                    Your command history will appear here.
                </p>{/each}
        </div>
    </aside>
    <section class="flex min-w-0 flex-col">
        {#if app.selectedRun}
            {@const run = app.selectedRun}
            <div
                class="flex flex-wrap items-center justify-between gap-3 border-b border-border-tertiary px-5 py-3"
            >
                <div class="flex items-center gap-2" aria-live="polite">
                    {#if run.status === "running"}<Spinner scale="s" /><span
                            class="text-label-medium">Running</span
                        >{:else}<Chip
                            label={run.status === "succeeded"
                                ? "Completed"
                                : "Failed"}
                            scale="s"
                            tone={run.status === "succeeded" ? "green" : "red"}
                        /><span class="text-caption text-text-tertiary"
                            >{run.code === null
                                ? "Process error"
                                : `Exit ${run.code}`} · {(
                                (run.duration ?? 0) / 1000
                            ).toFixed(1)}s</span
                        >{/if}
                </div>
                <Button
                    iconStart="copy"
                    kind="neutral"
                    appearance="transparent"
                    scale="s"
                    onclick={copy}
                    disabled={!run.output}>Copy output</Button
                >
            </div>
            <code
                class="block break-all border-b border-border-tertiary bg-foreground-secondary px-5 py-4 text-caption leading-relaxed text-text-secondary"
                >{run.command}</code
            >
            {#if run.truncated}<p
                    class="bg-warning-background px-5 py-2 text-caption"
                >
                    Earlier output was trimmed. Showing the last 250,000
                    characters.
                </p>{/if}
            <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard users need to focus this scrollable output region.) -->
            <div
                bind:this={output}
                role="region"
                tabindex="0"
                aria-label="Command output"
                onscroll={() => {
                    if (output)
                        follow =
                            output.scrollHeight -
                                output.scrollTop -
                                output.clientHeight <
                            40;
                }}
                class="min-h-80 max-h-[540px] flex-1 overflow-auto bg-foreground-secondary p-5"
            >
                <pre
                    class="whitespace-pre-wrap break-all text-caption leading-relaxed">{run.output ||
                        (run.status === "running"
                            ? "Waiting for output...\n"
                            : "Command completed without output.\n")}</pre>
            </div>
        {:else}
            <div
                class="flex flex-1 flex-col items-center justify-center p-8 text-center"
            >
                <Icon
                    name="console"
                    size={32}
                    class="mb-4 text-text-tertiary"
                />
                <h2 class="text-title-medium">Ready when you are</h2>
                <p
                    class="mt-2 max-w-md text-body-small leading-relaxed text-text-secondary"
                >
                    Run a Git operation or use the CLI tools above. Output,
                    errors, and exit codes will appear here.
                </p>
            </div>
        {/if}
    </section>
</div>
{#if app.running}<p class="mt-4 text-caption text-text-secondary">
        Keep PACE open while this command runs. Repository operations are
        allowed to finish before another command starts.
    </p>{/if}
