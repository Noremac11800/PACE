<script lang="ts">
    import { app } from "$lib/state/app.svelte";
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
    let custom = $state("status --short --branch");
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
                    monitoredArgs(["git", ...parseArguments(custom)]),
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
            const args = parseArguments(custom);
            if (!args.length) throw new Error("Enter a Git subcommand first.");
            await run(args, "Custom Git command", true);
        } catch (error) {
            app.error(error);
        }
    }
</script>

<PageHeader
    eyebrow="Operations"
    title="Git operations"
    description="Run Git across your selected repositories in parallel. Every command uses pacev2's non-interactive batch runner."
/>
<ScopeBar />
{#if app.dirty}<p
        role="status"
        class="mb-5 rounded border border-border-tertiary bg-warning-background p-4 text-body-small"
    >
        Save or discard your configuration edits before running commands.
    </p>{/if}
<div class="mb-6 grid grid-cols-3 gap-4">
    {#each [{ title: "Check status", eyebrow: "Inspect", icon: "list" as const, description: "Review branches and local changes without modifying repositories.", command: ["status", "--short", "--branch"], confirm: false, button: "Check status" }, { title: "Clone repositories", eyebrow: "Set up", icon: "download" as const, description: "Clone configured remotes. Existing checkouts are safely skipped.", command: ["clone"], confirm: true, button: "Clone missing" }, { title: "Pull latest changes", eyebrow: "Sync", icon: "refresh" as const, description: "Fast-forward each checkout. Diverged branches fail rather than merge.", command: ["pull", "--ff-only"], confirm: true, button: "Pull latest" }] as action}
        <section class="panel flex flex-col p-5">
            <div class="mb-5 flex items-center justify-between">
                <span class="eyebrow">{action.eyebrow}</span><Icon
                    name={action.icon}
                    class="text-brand"
                    size={24}
                />
            </div>
            <h2 class="text-title-medium">{action.title}</h2>
            <p
                class="mt-2 mb-6 flex-1 text-body-small leading-relaxed text-text-secondary"
            >
                {action.description}
            </p>
            <Button
                width="full"
                appearance={action.confirm ? "outline-fill" : "solid"}
                disabled={unavailable}
                onclick={() =>
                    run(action.command, action.title, action.confirm)}
                >{action.button}</Button
            >
        </section>
    {/each}
</div>
<section class="panel">
    <div class="panel-heading">
        <div>
            <h2 class="text-title-small">Custom Git command</h2>
            <p class="mt-1 text-caption text-text-tertiary">
                Arguments are passed directly to Git, never through a shell.
            </p>
        </div>
        <Icon name="console" class="text-text-tertiary" />
    </div>
    <form
        class="space-y-4 p-5"
        onsubmit={(event) => {
            event.preventDefault();
            runCustom();
        }}
    >
        <div class="flex items-end gap-3">
            <span class="mono pb-3 text-body-small text-text-tertiary">git</span
            ><Input
                label="Git arguments"
                variant="general"
                bind:value={custom}
                placeholder={'checkout -b "feature/my-change"'}
                clearable={false}
                class="flex-1"
            /><Button
                type="submit"
                iconStart="play"
                disabled={unavailable || !custom.trim()}>Run command</Button
            >
        </div>
        <div class="rounded bg-foreground-secondary p-4">
            <p class="eyebrow mb-2">Command preview</p>
            <code
                class="block break-all text-caption leading-relaxed text-text-secondary"
                >{preview}</code
            >
        </div>
    </form>
</section>
<div
    class="mt-5 flex items-start gap-3 text-body-small leading-relaxed text-text-secondary"
>
    <Icon name="information" size={18} class="mt-0.5 text-status-info" />
    <p>
        Commands run on the selected dependency range. Missing checkouts and
        projects without remotes are reported by pacev2. Interactive prompts,
        editors, and credential input are disabled.
    </p>
</div>
