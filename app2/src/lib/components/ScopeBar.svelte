<script lang="ts">
    import { app } from "$lib/state/app.svelte";
    import Button from "./ui/Button.svelte";
    import Icon from "./ui/Icon.svelte";
</script>

<section
    class="panel mb-6 flex flex-wrap items-center gap-4 p-4"
    aria-label="Repository scope"
>
    <div class="flex items-center gap-2 text-label-medium">
        <Icon name="code-branch" size={16} /> Scope
    </div>
    <label
        class="flex min-w-44 flex-1 items-center gap-3 text-body-small text-text-secondary"
    >
        From
        <select
            class="field-select"
            value={app.from}
            disabled={app.locked}
            onchange={(event) =>
                app.setRange(event.currentTarget.value, app.to)}
        >
            <option value="">Any starting point</option>
            {#each app.workspace?.config.projects ?? [] as project}<option
                    value={project.name}>{project.name}</option
                >{/each}
        </select>
    </label>
    <label
        class="flex min-w-44 flex-1 items-center gap-3 text-body-small text-text-secondary"
    >
        To
        <select
            class="field-select"
            value={app.to}
            disabled={app.locked}
            onchange={(event) =>
                app.setRange(app.from, event.currentTarget.value)}
        >
            <option value="">Any ending point</option>
            {#each app.workspace?.config.projects ?? [] as project}<option
                    value={project.name}>{project.name}</option
                >{/each}
        </select>
    </label>
    <span class="text-caption text-text-secondary" aria-live="polite"
        >{app.filtering
            ? "Resolving..."
            : `${app.selectedNames.length} of ${app.workspace?.config.projects.length ?? 0} repositories`}</span
    >
    {#if app.from || app.to}<Button
            scale="s"
            appearance="transparent"
            kind="neutral"
            disabled={app.locked}
            onclick={() => app.setRange("", "")}>Reset</Button
        >{/if}
</section>
