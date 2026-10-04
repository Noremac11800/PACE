import type { MonitorState } from "./monitor";

export interface Project {
    name: string;
    csproj_path: string;
    repo_url: string | null;
    sln_group: string | null;
    depends_on: string[];
}

export interface PaceConfig {
    repodir: string;
    nuget_cache_path: string | null;
    projects: Project[];
    build_props: {
        name: string;
        datatype: "string" | "boolean" | "path";
        default: string | boolean;
    }[];
}

export interface Workspace {
    path: string;
    content: string;
    config: PaceConfig;
    configs: { path: string; name: string }[];
    repoRoot: string;
    version: string;
}

export interface ConfigurationFields extends Pick<
    PaceConfig,
    "repodir" | "nuget_cache_path" | "build_props"
> {
    repoRoot: string;
    nugetCacheRoot: string | null;
}

export type ConfigurationEdit =
    | {
          kind: "build-property";
          index: number | null;
          property: PaceConfig["build_props"][number];
      }
    | { kind: "delete-build-property"; index: number }
    | {
          kind: "paths";
          repodir: string;
          nuget_cache_path: string | null;
      };

export interface RuntimeOptions {
    python: string;
    directory: string;
}
export interface Environment extends RuntimeOptions {
    appVersion: string;
}
export interface Diagnostic {
    name: string;
    available: boolean;
    version: string;
}
export type View =
    | "overview"
    | "repositories"
    | "dependencies"
    | "git"
    | "dotnet"
    | "configuration"
    | "activity"
    | "settings";
export interface Run {
    id: number;
    kind: "git" | "dotnet" | "tool";
    operation: string;
    context: {
        path: string;
        repoRoot: string;
        from: string;
        to: string;
        projects: Project[];
    } | null;
    label: string;
    command: string;
    started: Date;
    duration: number | null;
    code: number | null;
    status: "running" | "succeeded" | "failed";
    output: string;
    truncated: boolean;
    progress: MonitorState;
    repositoryLogs: {
        entries: { projectId: string; text: string }[];
        size: number;
        truncated: boolean;
    };
}
