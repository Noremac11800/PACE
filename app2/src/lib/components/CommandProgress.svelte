<script lang="ts">
    import type { MonitorState, ProgressStatus } from "$lib/domain/monitor";
    import Chip from "./ui/Chip.svelte";
    import Spinner from "./ui/Spinner.svelte";

    let { progress }: { progress: MonitorState } = $props();
    let stages = $derived([
        ...new Set(
            progress.projects.flatMap((project) => Object.keys(project.stages)),
        ),
    ]);
    const labels: Record<string, string> = {
        restore: "Restore",
        compile: "Compile",
        build: "Build",
        publish: "Publish",
        test: "Test",
    };
    const statuses: Record<ProgressStatus, string> = {
        queued: "Queued",
        running: "In progress",
        succeeded: "Succeeded",
        failed: "Failed",
        skipped: "Skipped",
        incomplete: "Incomplete",
    };
    function tone(status: ProgressStatus) {
        if (status === "succeeded") return "green";
        if (status === "failed") return "red";
        if (status === "skipped" || status === "incomplete") return "yellow";
        return "blue";
    }
</script>

<section class="border-b border-border-tertiary" aria-label="Project progress">
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3">
        <h2 class="text-label-medium">Project progress</h2>
        <span class="text-caption text-text-secondary" role="status">
            {progress.projects.length} projects ·
            {progress.projects.filter(
                (project) => project.status === "succeeded",
            ).length} succeeded ·
            {progress.projects.filter((project) => project.status === "failed")
                .length} failed ·
            {progress.projects.filter((project) => project.status === "skipped")
                .length} skipped
            {#if progress.projects.some((project) => project.status === "incomplete")}
                · {progress.projects.filter(
                    (project) => project.status === "incomplete",
                ).length} incomplete
            {/if}
        </span>
        {#each stages as stage}
            <span class="text-caption text-text-secondary">
                {labels[stage] ?? stage}:
                {progress.projects.filter(
                    (project) => project.stages[stage] === "succeeded",
                ).length} complete
            </span>
        {/each}
    </div>
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (Keyboard users need access to the scrollable project list.) -->
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
                    <th class="px-5 py-2 font-medium">Project</th>
                    <th class="px-3 py-2 font-medium">Status</th>
                    <th class="px-3 py-2 font-medium">Observed stages</th>
                </tr>
            </thead>
            <tbody>
                {#each progress.projects as project (project.id)}
                    <tr
                        class="border-t border-border-tertiary"
                        data-project={project.name}
                    >
                        <td class="max-w-64 px-5 py-3 align-top">
                            <p
                                class="break-words text-label-small"
                                title={project.path ?? project.id}
                            >
                                {project.name}
                            </p>
                            <p
                                class="mt-1 line-clamp-2 break-all text-text-tertiary"
                                title={project.detail}
                            >
                                {project.detail || "Waiting for execution"}
                            </p>
                        </td>
                        <td class="px-3 py-3 align-top">
                            <span class="inline-flex items-center gap-2">
                                {#if project.status === "running"}<Spinner
                                        scale="s"
                                    />{/if}
                                <Chip
                                    label={statuses[project.status]}
                                    tone={tone(project.status)}
                                    scale="s"
                                />
                            </span>
                        </td>
                        <td class="px-3 py-3 align-top">
                            <div class="flex flex-wrap gap-2">
                                {#each Object.entries(project.stages) as [stage, state]}
                                    <Chip
                                        label={`${labels[stage] ?? stage}: ${statuses[state]}`}
                                        tone={tone(state)}
                                        scale="s"
                                    />
                                {:else}
                                    <span class="text-text-tertiary"
                                        >No stages reported</span
                                    >
                                {/each}
                            </div>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
    {#if stages.length}
        <p class="px-5 py-2 text-caption text-text-tertiary">
            Stages reflect MSBuild targets, not a percentage or a test count.
            Projects can run more than once across frameworks; final status is
            confirmed when the command ends.
        </p>
    {/if}
</section>
