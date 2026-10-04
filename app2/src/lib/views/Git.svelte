<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import { gitForm } from "$lib/state/git.svelte";
    import {
        commandPreview,
        monitoredArgs,
        parseArguments,
        scopedArgs,
    } from "$lib/domain/commands";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import ScopeBar from "$lib/components/ScopeBar.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Input from "$lib/components/ui/Input.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import Spinner from "$lib/components/ui/Spinner.svelte";
    import RunSummary from "$lib/components/RunSummary.svelte";
    import GitResults from "$lib/components/GitResults.svelte";
    import CommandLog from "$lib/components/CommandLog.svelte";
    let current = $derived(app.operationRun("git"));
    let running = $derived(app.activeRun?.kind === "git");
    let unavailable = $derived(
        app.locked || app.filtering || !app.selectedNames.length || app.dirty,
    );
    let preview = $derived.by(() => {
        try {
            return commandPreview(
                scopedArgs(
                    app.workspace?.path ?? "",
                    app.from,
                    app.to,
                    monitoredArgs([
                        "git",
                        ...parseArguments(gitForm.customArgs),
                    ]),
                ),
            );
        } catch {
            return "Finish the quoted argument to preview this command.";
        }
    });

    async function run(args: string[], label: string, confirm = false) {
        if (
            confirm &&
            !(await app.confirm(
                `Run ${label.toLowerCase()}?`,
                `This will run against ${app.selectedNames.length} repositories in the selected scope. Git authentication must already be configured.`,
                "Run command",
            ))
        )
            return;
        await app.run(["git", ...args], label);
    }

    async function runCustom() {
        try {
            const args = parseArguments(gitForm.customArgs);
            if (!args.length) throw new Error("Enter a Git subcommand first.");
            await run(args, "Custom Git command", true);
        } catch (error) {
            app.error(error);
        }
    }
</script>

<PageHeader
    compact
    eyebrow="Operations"
    title="Git operations"
    description="Repositories, actions, and output in one place."
>
    {#snippet actions()}
        <Button
            scale="s"
            kind="neutral"
            appearance="outline-fill"
            iconStart="download"
            disabled={unavailable}
            onclick={() => run(["clone"], "Clone repositories", true)}
            >Clone missing</Button
        >
        <Button
            scale="s"
            kind="neutral"
            appearance="outline-fill"
            iconStart="refresh"
            disabled={unavailable}
            onclick={() =>
                run(["pull", "--ff-only"], "Pull latest changes", true)}
            >Pull latest</Button
        >
        <Button
            scale="s"
            disabled={unavailable}
            onclick={() =>
                run(["status", "--short", "--branch"], "Check status")}
        >
            {#if running}<Spinner scale="s" />Running…{:else}<Icon
                    name="list"
                    size={16}
                />Check status{/if}
        </Button>
    {/snippet}
</PageHeader>
<ScopeBar />
{#if app.dirty}<p
        role="status"
        class="mb-5 rounded border border-border-tertiary bg-warning-background p-4 text-body-small"
    >
        Save or discard your configuration edits before running commands.
    </p>{/if}
<div class="space-y-4">
    <details class="panel" bind:open={gitForm.customOpen}>
        <summary class="cursor-pointer px-4 py-3 text-label-medium"
            >Custom Git command</summary
        >
        <form
            class="space-y-3 border-t border-border-tertiary p-4"
            onsubmit={(event) => {
                event.preventDefault();
                runCustom();
            }}
        >
            <div class="flex items-end gap-3">
                <Input
                    label="Git arguments"
                    variant="general"
                    bind:value={gitForm.customArgs}
                    disabled={app.locked}
                    placeholder={'checkout -b "feature/my-change"'}
                    clearable={false}
                    class="min-w-0 flex-1"
                />
                <Button
                    type="submit"
                    iconStart="play"
                    disabled={unavailable || !gitForm.customArgs.trim()}
                    >Run command</Button
                >
            </div>
            <code
                class="block break-all rounded bg-foreground-secondary p-3 text-caption leading-relaxed"
                >{preview}</code
            >
        </form>
    </details>
    {#if current}
        <RunSummary
            run={current}
            runs={app.operationRuns("git")}
            onselect={(id) => (app.operationSelection.git = id)}
        />
    {/if}
    <GitResults
        run={current}
        projects={current?.context?.projects ?? app.selectedProjects}
        repoRoot={current?.context?.repoRoot ?? app.workspace?.repoRoot ?? ""}
    />
    {#if current}
        <details class="panel" open={current.status === "failed"}>
            <summary class="cursor-pointer px-4 py-3 text-label-small"
                >Full command log</summary
            >
            {#key current.id}
                <CommandLog
                    text={current.output}
                    running={current.status === "running"}
                    truncated={current.truncated}
                    empty="Command completed without output."
                />
            {/key}
        </details>
    {/if}
    <p class="text-caption leading-relaxed text-text-tertiary">
        Clone and pull ask for confirmation. Git runs without interactive
        prompts or editors.
        {#if current}Results show the saved run scope above; changing the scope
            applies to your next command.{/if}
    </p>
</div>
