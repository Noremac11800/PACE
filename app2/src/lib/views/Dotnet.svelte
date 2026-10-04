<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import { dotnetForm } from "$lib/state/dotnet.svelte";
    import {
        defaultDotnetOptions,
        dotnetArguments,
        dotnetNeedsConfirmation,
        dotnetTasks,
        supportsFramework,
        supportsNoRestore,
    } from "$lib/domain/dotnet";
    import {
        commandPreview,
        monitoredArgs,
        scopedArgs,
    } from "$lib/domain/commands";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import ScopeBar from "$lib/components/ScopeBar.svelte";
    import DotnetProperties from "$lib/components/DotnetProperties.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Input from "$lib/components/ui/Input.svelte";
    import Switch from "$lib/components/ui/Switch.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import Spinner from "$lib/components/ui/Spinner.svelte";
    import RunSummary from "$lib/components/RunSummary.svelte";
    import CommandLog from "$lib/components/CommandLog.svelte";
    import DotnetProgress from "$lib/components/DotnetProgress.svelte";
    import { commandOperation } from "$lib/domain/runs";

    let current = $derived(app.operationRun("dotnet"));
    let running = $derived(app.activeRun?.kind === "dotnet");
    let options = $derived(dotnetForm.options);
    let task = $derived(
        dotnetTasks.find((task) => task.value === options.task)!,
    );
    let properties = $derived(app.workspace?.config.build_props ?? []);
    let command = $derived.by((): { args: string[]; error: string | null } => {
        try {
            return { args: dotnetArguments(options, properties), error: null };
        } catch (error) {
            return {
                args: [],
                error: error instanceof Error ? error.message : String(error),
            };
        }
    });
    let preview = $derived(
        command.error
            ? ""
            : commandPreview(
                  scopedArgs(
                      app.workspace?.path ?? "",
                      app.from,
                      app.to,
                      monitoredArgs(command.args),
                  ),
              ),
    );
    let unavailable = $derived(
        app.locked ||
            app.filtering ||
            !app.selectedNames.length ||
            app.dirty ||
            !!command.error,
    );
    let operation = $derived(
        current?.operation ?? commandOperation(command.args),
    );

    async function run() {
        if (unavailable) return;
        if (
            dotnetNeedsConfirmation(options) &&
            !(await app.confirm(
                `Run ${options.rebuild && options.task === "build" ? "rebuild" : task.label.toLowerCase()}?`,
                `PACE will sync PACE.slnx for ${app.selectedNames.length} selected repositories and run this command. MSBuild can also process project references outside the selection. Review the command preview before continuing.`,
                "Run command",
            ))
        )
            return;
        await app.run(
            command.args,
            options.task === "build" && options.rebuild
                ? ".NET rebuild"
                : `.NET ${task.label.toLowerCase()}`,
        );
    }
</script>

<PageHeader
    compact
    eyebrow="Operations"
    title=".NET operations"
    description="Options, project stages, and output in one place."
