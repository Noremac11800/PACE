<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import { dependencyLayers } from "$lib/domain/dependencies";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import ScopeBar from "$lib/components/ScopeBar.svelte";
    import EmptyState from "$lib/components/EmptyState.svelte";
    import Chip from "$lib/components/ui/Chip.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    let selected = $state("");
    let layers = $derived(dependencyLayers(app.selectedProjects));
    let project = $derived(
        app.workspace?.config.projects.find(
            (project) => project.name === selected,
        ),
    );
    let dependents = $derived(
        app.workspace?.config.projects.filter((project) =>
            project.depends_on.includes(selected),
        ) ?? [],
    );
</script>

<PageHeader
    title="Dependency map"
    description="Read from left to right: foundations first, then the projects that depend on them. Select a project to inspect its relationships."
/>
<ScopeBar />
{#if layers.length}
    <section class="panel overflow-hidden">
        <div class="panel-heading">
            <h2 class="text-title-small">Project layers</h2>
            <div
                class="flex items-center gap-2 text-caption text-text-tertiary"
            >
                Dependencies <Icon name="arrow-right" size={16} /> Dependents
            </div>
        </div>
        <div class="flex gap-5 overflow-x-auto p-5">
            {#each layers as layer, index}
                <div class="min-w-60 flex-1">
                    <div class="mb-4 flex items-center justify-between">
                        <span class="eyebrow"
                            >{index === 0
                                ? "Foundations"
                                : `Layer ${index + 1}`}</span
                        ><span class="text-caption text-text-tertiary"
                            >{layer.length}</span
                        >
                    </div>
                    <div class="space-y-3">
                        {#each layer as node}
                            <button
                                class={[
                                    "w-full rounded border p-4 text-left transition-colors",
                                    selected === node.name
                                        ? "border-brand bg-foreground-current"
                                        : "border-border-tertiary bg-foreground-primary hover:bg-foreground-secondary",
                                ]}
                                aria-pressed={selected === node.name}
                                onclick={() => (selected = node.name)}
                            >
                                <div class="flex items-start gap-2">
                                    <Icon
                                        name="code-branch"
                                        size={16}
                                        class="mt-0.5 text-brand"
                                    /><span class="break-all text-label-medium"
                                        >{node.name}</span
                                    >
                                </div>
                                <p class="mt-2 text-caption text-text-tertiary">
                                    {node.sln_group || "Ungrouped"}
                                </p>
                                {#if node.depends_on.length}<div
                                        class="mt-3 border-t border-border-tertiary pt-3 text-caption leading-relaxed text-text-secondary"
                                    >
                                        Depends on {node.depends_on.join(", ")}
                                    </div>{/if}
                            </button>
                        {/each}
                    </div>
                </div>
            {/each}
        </div>
    </section>
    {#if project}
        <section class="panel mt-5">
            <div class="panel-heading">
                <h2 class="text-title-small">{project.name}</h2>
                <Button
                    scale="s"
                    kind="neutral"
                    appearance="transparent"
                    onclick={() => (selected = "")}>Clear selection</Button
                >
            </div>
            <div class="grid grid-cols-2 gap-6 p-5">
                <div>
                    <h3 class="eyebrow mb-3">Direct dependencies</h3>
                    <div class="flex flex-wrap gap-2">
                        {#each project.depends_on as name}<Chip
                                label={name}
                                scale="s"
                                onclick={() => (selected = name)}
                            />{:else}<p
                                class="text-body-small text-text-secondary"
                            >
                                No dependencies. This is a foundation project.
                            </p>{/each}
                    </div>
                </div>
                <div>
                    <h3 class="eyebrow mb-3">Direct dependents</h3>
                    <div class="flex flex-wrap gap-2">
                        {#each dependents as node}<Chip
                                label={node.name}
                                scale="s"
                                tone="blue"
                                onclick={() => (selected = node.name)}
                            />{:else}<p
                                class="text-body-small text-text-secondary"
                            >
                                No projects depend on this one.
                            </p>{/each}
                    </div>
                </div>
            </div>
        </section>
    {/if}
    <p class="mt-4 text-caption leading-relaxed text-text-tertiary">
        Layers show the selected scope. Relationship details include all
        configured projects, including dependencies outside that scope.
    </p>
{:else}
    <EmptyState
        icon="code-branch"
        title="No projects in this range"
        description="Reset the scope or choose connected endpoints to explore the dependency map."
    />
{/if}
