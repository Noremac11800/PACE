import { cleanOutput } from "./commands";
import type { ProjectProgress } from "./monitor";
import type { Project, Run } from "./types";

export const OUTPUT_LIMIT = 250_000;

export function commandKind(args: string[], scoped: boolean): Run["kind"] {
    return scoped && (args[0] === "git" || args[0] === "dotnet")
        ? args[0]
        : "tool";
}

export function commandOperation(args: string[]): string {
    return (
        args
            .slice(1)
            .find(
                (argument) =>
                    !["-w", "--summarize-warnings", "--"].includes(argument),
            ) ??
        args[0] ??
        "custom"
    );
}

export function workspaceRuns(
    runs: Run[],
    kind: Run["kind"],
    path: string | undefined,
): Run[] {
    return runs.filter(
        (run) => run.kind === kind && run.context?.path === path,
    );
}

export function appendRepositoryLog(
    run: Run,
    projectId: string,
    text: string,
): void {
    const logs = run.repositoryLogs;
    const entry = cleanOutput(text) + "\n";
    logs.entries.push({ projectId, text: entry });
    logs.size += entry.length;
    while (logs.size > OUTPUT_LIMIT) {
        const first = logs.entries[0];
        const excess = logs.size - OUTPUT_LIMIT;
        if (first.text.length <= excess) {
            logs.size -= first.text.length;
            logs.entries.shift();
        } else {
            first.text = first.text.slice(excess);
            logs.size -= excess;
        }
        logs.truncated = true;
    }
}

export function repositoryOutput(run: Run | null, projectId: string): string {
    return (
        run?.repositoryLogs.entries
            .filter((entry) => entry.projectId === projectId)
            .map((entry) => entry.text)
            .join("") ?? ""
    );
}

export function queuedProject(
    project: Project,
    run: Run | null,
): ProjectProgress {
    return {
        id: `selected:${project.name}`,
        name: project.name,
        path: null,
        status: run && run.status !== "running" ? "incomplete" : "queued",
        detail:
            run && run.status !== "running"
                ? "No project completion was reported."
                : "",
        stages: {},
    };
}

export function dotnetProjects(
    run: Run | null,
    selected: Project[],
): ProjectProgress[] {
    const reported = run?.progress.projects ?? [];
    const rows = selected.map(
        (project) =>
            reported.find((item) => item.name === project.name) ??
            queuedProject(project, run),
    );
    const included = new Set(rows.map((project) => project.id));
    return [
        ...rows,
        ...reported.filter((project) => !included.has(project.id)),
    ];
}

export const progressLabels = {
    queued: "Queued",
    running: "In progress",
    succeeded: "Succeeded",
    failed: "Failed",
    skipped: "Skipped",
    incomplete: "Incomplete",
};

export function progressTone(status: ProjectProgress["status"]) {
    if (status === "succeeded") return "green";
    if (status === "failed") return "red";
    if (status === "skipped" || status === "incomplete") return "yellow";
    return "blue";
}
