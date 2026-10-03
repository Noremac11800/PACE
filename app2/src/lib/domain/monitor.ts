import { cleanOutput } from "./commands";

export type ProgressStatus =
    "queued" | "running" | "succeeded" | "failed" | "skipped" | "incomplete";

export interface ProjectProgress {
    id: string;
    name: string;
    path: string | null;
    status: ProgressStatus;
    detail: string;
    stages: Record<string, ProgressStatus>;
}

interface Envelope {
    protocol: "pace.monitor";
    version: 1;
    sequence: number;
    command: string;
    timestamp: string;
}

export type MonitorEvent = Envelope &
    (
        | { event: "start" }
        | ({ event: "project" } & ProjectProgress)
        | { event: "log"; text: string; project_id: string | null }
        | {
              event: "finish";
              status: "succeeded" | "failed";
              returncode: number;
          }
    );

export interface MonitorState {
    active: boolean;
    finished: boolean;
    returncode: number | null;
    projects: ProjectProgress[];
}

export function newMonitorState(): MonitorState {
    return { active: false, finished: false, returncode: null, projects: [] };
}

function record(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}

function status(value: unknown): value is ProgressStatus {
    return (
        value === "queued" ||
        value === "running" ||
        value === "succeeded" ||
        value === "failed" ||
        value === "skipped" ||
        value === "incomplete"
    );
}

export function parseMonitorEvent(line: string): MonitorEvent | null {
    let value: unknown;
    try {
        value = JSON.parse(line);
    } catch (error) {
        if (line.includes('"pace.monitor"'))
            throw new Error("Invalid JSON in pacev2 monitor output.", {
                cause: error,
            });
        return null;
    }
    if (!record(value) || value.protocol !== "pace.monitor") return null;
    if (value.version !== 1)
        throw new Error(
            `Unsupported pacev2 monitor version: ${value.version}. Update PACE Desktop.`,
        );
    if (
        !Number.isInteger(value.sequence) ||
        typeof value.sequence !== "number" ||
        value.sequence < 1 ||
        typeof value.command !== "string" ||
        typeof value.timestamp !== "string"
    )
        throw new Error("Invalid pacev2 monitor event envelope.");
    const envelope: Envelope = {
        protocol: "pace.monitor",
        version: 1,
        sequence: value.sequence,
        command: value.command,
        timestamp: value.timestamp,
    };
    if (value.event === "start") return { ...envelope, event: "start" };
    if (
        value.event === "log" &&
        typeof value.text === "string" &&
        (value.project_id === null || typeof value.project_id === "string")
    )
        return {
            ...envelope,
            event: "log",
            text: value.text,
            project_id: value.project_id,
        };
    if (
        value.event === "project" &&
        typeof value.id === "string" &&
        typeof value.name === "string" &&
        (value.path === null || typeof value.path === "string") &&
        status(value.status) &&
        typeof value.detail === "string" &&
        record(value.stages)
    ) {
        const stages: [string, ProgressStatus][] = [];
        for (const [stage, state] of Object.entries(value.stages)) {
            if (!status(state))
                throw new Error("Invalid pacev2 monitor stage status.");
            stages.push([stage, state]);
        }
        return {
            ...envelope,
            event: "project",
            id: value.id,
            name: value.name,
            path: value.path,
            status: value.status,
            detail: value.detail,
            stages: Object.fromEntries(stages),
        };
    }
    if (
        value.event === "finish" &&
        (value.status === "succeeded" || value.status === "failed") &&
        typeof value.returncode === "number" &&
        Number.isInteger(value.returncode) &&
        value.returncode >= 0 &&
        (value.status === "succeeded") === (value.returncode === 0)
    )
        return {
            ...envelope,
            event: "finish",
            status: value.status,
            returncode: value.returncode,
        };
    throw new Error(
        `Invalid or unsupported pacev2 monitor event: ${String(value.event)}.`,
    );
}

export function applyMonitorEvent(
    state: MonitorState,
    event: MonitorEvent,
): void {
    if (event.event === "start") state.active = true;
    if (event.event === "project") {
        const project: ProjectProgress = {
            id: event.id,
            name: event.name,
            path: event.path,
            status: event.status,
            detail: cleanOutput(event.detail),
            stages: event.stages,
        };
        const index = state.projects.findIndex((item) => item.id === event.id);
        if (index === -1) state.projects.push(project);
        else state.projects[index] = project;
    }
    if (event.event === "finish") {
        state.finished = true;
        state.returncode = event.returncode;
    }
}

export function closeMonitor(state: MonitorState): void {
    for (const project of state.projects) {
        if (project.status === "running" || project.status === "queued") {
            project.status = "incomplete";
            project.detail =
                "Process ended without a project completion event.";
        }
        for (const [stage, value] of Object.entries(project.stages))
            if (value === "running") project.stages[stage] = "incomplete";
    }
}

/** Native stdout is line based; buffering also supports transports delivering chunks. */
export class MonitorOutput {
    private pending = "";
    private sequence = 0;
    private ended = false;
    error: Error | null = null;

    constructor(
        private onOutput: (text: string) => void,
        private onEvent: (event: MonitorEvent) => void,
    ) {}

    push(text: string, stream = "stdout") {
        if (stream !== "stdout") {
            this.onOutput(text);
            return;
        }
        const lines = (this.pending + text).split("\n");
        this.pending = lines.pop() ?? "";
        for (const line of lines) this.line(line);
    }

    finish() {
        if (this.pending) this.line(this.pending);
        this.pending = "";
    }

    private line(line: string) {
        try {
            const event = parseMonitorEvent(line);
            if (!event) {
                this.onOutput(line + "\n");
                return;
            }
            if (event.sequence !== this.sequence + 1)
                throw new Error(
                    "pacev2 monitor events were lost or received out of order.",
                );
            if (
                this.ended ||
                (event.event === "start") !== (this.sequence === 0)
            )
                throw new Error(
                    "Invalid pacev2 monitor start/finish lifecycle.",
                );
            this.sequence = event.sequence;
            this.ended = event.event === "finish";
            if (event.event === "log")
                this.onOutput(
                    (event.project_id ? `[${event.project_id}] ` : "") +
                        event.text +
                        "\n",
                );
            this.onEvent(event);
        } catch (error) {
            this.error =
                error instanceof Error ? error : new Error(String(error));
            this.onOutput(`Monitor error: ${this.error.message}\n${line}\n`);
        }
    }
}
