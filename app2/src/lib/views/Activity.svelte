<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import { desktop } from "$lib/services/desktop";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import RunSummary from "$lib/components/RunSummary.svelte";
    import CommandLog from "$lib/components/CommandLog.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    let tool = $state("--help");
    const tools = [
        { value: "--help", label: "CLI help", args: ["--help"], scoped: false },
        {
            value: "--version",
            label: "CLI version",
            args: ["--version"],
            scoped: false,
        },
        {
            value: "--print-config",
            label: "Print selected configuration",
            args: ["--print-config"],
            scoped: true,
        },
        {
            value: "--print-config-path",
            label: "Print configuration path",
            args: ["--print-config-path"],
            scoped: true,
        },
        {
            value: "dotnet-info",
            label: ".NET SDK information",
            args: ["dotnet", "--info"],
            scoped: false,
        },
    ];
    let selectedTool = $derived(tools.find((item) => item.value === tool)!);
</script>

<PageHeader
    eyebrow="Operations"
    title="Command history"
    description="Session history and CLI tools. Git and .NET commands run in their own workspaces; the last 20 commands are kept here."
>
    {#snippet actions()}<Button
            kind="neutral"
            appearance="outline-fill"
            scale="s"
            disabled={app.running || !app.runs.length}
            onclick={() => app.clearHistory()}>Clear history</Button
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
            (selectedTool.scoped && (!app.workspace || app.dirty))}
        onclick={() =>
            app.run(selectedTool.args, selectedTool.label, selectedTool.scoped)}
        >Run</Button
    >
    <span class="ml-auto text-caption text-text-tertiary"
        >Use Git or .NET operations to run workspace commands.</span
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
            <div class="space-y-3 p-4">
                <RunSummary {run} />
                {#if run.kind !== "tool" && run.context?.path === app.workspace?.path}
                    <Button
                        scale="s"
                        kind="neutral"
                        appearance="outline-fill"
                        onclick={() => app.showRun(run)}
                        >Open in {run.kind === "git" ? "Git" : ".NET"} workspace</Button
                    >
                {/if}
            </div>
            {#key run.id}
                <CommandLog
                    text={run.output}
                    running={run.status === "running"}
                    truncated={run.truncated}
                    empty="Command completed without output."
                />
            {/key}
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
                    Run a Git or .NET operation, or use the CLI tools above.
                    Operations stay in their workspace. Saved results and exit
                    codes are available here.
                </p>
            </div>
        {/if}
    </section>
</div>
{#if app.running}<p class="mt-4 text-caption text-text-secondary">
        Keep PACE open while this command runs. Repository operations are
        allowed to finish before another command starts.
    </p>{/if}
