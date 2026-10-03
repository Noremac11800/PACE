import { expect, test } from "bun:test";
import {
    applyMonitorEvent,
    closeMonitor,
    MonitorOutput,
    newMonitorState,
    parseMonitorEvent,
} from "./monitor";
import { monitoredArgs, scopedArgs } from "./commands";

function event(sequence: number, fields: Record<string, unknown>) {
    return JSON.stringify({
        protocol: "pace.monitor",
        version: 1,
        sequence,
        timestamp: "2026-10-04T00:00:00+00:00",
        command: "dotnet.build",
        ...fields,
    });
}

test("global monitor precedes commands and never becomes a forwarded argument", () => {
    expect(
        scopedArgs(
            "work.toml",
            "",
            "",
            monitoredArgs(["dotnet", "-w", "build"]),
        ),
    ).toEqual(["-C", "work.toml", "--monitor", "dotnet", "-w", "build"]);
    expect(monitoredArgs(["git", "status"])).toEqual([
        "--monitor",
        "git",
        "status",
    ]);
    expect(monitoredArgs(["--print-config"])).toEqual(["--print-config"]);
});

test("incremental JSONL updates state before completion and retains raw stderr", () => {
    const state = newMonitorState();
    let output = "";
    const decoder = new MonitorOutput(
        (text) => (output += text),
        (message) => applyMonitorEvent(state, message),
    );
    decoder.push(event(1, { event: "start" }) + "\n");
    const project = {
        event: "project",
        id: "/a/App.csproj",
        name: "App",
        path: "/a/App.csproj",
        status: "running",
        detail: "Build: succeeded",
        stages: { build: "succeeded" },
    };
    const line = event(2, project);
    decoder.push(line.slice(0, 23));
    expect(state.projects).toHaveLength(0);
    decoder.push(line.slice(23) + "\n");
    expect(state.projects[0].stages.build).toBe("succeeded");
    expect(state.finished).toBe(false);
    decoder.push(event(99, { event: "start" }) + "\n", "stderr");
    decoder.push(
        event(3, {
            event: "log",
            text: "\x1b[31merror\x1b[0m",
            project_id: null,
        }) + "\n",
    );
    decoder.push(event(4, { ...project, status: "succeeded" }) + "\n");
    decoder.push(
        event(5, { event: "finish", status: "succeeded", returncode: 0 }),
    );
    decoder.finish();
    expect(decoder.error).toBeNull();
    expect(state.projects).toHaveLength(1);
    expect(state.projects[0].status).toBe("succeeded");
    expect(state.finished).toBe(true);
    expect(output).toContain('"sequence":99');
    expect(output).toContain("error");
    expect(output).not.toContain('"sequence":1,');
});

test("raw output and unrelated JSON are not mistaken for monitor events", () => {
    expect(parseMonitorEvent('{"message": "ordinary JSON"}')).toBeNull();
    expect(parseMonitorEvent("Build succeeded.")).toBeNull();
});

test("unsupported, malformed, and missing events are visible protocol errors", () => {
    expect(() =>
        parseMonitorEvent(event(1, { version: 2, event: "start" })),
    ).toThrow("Unsupported");
    expect(() =>
        parseMonitorEvent(event(1, { event: "project", stages: [] })),
    ).toThrow("Invalid");
    expect(() => parseMonitorEvent('{"protocol":"pace.monitor",')).toThrow(
        "Invalid JSON",
    );
    let output = "";
    const decoder = new MonitorOutput(
        (text) => (output += text),
        () => {},
    );
    decoder.push(event(2, { event: "start" }) + "\n");
    expect(decoder.error?.message).toContain("lost");
    expect(output).toContain("Monitor error");
    expect(() =>
        parseMonitorEvent(
            event(1, {
                event: "finish",
                status: "succeeded",
                returncode: 7,
            }),
        ),
    ).toThrow("Invalid");
});

test("events must start once and cannot continue after completion", () => {
    const missingStart = new MonitorOutput(
        () => {},
        () => {},
    );
    missingStart.push(
        event(1, { event: "log", text: "oops", project_id: null }) + "\n",
    );
    expect(missingStart.error?.message).toContain("lifecycle");
    const decoder = new MonitorOutput(
        () => {},
        () => {},
    );
    decoder.push(event(1, { event: "start" }) + "\n");
    decoder.push(
        event(2, { event: "finish", status: "succeeded", returncode: 0 }) +
            "\n",
    );
    decoder.push(
        event(3, { event: "log", text: "late", project_id: null }) + "\n",
    );
    expect(decoder.error?.message).toContain("lifecycle");
});

test("an interrupted run marks only unfinished projects and stages incomplete", () => {
    const state = newMonitorState();
    const project = parseMonitorEvent(
        event(1, {
            event: "project",
            id: "app",
            name: "App",
            path: null,
            status: "running",
            detail: "",
            stages: { restore: "succeeded", build: "running" },
        }),
    );
    if (!project) throw new Error("Fixture must be a monitor event");
    applyMonitorEvent(state, project);
    closeMonitor(state);
    expect(state.projects[0].status).toBe("incomplete");
    expect(state.projects[0].stages).toEqual({
        restore: "succeeded",
        build: "incomplete",
    });
});
