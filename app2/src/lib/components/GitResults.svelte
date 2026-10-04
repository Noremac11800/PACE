<script lang="ts">
    import type { Project, Run } from "$lib/domain/types";
    import {
        progressLabels,
        progressTone,
        queuedProject,
        repositoryOutput,
    } from "$lib/domain/runs";
    import { app } from "$lib/state/app.svelte";
    import { gitForm } from "$lib/state/git.svelte";
    import CommandLog from "./CommandLog.svelte";
    import Chip from "./ui/Chip.svelte";
    import Button from "./ui/Button.svelte";
    import Icon from "./ui/Icon.svelte";
    import Spinner from "./ui/Spinner.svelte";

    let {
        run,
        projects,
        repoRoot,
    }: { run: Run | null; projects: Project[]; repoRoot: string } = $props();
    let groups = $derived([
        ...new Set(projects.map((project) => project.sln_group || "Ungrouped")),
    ]);
    let selected = $derived(
        projects.find(
            (project) => project.name === gitForm.selectedRepository,
        ) ?? projects[0],
    );
    let reported = $derived(
        new Map(
            run?.progress.projects.map((project) => [project.name, project]) ??
                [],
        ),
    );
    let text = $derived(selected ? repositoryOutput(run, selected.name) : "");
    const completedLabels: Record<string, string> = {
        status: "Checked",
        clone: "Cloned",
        pull: "Updated",
    };
    function label(project: Project) {
        if (!run) return "Not checked";
        const status =
            reported.get(project.name)?.status ??
            queuedProject(project, run).status;
        if (status === "succeeded")
            return completedLabels[run.operation] ?? "Succeeded";
        return progressLabels[status];
    }
</script>

<section class="panel overflow-hidden" aria-label="Git repository results">
    <div class="panel-heading">
        <h2 class="text-title-small">Repositories</h2>
        <span class="text-caption text-text-secondary"
            >{projects.length} in {run ? "run" : "selected"} scope</span
        >
    </div>
    <div
        class="grid min-h-80 grid-cols-[minmax(220px,0.85fr)_minmax(0,1.15fr)]"
    >
        <!-- svelte-ignore a11y_no_noninteractive_tabindex (Grouped repository results can be scrolled with the keyboard.) -->
        <div
            class="max-h-[480px] overflow-y-auto border-r border-border-tertiary"
            tabindex="0"
            role="region"
            aria-label="Repository list"
        >
            {#each groups as group}
                <details open>
                    <summary
                        class="cursor-pointer bg-foreground-secondary px-4 py-2 text-label-small"
                        >{group}</summary
                    >
                    {#each projects.filter((project) => (project.sln_group || "Ungrouped") === group) as project (project.name)}
                        {@const progress =
                            reported.get(project.name) ??
                            queuedProject(project, run)}
                        <button
                            class={[
                                "w-full border-t border-border-tertiary px-4 py-3 text-left",
                                selected?.name === project.name
                                    ? "bg-foreground-current"
                                    : "hover:bg-transparent-hover",
                            ]}
                            aria-label={`Repository ${project.name}`}
                            aria-pressed={selected?.name === project.name}
                            data-project={project.name}
                            onclick={() =>
                                (gitForm.selectedRepository = project.name)}
                        >
                            <span
                                class="flex flex-wrap items-center justify-between gap-2"
                            >
                                <span
                                    class="flex min-w-0 items-center gap-2 text-label-small"
                                >
                                    {#if run && progress.status === "running"}<Spinner
                                            scale="s"
                                        />{:else}<Icon
                                            name="code-branch"
                                            size={16}
                                        />{/if}
                                    <span class="break-all">{project.name}</span
                                    >
                                </span>
                                <Chip
                                    label={label(project)}
                                    tone={run
                                        ? progressTone(progress.status)
                                        : undefined}
                                    scale="s"
                                />
                            </span>
                            <span
                                class="mt-1 block truncate text-caption text-text-secondary"
                                >{progress.detail ||
                                    (project.repo_url
                                        ? "Ready for a Git command"
                                        : "No remote configured")}</span
                            >
                        </button>
                    {/each}
                </details>
            {:else}
                <p class="p-5 text-body-small text-text-secondary">
                    No repositories in this scope.
                </p>
            {/each}
        </div>
        <div class="min-w-0">
            {#if selected}
                <div class="flex items-start justify-between gap-3 px-4 py-3">
                    <div class="min-w-0">
                        <h3 class="break-all text-label-medium">
                            {selected.name}
                        </h3>
                        <p
                            class="mt-1 break-all text-caption text-text-tertiary"
                        >
                            {selected.repo_url || "No remote configured"}
                        </p>
                    </div>
                    <Button
                        kind="neutral"
                        appearance="transparent"
                        scale="s"
                        icon="folder-open"
                        label={`Open ${selected.name} folder`}
                        onclick={() =>
                            app.reveal(`${repoRoot}/${selected.name}`)}
                    />
                </div>
                {#key `${run?.id ?? "idle"}:${selected.name}`}
                    <CommandLog
                        {text}
                        title="Repository output"
                        running={run?.status === "running"}
                        truncated={run?.repositoryLogs.truncated}
                        empty={run
                            ? reported.get(selected.name)?.detail ||
                              "No output was reported for this repository."
                            : "Check status, clone, or pull to see this repository's output here."}
                    />
                {/key}
            {:else}
                <p class="p-5 text-body-small text-text-secondary">
                    Choose a repository scope to get started.
                </p>
            {/if}
        </div>
    </div>
</section>
