<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import {
        chooseDirectory,
        choosePython,
        desktop,
    } from "$lib/services/desktop";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import ThemeToggle from "$lib/components/ThemeToggle.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Input from "$lib/components/ui/Input.svelte";
    import Chip from "$lib/components/ui/Chip.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    let python = $state(app.options.python);
    let directory = $state(app.options.directory);
    let edited = $state(false);
    $effect(() => {
        if (!edited) {
            python = app.options.python;
            directory = app.options.directory;
        }
    });
    async function browse(kind: "python" | "directory") {
        try {
            const path = await (kind === "python"
                ? choosePython()
                : chooseDirectory());
            if (path) {
                edited = true;
                if (kind === "python") python = path;
                else directory = path;
            }
        } catch (error) {
            app.error(error);
        }
    }
</script>

<PageHeader
    eyebrow="Application"
    title="Settings"
    description="Make PACE feel at home and connect it to your development tools."
/>
<div class="max-w-4xl space-y-6">
    <section class="panel">
        <div class="panel-heading">
            <div>
                <h2 class="text-title-small">Appearance</h2>
                <p class="mt-1 text-caption text-text-tertiary">
                    Use your system preference or choose a theme for PACE.
                </p>
            </div>
            <Icon name="brightness" class="text-text-tertiary" />
        </div>
        <div class="flex flex-wrap items-center justify-between gap-4 p-5">
            <div>
                <p class="text-label-medium">Color theme</p>
                <p class="mt-1 text-caption text-text-secondary">
                    Saved on this device.
                </p>
            </div>
            <ThemeToggle />
        </div>
    </section>
    <section class="panel">
        <div class="panel-heading">
            <div>
                <h2 class="text-title-small">Python runtime</h2>
                <p class="mt-1 text-caption text-text-tertiary">
                    PACE runs your installed pacev2 module, not the legacy pace
                    command.
                </p>
            </div>
            <Icon name="console" class="text-text-tertiary" />
        </div>
        <form
            class="space-y-5 p-5"
            onsubmit={(event) => {
                event.preventDefault();
                app.connect({ python, directory });
            }}
        >
            <div class="flex items-end gap-2">
                <Input
                    label="Python executable"
                    variant="general"
                    bind:value={python}
                    oninput={() => (edited = true)}
                    clearable={false}
                    placeholder="Full path to Python in your pacev2 environment"
                    class="flex-1"
                /><Button
                    kind="neutral"
                    appearance="outline-fill"
                    icon="folder-open"
                    label="Browse for Python"
                    disabled={!desktop || app.locked}
                    onclick={() => browse("python")}
                />
            </div>
            <div class="flex items-end gap-2">
                <Input
                    label="Working directory"
                    variant="general"
                    bind:value={directory}
                    oninput={() => (edited = true)}
                    clearable={false}
                    placeholder="Working directory for CLI commands"
                    class="flex-1"
                /><Button
                    kind="neutral"
                    appearance="outline-fill"
                    icon="folder-open"
                    label="Browse for working directory"
                    disabled={!desktop || app.locked}
                    onclick={() => browse("directory")}
                />
            </div>
            <div
                class="rounded bg-foreground-secondary p-4 text-body-small leading-relaxed text-text-secondary"
            >
                During development, PACE detects <code>pacev2/.venv</code>. For
                a packaged app, choose a Python executable where pacev2 is
                installed. Relative repository and cache paths resolve from the
                working directory above.
            </div>
            <div class="flex justify-end">
                <Button
                    type="submit"
                    iconStart="link"
                    disabled={!desktop ||
                        app.locked ||
                        !python.trim() ||
                        !directory.trim()}>Save & connect</Button
                >
            </div>
        </form>
    </section>
    <section class="panel">
        <div class="panel-heading">
            <div>
                <h2 class="text-title-small">Development tools</h2>
                <p class="mt-1 text-caption text-text-tertiary">
                    Git is required for repository operations. .NET is optional
                    for the current UI.
                </p>
            </div>
            <Button
                scale="s"
                kind="neutral"
                appearance="outline-fill"
                iconStart="refresh"
                disabled={!desktop || app.locked}
                onclick={() => app.checkTools()}>Check tools</Button
            >
        </div>
        {#each app.diagnostics as tool}
            <div
                class="flex items-center gap-4 border-b border-border-tertiary px-5 py-4 last:border-0"
            >
                <Icon
                    name={tool.available
                        ? "check-circle"
                        : "exclamation-mark-triangle"}
                    size={18}
                    class={tool.available ? "text-brand" : "text-status-danger"}
                /><span class="w-24 shrink-0 text-label-medium"
                    >{tool.name}</span
                ><span
                    class="min-w-0 flex-1 break-all text-caption leading-relaxed text-text-secondary"
                    >{tool.version}</span
                ><Chip
                    label={tool.available ? "Available" : "Unavailable"}
                    tone={tool.available ? "green" : "red"}
                    scale="s"
                />
            </div>
        {:else}<p class="p-5 text-body-small text-text-tertiary">
                Run a check to see which tools are available to PACE.
            </p>{/each}
    </section>
    <div
        class="flex items-center gap-3 px-1 pb-4 text-caption leading-relaxed text-text-tertiary"
    >
        <span
            aria-hidden="true"
            class="size-8 shrink-0 bg-brand [mask-image:url('/pace.svg')] [mask-size:contain] [mask-repeat:no-repeat]"
        ></span>
        <p>
            PACE Desktop {app.appVersion}<br />Project Automation and
            Configuration Engine
        </p>
        <span class="ml-auto">Built with the Survey123 design system</span>
    </div>
</div>