>
    {#snippet actions()}
        <Button
            scale="s"
            kind="neutral"
            appearance="outline-fill"
            icon="refresh"
            label="Reset options"
            disabled={app.locked}
            onclick={() => (dotnetForm.options = defaultDotnetOptions())}
        />
        <Button type="submit" form="dotnet-command" disabled={unavailable}
            >{#if running}<Spinner scale="s" />Running…
            {:else}<Icon name="play" size={18} />{options.task === "custom"
                    ? "Run command"
                    : options.task === "build" && options.rebuild
                      ? "Rebuild solution"
                      : `${task.label} solution`}{/if}</Button
        >
    {/snippet}
</PageHeader>
<ScopeBar />
{#if app.dirty}<p
        role="status"
        class="mb-5 rounded border border-border-tertiary bg-warning-background p-4 text-body-small"
    >
        Save or discard your configuration edits before running commands.
    </p>{/if}

<div
    class="grid items-start gap-5 grid-cols-[260px_minmax(0,1fr)] 2xl:grid-cols-[300px_minmax(0,1fr)]"
>
    <form
        id="dotnet-command"
        class="max-h-[calc(100dvh-300px)] min-w-0 space-y-4 overflow-y-auto pr-1"
        onsubmit={(event) => {
            event.preventDefault();
            run();
        }}
    >
        <section class="panel">
            <div class="px-4 py-3">
                <div>
                    <h2 class="text-title-small">Next command options</h2>
                    <p class="mt-1 text-caption text-text-tertiary">
                        {task.description}
                    </p>
                </div>
            </div>
            <div class="space-y-4 border-t border-border-tertiary p-4">
                <div class="grid gap-4">
                    <label
                        class="space-y-2 text-body-small text-text-secondary"
                    >
                        <span class="block">Task</span>
                        <select
                            class="field-select"
                            aria-label="Dotnet task"
                            bind:value={dotnetForm.options.task}
                            disabled={app.locked}
                        >
                            {#each dotnetTasks as item}<option
                                    value={item.value}>{item.label}</option
                                >{/each}
                        </select>
                    </label>
                    {#if options.task !== "custom"}
                        <label
                            class="space-y-2 text-body-small text-text-secondary"
                        >
                            <span class="block">Build configuration</span>
                            <select
                                class="field-select"
                                aria-label="Build configuration"
                                bind:value={dotnetForm.options.configuration}
                                disabled={app.locked}
                            >
                                <option value="Debug">Debug</option><option
                                    value="Release">Release</option
                                >
                            </select>
                        </label>
                    {/if}
                </div>
                {#if options.task === "custom"}
                    <Input
                        label="Dotnet arguments"
                        variant="general"
                        bind:value={dotnetForm.options.customArgs}
                        disabled={app.locked}
                        clearable={false}
                        placeholder="build -c Release -t:Rebuild"
                        hint="Enter the arguments after dotnet. Do not supply a project or solution; pacev2 supplies PACE.slnx."
                    />
                {:else}
                    {#if supportsFramework(options.task)}
                        <Input
                            label="Target framework (optional)"
                            variant="general"
                            bind:value={dotnetForm.options.framework}
                            disabled={app.locked}
                            clearable={false}
                            placeholder="For example, net10.0 or net10.0-windows"
                        />
                    {/if}
                    {#if supportsNoRestore(options.task) || options.task === "build"}<div
                            class="grid gap-4 border-t border-border-tertiary pt-4"
                        >
                            {#if supportsNoRestore(options.task)}<Switch
                                    label="Skip restore"
                                    bind:checked={dotnetForm.options.noRestore}
                                    disabled={app.locked}
                                />{/if}
                            {#if options.task === "build"}<Switch
                                    label="Rebuild all outputs"
                                    bind:checked={dotnetForm.options.rebuild}
                                    disabled={app.locked}
                                />{/if}
                        </div>{/if}
                    {#if options.task === "build" && options.rebuild}<p
                            class="text-caption leading-relaxed text-text-secondary"
                        >
                            Uses <code>-t:Rebuild</code> to clean and build again.
                            This also reproduces compiler warnings that an incremental
                            build would skip.
                        </p>{/if}
                    <Input
                        label="Additional arguments (optional)"
                        variant="general"
                        bind:value={dotnetForm.options.additionalArgs}
                        disabled={app.locked}
                        clearable={false}
                        placeholder="--verbosity minimal"
                    />
                {/if}
                <div class="border-t border-border-tertiary pt-5">
                    <Switch
                        label="Summarize build warnings"
                        bind:checked={dotnetForm.options.summarizeWarnings}
                        disabled={app.locked}
                    />
                </div>
            </div>
        </section>

        {#if options.task !== "custom" && properties.length}
            <details class="panel" bind:open={dotnetForm.propertiesOpen}>
                <summary class="cursor-pointer px-4 py-3 text-label-medium"
                    >MSBuild properties ({Object.keys(options.properties)
                        .length} enabled)</summary
                >
                <DotnetProperties
                    {properties}
                    bind:values={dotnetForm.options.properties}
                    disabled={app.locked}
                    compact
                />
            </details>
        {/if}

        <section class="panel overflow-hidden">
            <div class="px-4 py-3">
                <h2 class="text-label-medium">Next command</h2>
            </div>
            <div class="bg-foreground-secondary p-4">
                {#if command.error}<p
                        role="alert"
                        class="text-body-small text-status-danger"
                    >
                        {command.error}
                    </p>
                {:else}<code
                        data-testid="dotnet-preview"
                        class="block whitespace-pre-wrap break-all text-caption leading-relaxed text-text-secondary"
                        >{preview}</code
                    >{/if}
            </div>
        </section>
    </form>
    <div class="min-w-0 space-y-4">
        {#if current}
            <RunSummary
                run={current}
                runs={app.operationRuns("dotnet")}
                onselect={(id) => (app.operationSelection.dotnet = id)}
            />
        {:else}
            <section class="panel p-4">
                <h2 class="text-title-small">
                    Ready to {options.task === "custom" ? "run" : options.task}
                </h2>
                <p
                    class="mt-2 text-body-small leading-relaxed text-text-secondary"
                >
                    Choose your options and run the command. Progress and output
                    will stay in this workspace.
                </p>
            </section>
        {/if}
        {#if ["build", "publish", "test"].includes(operation)}
            <DotnetProgress
                run={current}
                projects={current?.context?.projects ?? app.selectedProjects}
                {operation}
            />
        {/if}
        <div class="panel overflow-hidden">
            {#key current?.id ?? "idle"}
                <CommandLog
                    text={current?.output ?? ""}
                    running={current?.status === "running"}
                    truncated={current?.truncated}
                    empty={current
                        ? "Command completed without output."
                        : "Build messages, test results, warnings, and errors appear here."}
                />
            {/key}
        </div>
        <p class="text-caption leading-relaxed text-text-tertiary">
            MSBuild may also process references outside the selected scope.
            Options and scope changes apply to the next command; the displayed
            run keeps its original settings. Requires .NET SDK 9.0.200+.
        </p>
    </div>
</div>
