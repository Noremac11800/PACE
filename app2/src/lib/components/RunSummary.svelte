<script lang="ts">
    import type { Run } from "$lib/domain/types";
    import Chip from "./ui/Chip.svelte";
    import Spinner from "./ui/Spinner.svelte";

    let {
        run,
        runs = [],
        onselect,
    }: {
        run: Run;
        runs?: Run[];
        onselect?: (id: number) => void;
    } = $props();
    let now = $state(Date.now());
    $effect(() => {
        if (run.status !== "running") return;
        now = Date.now();
        const timer = setInterval(() => (now = Date.now()), 1000);
        return () => clearInterval(timer);
    });
    let seconds = $derived(
        Math.max(0, (run.duration ?? now - run.started.getTime()) / 1000),
    );
</script>

<section class="panel overflow-hidden" aria-label="Command status">
    <div class="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div class="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-2">
            <p class="text-label-medium">{run.label}</p>
            <div
                class="flex flex-wrap items-center gap-2 text-caption text-text-secondary"
                role="status"
            >
                {#if run.status === "running"}
                    <Spinner scale="s" /><span>Running</span>
                {:else}
                    <Chip
                        label={run.status === "succeeded"
                            ? "Completed"
                            : "Failed"}
                        tone={run.status === "succeeded" ? "green" : "red"}
                        scale="s"
                    />
                    <span
                        >{run.code === null
                            ? "Process error"
                            : `Exit ${run.code}`}</span
                    >
                {/if}
                <span>{seconds.toFixed(0)}s</span>
                <span
                    >{run.started.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                    })}</span
                >
            </div>
        </div>
        {#if runs.length > 1 && onselect}
            <select
                class="field-select max-w-52 text-caption"
                aria-label={`Recent ${run.kind === "dotnet" ? ".NET" : "Git"} commands`}
                value={run.id}
                disabled={runs.some((item) => item.status === "running")}
                onchange={(event) =>
                    onselect?.(Number(event.currentTarget.value))}
            >
                {#each runs as item}
                    <option value={item.id}
                        >{item.label} · {item.started.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                        })} · {item.status}</option
                    >
                {/each}
            </select>
        {/if}
    </div>
    {#if run.context}
        <p
            class="border-t border-border-tertiary px-4 py-2 text-caption text-text-secondary"
        >
            Run scope: {run.context.projects.length}
            {run.context.projects.length === 1 ? "repository" : "repositories"} ·
            {run.context.from || "Any start"} → {run.context.to || "Any end"}
        </p>
    {/if}
    <details class="border-t border-border-tertiary bg-foreground-secondary">
        <summary
            class="cursor-pointer px-4 py-2 text-caption text-text-secondary"
            >Executed command</summary
        >
        <code
            class="block whitespace-pre-wrap break-all px-4 pb-3 text-caption leading-relaxed"
            >{run.command}</code
        >
        {#if run.context}
            <p
                class="break-all px-4 pb-3 text-caption leading-relaxed text-text-tertiary"
            >
                Configuration: {run.context.path}<br />Repositories: {run
                    .context.repoRoot}
            </p>
        {/if}
    </details>
</section>
