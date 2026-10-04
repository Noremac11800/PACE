<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import { desktop } from "$lib/services/desktop";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import EmptyState from "$lib/components/EmptyState.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import Chip from "$lib/components/ui/Chip.svelte";
    import Card from "$lib/components/ui/Card.svelte";
    let config = $derived(app.workspace?.config);
    let groups = $derived(
        new Set(
            config?.projects
                .map((project) => project.sln_group)
                .filter(Boolean),
        ).size,
    );
    let links = $derived(
        config?.projects.reduce(
            (count, project) => count + project.depends_on.length,
            0,
        ) ?? 0,
    );
</script>

<PageHeader
    title="Workspace overview"
    description="One place for your repositories, their dependencies, and the work between them."
>
    {#snippet actions()}
        <Button
            kind="neutral"
            appearance="outline-fill"
            iconStart="folder-open"
            disabled={!desktop || app.locked}
            onclick={() => app.open()}>Open configuration</Button
        >
    {/snippet}
</PageHeader>

{#if app.workspace && config}
    <section class="mb-6 grid grid-cols-3 gap-4" aria-label="Workspace summary">
        {#each [{ label: "Repositories", value: config.projects.length, detail: "Managed in this workspace", icon: "folders" as const }, { label: "Solution groups", value: groups, detail: "Organized by application", icon: "folder" as const }, { label: "Dependency links", value: links, detail: "Declared project relationships", icon: "code-branch" as const }] as metric}
            <div class="panel p-5">
                <div
                    class="mb-4 flex items-center justify-between text-text-secondary"
                >
                    <span class="text-label-medium">{metric.label}</span><Icon
                        name={metric.icon}
                        size={20}
                        class="text-brand"
                    />
                </div>
                <p class="text-headline-large">{metric.value}</p>
                <p class="mt-2 text-caption text-text-tertiary">
                    {metric.detail}
                </p>
            </div>
        {/each}
    </section>
    <div class="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(280px,1fr)]">
        <section class="panel min-w-0">
            <div class="panel-heading">
                <h2 class="text-title-small">Repositories</h2>
                <Button
                    scale="s"
                    appearance="transparent"
                    iconEnd="chevron-right"
                    onclick={() => (app.view = "repositories")}>View all</Button
                >
            </div>
            {#if config.projects.length}
                {#each config.projects.slice(0, 6) as project}
                    <button
                        class="flex w-full items-center gap-3 border-b border-border-tertiary px-5 py-4 text-left last:border-0 hover:bg-transparent-hover"
                        onclick={() => (app.view = "repositories")}
                    >
                        <span
                            class="grid size-9 shrink-0 place-items-center rounded bg-foreground-secondary text-text-secondary"
                            ><Icon name="code-branch" size={18} /></span
                        >
                        <div class="min-w-0 flex-1">
                            <p class="truncate text-label-medium">
                                {project.name}
                            </p>
                            <p
                                class="mt-1 truncate text-caption text-text-tertiary"
                            >
                                {project.csproj_path}
                            </p>
                        </div>
                        {#if project.sln_group}<Chip
                                label={project.sln_group}
                                scale="s"
                                appearance="none"
                            />{/if}
                        <Icon
                            name="chevron-right"
                            size={16}
                            class="text-text-tertiary"
                        />
                    </button>
                {/each}
            {:else}
                <div
                    class="p-6 text-body-small leading-relaxed text-text-secondary"
                >
                    No repositories yet. Add projects in your configuration to
                    get started.
                </div>
            {/if}
        </section>
        <section class="panel min-w-0">
            <div class="panel-heading">
                <h2 class="text-title-small">Active configuration</h2>
                <Icon name="file-code" size={20} class="text-text-tertiary" />
            </div>
            <div class="space-y-5 p-5">
                <div>
                    <p class="eyebrow mb-2">Configuration</p>
                    <p class="text-title-small">{app.name}</p>
                    <p
                        class="mt-2 break-all text-caption leading-relaxed text-text-tertiary"
                    >
                        {app.workspace.path}
                    </p>
                </div>
                <div>
                    <p class="eyebrow mb-2">Repository directory</p>
                    <p class="break-all text-body-small leading-relaxed">
                        {app.workspace.repoRoot}
                    </p>
                </div>
                <div class="flex items-center gap-2">
                    <Chip
                        label={`pacev2 ${app.workspace.version}`}
                        iconStart="check-circle"
                        scale="s"
                    /><span class="text-caption text-text-tertiary"
                        >Connected</span
                    >
                </div>
                <Button
                    width="full"
                    kind="neutral"
                    appearance="outline-fill"
                    iconStart="file-code"
                    onclick={() => (app.view = "configuration")}
                    >Edit configuration</Button
                >
            </div>
        </section>
    </div>
    <section class="mt-7">
        <h2 class="mb-4 text-title-small">Keep work moving</h2>
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
            <Card
                heading="Build your solution"
                description="Build, test, and inspect compiler warnings."
                size="l"
                thumbnail={false}
                onclick={() => (app.view = "dotnet")}
            >
                {#snippet contextual()}<Icon
                        name="gear"
                        size={16}
                        class="text-brand"
                    /><span class="text-caption text-text-secondary"
                        >.NET operations</span
                    >{/snippet}
                {#snippet status()}<Icon
                        name="arrow-right"
                        size={16}
                    />{/snippet}
            </Card>
            <Card
                heading="Inspect repositories"
                description="Run Git status across your workspace."
                size="l"
                thumbnail={false}
                onclick={() => (app.view = "git")}
            >
                {#snippet contextual()}<Icon
                        name="code-branch"
                        size={16}
                        class="text-brand"
                    /><span class="text-caption text-text-secondary"
                        >Git operations</span
                    >{/snippet}
                {#snippet status()}<Icon
                        name="arrow-right"
                        size={16}
                    />{/snippet}
            </Card>
            <Card
                heading="Understand dependencies"
                description="See how your projects fit together."
                size="l"
                thumbnail={false}
                onclick={() => (app.view = "dependencies")}
            >
                {#snippet contextual()}<Icon
                        name="link"
                        size={16}
                        class="text-brand"
                    /><span class="text-caption text-text-secondary"
                        >Dependency map</span
                    >{/snippet}
                {#snippet status()}<Icon
                        name="arrow-right"
                        size={16}
                    />{/snippet}
            </Card>
            <Card
                heading="Review command history"
                description="A clear history of this session's work."
                size="l"
                thumbnail={false}
                onclick={() => (app.view = "activity")}
            >
                {#snippet contextual()}<Icon
                        name="console"
                        size={16}
                        class="text-brand"
                    /><span class="text-caption text-text-secondary"
                        >{app.runs.length} commands this session</span
                    >{/snippet}
                {#snippet status()}<Icon
                        name="arrow-right"
                        size={16}
                    />{/snippet}
            </Card>
        </div>
    </section>
{:else}
    <EmptyState
        icon="folders"
        title={desktop
            ? "Bring your workspace together"
            : "Your desktop workspace starts here"}
        description={desktop
            ? "Open an existing PACE TOML configuration, or create one to organize your .NET repositories. If the CLI could not connect, check your Python runtime in Settings."
            : "This browser preview shows the interface only. Launch the Tauri desktop app to connect to pacev2, open local configurations, and run Git and dotnet commands."}
    >
        {#snippet actions()}
            <Button
                iconStart="plus"
                disabled={!desktop || app.locked}
                onclick={() => app.create()}>New configuration</Button
            >
            <Button
                kind="neutral"
                appearance="outline-fill"
                iconStart="gear"
                onclick={() => (app.view = "settings")}>Runtime settings</Button
            >
        {/snippet}
    </EmptyState>
    <div class="mt-6 grid grid-cols-3 gap-4">
        {#each [{ title: "Organize", text: "Manage repositories and solution groups with a single TOML configuration." }, { title: "Understand", text: "Explore project dependencies and select an inclusive execution range." }, { title: "Execute", text: "Run Git and dotnet commands with live output and clear exit statuses." }] as feature}
            <div class="panel p-5">
                <h2 class="mb-2 text-title-small">{feature.title}</h2>
                <p class="text-body-small leading-relaxed text-text-secondary">
                    {feature.text}
                </p>
            </div>
        {/each}
    </div>
{/if}
