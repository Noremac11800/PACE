import { expect, test } from "bun:test";
import { newMonitorState } from "./monitor";
import {
    appendRepositoryLog,
    commandKind,
    commandOperation,
    dotnetProjects,
    OUTPUT_LIMIT,
    repositoryOutput,
    workspaceRuns,
} from "./runs";
import type { Project, Run } from "./types";

const project: Project = {
    name: "app",
    csproj_path: "App.csproj",
    sln_group: "Apps",
    repo_url: null,
    depends_on: [],
};
function run(overrides: Partial<Run> = {}): Run {
    return {
        id: 1,
        kind: "git",
        operation: "status",
        label: "Check status",
        command: "pacev2 --monitor git status",
        context: {
            path: "/workspace.toml",
            repoRoot: "/repos",
            from: "",
            to: "",
            projects: [project],
        },
        started: new Date(),
        duration: null,
        code: null,
        status: "running",
        output: "",
        truncated: false,
        progress: newMonitorState(),
        repositoryLogs: { entries: [], size: 0, truncated: false },
        ...overrides,
    };
}

test("workspace commands and diagnostics have independent ownership", () => {
    expect(commandKind(["git", "status"], true)).toBe("git");
    expect(commandKind(["dotnet", "-w", "build"], true)).toBe("dotnet");
    expect(commandKind(["dotnet", "--info"], false)).toBe("tool");
    expect(commandKind(["--print-config"], true)).toBe("tool");
    expect(commandOperation(["dotnet", "-w", "test"])).toBe("test");
    expect(
        commandOperation(["dotnet", "--summarize-warnings", "publish"]),
    ).toBe("publish");
    expect(commandOperation([])).toBe("custom");
    expect(commandOperation(["dotnet", "-w", "--", "build"])).toBe("build");
});

test("operation history is isolated by kind and configuration, not the next scope", () => {
    const git = run();
    const build = run({ id: 2, kind: "dotnet" });
    const differentWorkspace = run({
        id: 3,
        context: { ...git.context!, path: "/other.toml" },
    });
    const tool = run({ id: 4, kind: "tool", context: null });
    expect(
        workspaceRuns(
            [tool, build, differentWorkspace, git],
            "git",
            "/workspace.toml",
        ),
    ).toEqual([git]);
    expect(workspaceRuns([git, build], "dotnet", "/workspace.toml")).toEqual([
        build,
    ]);
    expect(workspaceRuns([git], "git", undefined)).toEqual([]);
});

test("repository output uses monitor IDs, not guesses from terminal text", () => {
    const current = run();
    appendRepositoryLog(current, "app", "\x1b[32m## main\x1b[0m\n M App.cs");
    appendRepositoryLog(current, "base", "Warning: not cloned");
    appendRepositoryLog(current, "__proto__", "literal repository name");
    expect(repositoryOutput(current, "app")).toBe("## main\n M App.cs\n");
    expect(repositoryOutput(current, "base")).toBe("Warning: not cloned\n");
    expect(repositoryOutput(current, "__proto__")).toBe(
        "literal repository name\n",
    );
    expect(repositoryOutput(current, "missing")).toBe("");
});

test("per-repository logs share a bounded buffer and retain recent failures", () => {
    const current = run();
    appendRepositoryLog(current, "app", "a".repeat(OUTPUT_LIMIT + 50));
    appendRepositoryLog(current, "base", "fatal: test failure");
    expect(current.repositoryLogs.size).toBe(OUTPUT_LIMIT);
    expect(
        current.repositoryLogs.entries.reduce(
            (size, entry) => size + entry.text.length,
            0,
        ),
    ).toBe(OUTPUT_LIMIT);
    expect(current.repositoryLogs.truncated).toBe(true);
    expect(repositoryOutput(current, "base")).toContain("fatal: test failure");
});

test("project matrix keeps queued members, adds discovered references, and exposes missing results", () => {
    const current = run({ kind: "dotnet" });
    current.progress.projects.push({
        id: "/refs/Base.csproj",
        name: "base",
        path: "/refs/Base.csproj",
        status: "running",
        detail: "Compiling",
        stages: { compile: "running" },
    });
    const rows = dotnetProjects(current, [project]);
    expect(rows.map((row) => row.name)).toEqual(["app", "base"]);
    expect(rows[0].status).toBe("queued");
    current.status = "failed";
    expect(dotnetProjects(current, [project])[0].status).toBe("incomplete");
    expect(dotnetProjects(current, [project])[1].stages.compile).toBe(
        "running",
    );
});
