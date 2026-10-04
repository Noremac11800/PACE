<script lang="ts">
    import type { Project, Run } from "$lib/domain/types";
    import {
        dotnetProjects,
        progressLabels,
        progressTone,
    } from "$lib/domain/runs";
    import Chip from "./ui/Chip.svelte";
    import Spinner from "./ui/Spinner.svelte";
    import Icon from "./ui/Icon.svelte";

    let {
        run,
        projects,
        operation,
    }: { run: Run | null; projects: Project[]; operation: string } = $props();
    let rows = $derived(dotnetProjects(run, projects));
    const labels: Record<string, string> = {
        restore: "Restore",
        compile: "Compile",
        build: "Build",
        publish: "Publish",
        test: "Test",
    };
    let stages = $derived([
        ...new Set([
            "compile",
            "build",
            ...(operation === "publish" || operation === "test"
                ? [operation]
                : []),
            ...rows.flatMap((project) => Object.keys(project.stages)),
        ]),
    ]);
    let observed = $derived(
        rows.filter((project) => Object.keys(project.stages).length),
    );
</script>

<section class="panel overflow-hidden" aria-label="Project progress">
    <div class="px-4 py-3">
        <h2 class="text-title-small">{labels[operation] ?? ".NET"} progress</h2>
        <p class="mt-1 text-caption text-text-secondary" role="status">
            {#if run}
                {rows.filter((project) => project.status === "succeeded")
                    .length} succeeded ·
                {rows.filter((project) => project.status === "failed").length} failed
                ·
                {rows.filter((project) => project.status === "skipped").length} skipped
                {#if rows.some((project) => project.status === "incomplete")}
                    · {rows.filter((project) => project.status === "incomplete")
                        .length} incomplete
                {/if}
            {:else}
                {projects.length} selected projects · ready to run
            {/if}
        </p>
    </div>
    {#if observed.length}
        <div
            class="flex flex-wrap gap-x-5 gap-y-2 border-t border-border-tertiary bg-foreground-secondary px-4 py-3"
        >
            {#each stages.filter( (stage) => observed.some((project) => stage in project.stages) ) as stage}
                <span class="text-caption text-text-secondary"
                    ><strong class="text-text-primary"
                        >{rows.filter(
                            (project) => project.stages[stage] === "succeeded",
                        ).length}</strong
                    >
                    {labels[stage]?.toLowerCase() ?? stage} complete</span
                >
            {/each}
        </div>
    {/if}
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard users need access to the stage matrix.) -->
    <div
        class="max-h-72 overflow-auto"
        role="region"
        aria-label="Project status details"
        tabindex="0"
    >
        <table class="w-full text-left text-caption">
            <thead
                class="sticky top-0 bg-foreground-primary text-text-secondary"
            >
                <tr>
                    <th class="px-4 py-2 font-medium">Project</th>
                    <th class="px-2 py-2 font-medium">Status</th>
                    {#each stages as stage}<th class="px-2 py-2 font-medium"
                            >{labels[stage] ?? stage}</th
                        >{/each}
                </tr>
            </thead>
            <tbody>
                {#each rows as project (project.id)}
                    <tr
                        class="border-t border-border-tertiary"
                        data-project={project.name}
                    >
                        <td class="min-w-32 max-w-48 px-4 py-2 align-middle">
                            <p
                                class="break-all text-label-small"
                                title={project.detail ||
                                    project.path ||
                                    project.name}
                            >
                                {project.name}
                            </p>
                        </td>
                        <td class="px-2 py-2 align-middle">
                            <Chip
                                label={run
                                    ? progressLabels[project.status]
                                    : "Ready"}
                                tone={run
                                    ? progressTone(project.status)
                                    : undefined}
                                scale="s"
                            />
                        </td>
                        {#each stages as stage}
                            {@const status = project.stages[stage]}
                            <td
                                class="px-2 py-2 align-middle"
                                aria-label={`${project.name} ${labels[stage] ?? stage}: ${status ? progressLabels[status] : "Not reported"}`}
                            >
                                {#if status}
                                    <span
                                        class="inline-flex items-center gap-1"
                                        title={`${labels[stage] ?? stage}: ${progressLabels[status]}`}
                                    >
                                        {#if status === "running"}<Spinner
                                                scale="s"
                                            />
                                        {:else}<Icon
                                                name={status === "succeeded"
                                                    ? "check-circle"
                                                    : "exclamation-mark-triangle"}
                                                size={16}
                                                class={status === "succeeded"
                                                    ? "text-brand"
                                                    : status === "failed"
                                                      ? "text-status-danger"
                                                      : "text-status-warning"}
                                            />{/if}
                                        <span class="sr-only"
                                            >{labels[stage] ?? stage}: {progressLabels[
                                                status
                                            ]}</span
                                        >
                                    </span>
                                {:else}<span
                                        class="text-text-tertiary"
                                        title="Not reported">—</span
                                    >{/if}
                            </td>
                        {/each}
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
    <p
        class="border-t border-border-tertiary px-4 py-2 text-caption leading-relaxed text-text-tertiary"
    >
        MSBuild stages, not a percentage or test count. — means not reported.
        {#if run}Final project status is confirmed when the command ends.{/if}
    </p>
</section>
