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
    label: string;
    command: string;
    started: Date;
    duration: number | null;
    code: number | null;
    status: "running" | "succeeded" | "failed";
    output: string;
    truncated: boolean;
}
