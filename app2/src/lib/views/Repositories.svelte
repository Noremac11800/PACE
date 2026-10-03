<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import type { Project } from "$lib/domain/types";
    import PageHeader from "$lib/components/PageHeader.svelte";
    import ScopeBar from "$lib/components/ScopeBar.svelte";
    import EmptyState from "$lib/components/EmptyState.svelte";
    import Input from "$lib/components/ui/Input.svelte";
    import Button from "$lib/components/ui/Button.svelte";
    import Chip from "$lib/components/ui/Chip.svelte";
    import Icon from "$lib/components/ui/Icon.svelte";
    import Dialog from "$lib/components/ui/Dialog.svelte";
    let search = $state("");
    let group = $state("");
    let selected = $state<Project | null>(null);
    let detailOpen = $state(false);
    let groups = $derived([
        ...new Set(
            app.workspace?.config.projects
                .map((project) => project.sln_group)
                .filter((name): name is string => !!name),
        ),
    ]);
    let projects = $derived(
        app.selectedProjects.filter(
            (project) =>
                (!group || project.sln_group === group) &&
                `${project.name} ${project.csproj_path} ${project.sln_group ?? ""}`
                    .toLowerCase()
                    .includes(search.toLowerCase()),
        ),
    );
</script>

<PageHeader
    title="Repositories"
    description="Browse the projects in your active configuration. Search and group filters only affect this view."
>
    {#snippet actions()}<Button
            kind="neutral"
            appearance="outline-fill"
            iconStart="file-code"
            onclick={() => (app.view = "configuration")}
            >Edit configuration</Button
        >{/snippet}
</PageHeader>
<ScopeBar />
<div class="mb-4 flex items-center gap-3">
    <Input
        label="Search repositories"
        variant="general"
        hideLabel
        iconStart="search"
        placeholder="Search repositories..."
        bind:value={search}
        class="max-w-lg flex-1"
    />
    <select
        aria-label="Solution group"
        class="field-select max-w-52"
        bind:value={group}
    >
        <option value="">All solution groups</option>
        {#each groups as name}<option value={name}>{name}</option>{/each}
    </select>
    <span class="ml-auto text-caption text-text-tertiary"
        >{projects.length} results</span
    >
</div>
{#if projects.length}
    <div class="panel overflow-x-auto">
        <table class="w-full">
            <thead class="table-head"
                ><tr
                    ><th class="px-5 py-3">Repository</th><th class="px-5 py-3"
                        >Solution group</th
                    ><th class="px-5 py-3">Dependencies</th><th
                        class="px-5 py-3">Source</th
                    ><th><span class="sr-only">Details</span></th></tr
                ></thead
            >
            <tbody>
                {#each projects as project}
                    <tr class="hover:bg-transparent-hover">
                        <td class="table-cell"
                            ><button
                                class="text-left"
                                onclick={() => {
                                    selected = project;
                                    detailOpen = true;
                                }}
                                ><span
                                    class="text-label-medium text-text-primary hover:text-brand"
                                    >{project.name}</span
                                ><span
                                    class="mt-1.5 block max-w-sm truncate text-caption text-text-tertiary"
                                    title={project.csproj_path}
                                    >{project.csproj_path}</span
                                ></button
                            ></td
                        >
                        <td class="table-cell"
                            >{#if project.sln_group}<Chip
                                    label={project.sln_group}
                                    appearance="none"
                                    scale="s"
                                />{:else}<span class="text-text-tertiary"
                                    >Ungrouped</span
                                >{/if}</td
                        >
                        <td class="table-cell text-text-secondary"
                            >{project.depends_on.length}
                            {project.depends_on.length === 1
                                ? "dependency"
                                : "dependencies"}</td
                        >
                        <td class="table-cell"
                            ><span
                                class={project.repo_url
                                    ? "text-text-secondary"
                                    : "text-text-tertiary"}
                                >{project.repo_url
                                    ? "Git repository"
                                    : "Local project"}</span
                            ></td
                        >
                        <td class="table-cell"
                            ><Button
                                icon="chevron-right"
                                label={`Details for ${project.name}`}
                                scale="s"
                                kind="neutral"
                                appearance="transparent"
                                onclick={() => {
                                    selected = project;
                                    detailOpen = true;
                                }}
                            /></td
                        >
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
{:else}
    <EmptyState
        icon="search"
        title="No matching repositories"
        description="Adjust your search, solution group, or dependency range. You can add repositories in Configuration."
    />
{/if}

<Dialog
    bind:open={detailOpen}
    heading={selected?.name}
    description="Repository details from the active configuration."
    width="wide"
    scrollable
>
    {#if selected}
        <dl class="space-y-5 py-2">
            {#each [{ label: "Project file", value: selected.csproj_path }, { label: "Checkout directory", value: `${app.workspace?.repoRoot}/${selected.name}` }, { label: "Remote URL", value: selected.repo_url || "No remote URL configured" }, { label: "Solution group", value: selected.sln_group || "Ungrouped" }] as item}
                <div>
                    <dt class="eyebrow mb-2">{item.label}</dt>
                    <dd class="break-all leading-relaxed text-text-primary">
                        {item.value}
                    </dd>
                </div>
            {/each}
            <div>
                <dt class="eyebrow mb-2">Depends on</dt>
                <dd class="flex flex-wrap gap-2">
                    {#each selected.depends_on as name}<Chip
                            label={name}
                            scale="s"
                        />{:else}<span>No dependencies</span>{/each}
                </dd>
            </div>
        </dl>
    {/if}
    {#snippet actions()}
        <Button
            kind="neutral"
            appearance="transparent"
            scale="s"
            onclick={() => (detailOpen = false)}>Close</Button
        >
        <Button
            kind="neutral"
            appearance="outline-fill"
            scale="s"
            iconStart="folder-open"
            onclick={() =>
                selected &&
                app.reveal(`${app.workspace?.repoRoot}/${selected.name}`)}
            >Reveal repository</Button
        >
    {/snippet}
</Dialog>
