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
    import { commandPreview, scopedArgs } from "$lib/domain/commands";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import ScopeBar from "$lib/components/ScopeBar.svelte";
    import DotnetProperties from "$lib/components/DotnetProperties.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Input from "$lib/components/ui/Input.svelte";
    import Switch from "$lib/components/ui/Switch.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";

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
                      command.args,
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
    eyebrow="Operations"
    title=".NET operations"
    description="Build and manage your solution through pacev2. MSBuild handles dependency ordering and parallel execution."
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
        <Button
            scale="s"
            kind="neutral"
            appearance="transparent"
            iconStart="console"
            onclick={() => (app.view = "activity")}>View activity</Button
        >
        <Button
            type="submit"
            form="dotnet-command"
            iconStart="play"
            disabled={unavailable}
            >{options.task === "custom"
                ? "Run command"
                : options.task === "build" && options.rebuild
                  ? "Rebuild solution"
                  : `${task.label} solution`}</Button
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

<form
    id="dotnet-command"
    class="space-y-5"
    onsubmit={(event) => {
        event.preventDefault();
        run();
    }}
>
    <section class="panel">
        <div class="panel-heading">
            <div>
                <h2 class="text-title-small">Command options</h2>
                <p class="mt-1 text-caption text-text-tertiary">
                    {task.description}
                </p>
            </div>
            <Icon name="gear" class="text-brand" />
        </div>
        <div class="space-y-5 p-5">
            <div class="grid gap-5 lg:grid-cols-2">
                <label class="space-y-2 text-body-small text-text-secondary">
                    <span class="block">Task</span>
                    <select
                        class="field-select"
                        aria-label="Dotnet task"
                        bind:value={dotnetForm.options.task}
                        disabled={app.locked}
                    >
                        {#each dotnetTasks as item}<option value={item.value}
                                >{item.label}</option
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
                        hint="Leave empty to use all configured targets. pacev2 evaluates compatibility when a framework is specified."
                    />
                {/if}
                {#if supportsNoRestore(options.task) || options.task === "build"}<div
                        class="grid gap-4 border-t border-border-tertiary pt-5 lg:grid-cols-2"
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
                        Uses <code>-t:Rebuild</code> to clean and build again. This
                        also reproduces compiler warnings that an incremental build
                        would skip.
                    </p>{/if}
                <Input
                    label="Additional arguments (optional)"
                    variant="general"
                    bind:value={dotnetForm.options.additionalArgs}
                    disabled={app.locked}
                    clearable={false}
                    placeholder="--verbosity minimal"
                    hint="Appended after the form options. Quote arguments containing spaces; shell operators are not executed."
                />
            {/if}
            <div class="border-t border-border-tertiary pt-5">
                <Switch
                    label="Summarize build warnings"
                    bind:checked={dotnetForm.options.summarizeWarnings}
                    disabled={app.locked}
                />
                <p
                    class="mt-2 text-caption leading-relaxed text-text-secondary"
                >
                    Adds <code>-w</code> before the dotnet subcommand. Summaries
                    appear in command output and are saved by pacev2 under
                    <code>~/.pace/logs</code>.
                </p>
            </div>
        </div>
    </section>

    {#if options.task !== "custom" && properties.length}
        <DotnetProperties
            {properties}
            bind:values={dotnetForm.options.properties}
            disabled={app.locked}
        />
    {/if}

    <section class="panel overflow-hidden">
        <div class="panel-heading">
            <h2 class="text-title-small">Command preview</h2>
            <span class="text-caption text-text-tertiary"
                >pacev2 · PACE.slnx</span
            >
        </div>
        <div class="bg-foreground-secondary p-5">
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
        <div
            class="flex flex-wrap items-center justify-between gap-4 border-t border-border-tertiary p-4"
        >
            <p class="text-caption text-text-secondary">
                Output and exit status will appear in Command activity.
            </p>
        </div>
    </section>
</form>
<div
    class="mt-5 flex items-start gap-3 text-body-small leading-relaxed text-text-secondary"
>
    <Icon name="information" size={18} class="mt-0.5 text-status-info" />
    <p>
        Scope controls the direct members of <code>PACE.slnx</code>, not every
        project MSBuild may build. Referenced projects outside the scope can
        still run. .NET SDK 9.0.200 or newer is required for solution support.
    </p>
</div>
