import * as api from "$lib/services/desktop";
import { dotnetForm } from "./dotnet.svelte";
import { defaultDotnetOptions } from "$lib/domain/dotnet";
import { cleanOutput, commandPreview, scopedArgs } from "$lib/domain/commands";
import type {
    Diagnostic,
    PaceConfig,
    Run,
    RuntimeOptions,
    View,
    Workspace,
} from "$lib/domain/types";

const SETTINGS_KEY = "pace.desktop.runtime";
const OUTPUT_LIMIT = 250_000;

class App {
    view = $state<View>("overview");
    workspace = $state<Workspace | null>(null);
    draft = $state("");
    options = $state<RuntimeOptions>({ python: "", directory: "" });
    appVersion = $state("0.1.0");
    busy = $state(false);
    initialized = $state(false);
    from = $state("");
    to = $state("");
    selectedNames = $state<string[]>([]);
    filtering = $state(false);
    runs = $state<Run[]>([]);
    selectedRunId = $state<number | null>(null);
    diagnostics = $state<Diagnostic[]>([]);
    notice = $state<{
        tone: "error" | "success" | "info";
        text: string;
    } | null>(null);
    confirmation = $state<{
        heading: string;
        description: string;
        accept: string;
    } | null>(null);
    private resolveConfirmation: ((accepted: boolean) => void) | null = null;
    private filterGeneration = 0;

    get dirty() {
        return !!this.workspace && this.draft !== this.workspace.content;
    }
    get running() {
        return this.runs.some((run) => run.status === "running");
    }
    get locked() {
        return this.busy || this.running;
    }
    get selectedProjects() {
        return (
            this.workspace?.config.projects.filter((project) =>
                this.selectedNames.includes(project.name),
            ) ?? []
        );
    }
    get selectedRun() {
        return this.runs.find((run) => run.id === this.selectedRunId) ?? null;
    }
    get name() {
        return (
            this.workspace?.path
                .split(/[/\\]/)
                .pop()
                ?.replace(/\.toml$/i, "") ?? "No configuration"
        );
    }

    notify(text: string, tone: "error" | "success" | "info" = "error") {
        this.notice = { text, tone };
    }
    error(error: unknown) {
        this.notify(error instanceof Error ? error.message : String(error));
    }

    confirm(
        heading: string,
        description: string,
        accept = "Continue",
    ): Promise<boolean> {
        this.confirmation = { heading, description, accept };
        return new Promise((resolve) => {
            this.resolveConfirmation = resolve;
        });
    }

    answer(accepted: boolean) {
        this.resolveConfirmation?.(accepted);
        this.resolveConfirmation = null;
        this.confirmation = null;
    }

    async call<T>(request: Record<string, unknown>) {
        const result = await api.request<T>(
            $state.snapshot(this.options),
            request,
        );
        if (result.warnings) this.notify(result.warnings, "info");
        return result.data;
    }

    private apply(workspace: Workspace) {
        if (dotnetForm.configPath !== workspace.path) {
            dotnetForm.configPath = workspace.path;
            dotnetForm.options = defaultDotnetOptions();
        }
        this.filterGeneration++;
        this.workspace = workspace;
        this.draft = workspace.content;
        this.from = "";
        this.to = "";
        this.filtering = false;
        this.selectedNames = workspace.config.projects.map(
            (project) => project.name,
        );
    }

    async initialize() {
        if (!api.desktop) {
            this.initialized = true;
            return;
        }
        try {
            const defaults = await api.environment();
            this.appVersion = defaults.appVersion;
            this.options = {
                python: defaults.python,
                directory: defaults.directory,
            };
            const saved = localStorage.getItem(SETTINGS_KEY);
            if (saved) {
                const parsed: unknown = JSON.parse(saved);
                if (
                    !parsed ||
                    typeof parsed !== "object" ||
                    !("python" in parsed) ||
                    !("directory" in parsed) ||
                    typeof parsed.python !== "string" ||
                    typeof parsed.directory !== "string"
                ) {
                    throw new Error(
                        "Saved runtime settings are invalid. Choose a Python executable in Settings.",
                    );
                }
                this.options = {
                    python: parsed.python,
                    directory: parsed.directory,
                };
            }
            await this.load();
        } catch (error) {
            this.error(error);
        } finally {
            this.initialized = true;
        }
    }

    async canReplace() {
        return (
            !this.dirty ||
            (await this.confirm(
                "Discard unsaved changes?",
                "Your configuration has unsaved edits. Continuing will discard those edits.",
                "Discard changes",
            ))
        );
    }

    async load(path?: string) {
        if (this.locked || !(await this.canReplace())) return;
        this.busy = true;
        this.notice = null;
        try {
            this.apply(
                await this.call<Workspace>({
                    action: "workspace",
                    ...(path ? { path } : {}),
                }),
            );
        } catch (error) {
            this.error(error);
        } finally {
            this.busy = false;
        }
    }

    async open() {
        try {
            const path = await api.chooseConfig();
            if (path) await this.load(path);
        } catch (error) {
            this.error(error);
        }
    }

    async save(copy = false, content = this.draft) {
        if (this.locked) return;
        this.busy = true;
        this.notice = null;
        try {
            const path = copy
                ? await api.chooseSavePath()
                : this.workspace?.path;
            if (!path) return;
            this.apply(
                await this.call<Workspace>({
                    action: "save",
                    path,
                    content,
                    expected: copy ? null : this.workspace?.content,
                }),
            );
            if (!this.notice)
                this.notify("Configuration saved and loaded.", "success");
        } catch (error) {
            this.error(error);
        } finally {
            this.busy = false;
        }
    }

    async create() {
        if (!(await this.canReplace())) return;
        await this.save(
            true,
            '# PACE workspace\nrepodir = "./repositories"\nprojects = []\n',
        );
    }

    async validate() {
        this.busy = true;
        this.notice = null;
        try {
            await this.call<PaceConfig>({
                action: "validate",
                content: this.draft,
            });
            this.notify(
                "Valid pacev2 configuration. No files were changed.",
                "success",
            );
        } catch (error) {
            this.error(error);
        } finally {
            this.busy = false;
        }
    }

    async setRange(from: string, to: string) {
        if (!this.workspace) return;
        this.from = from;
        this.to = to;
        this.filtering = true;
        this.selectedNames = [];
        const generation = ++this.filterGeneration;
        try {
            const names = await this.call<string[]>({
                action: "filter",
                config: $state.snapshot(this.workspace.config),
                from: from || null,
                to: to || null,
            });
            if (generation === this.filterGeneration)
                this.selectedNames = names;
        } catch (error) {
            if (generation === this.filterGeneration) this.error(error);
        } finally {
            if (generation === this.filterGeneration) this.filtering = false;
        }
    }

    async run(args: string[], label: string, scoped = true) {
        if (this.locked || this.filtering) return;
        if (scoped && !this.workspace) {
            this.notify(
                "Open a configuration before running workspace commands.",
            );
            return;
        }
        if (scoped && this.dirty) {
            this.notify(
                "Save or discard configuration edits before running a workspace command.",
            );
            return;
        }
        const allArgs =
            scoped && this.workspace
                ? scopedArgs(this.workspace.path, this.from, this.to, args)
                : args;
        this.notice = null;
        const id = Date.now();
        this.runs.unshift({
            id,
            label,
            command: commandPreview(allArgs),
            started: new Date(),
            duration: null,
            code: null,
            status: "running",
            output: "",
            truncated: false,
        });
        this.runs = this.runs.slice(0, 20);
        this.selectedRunId = id;
        this.view = "activity";
        const run = this.runs[0];
        try {
            if (scoped && this.workspace)
                await this.call({
                    action: "verify",
                    path: this.workspace.path,
                    expected: this.workspace.content,
                });
            run.code = await api.execute(
                $state.snapshot(this.options),
                allArgs,
                (text) => {
                    const output = run.output + cleanOutput(text);
                    if (output.length > OUTPUT_LIMIT) run.truncated = true;
                    run.output = output.slice(-OUTPUT_LIMIT);
                },
            );
            run.status = run.code === 0 ? "succeeded" : "failed";
            if (run.code !== 0)
                this.notify(
                    `${label} exited with code ${run.code}. Review the command output for details.`,
                );
        } catch (error) {
            run.status = "failed";
            run.output += `\n${error instanceof Error ? error.message : String(error)}\n`;
            this.error(error);
        } finally {
            run.duration = Date.now() - run.started.getTime();
        }
    }

    async connect(options: RuntimeOptions) {
        if (this.locked || !(await this.canReplace())) return;
        this.busy = true;
        this.notice = null;
        try {
            const checked = await api.request<Diagnostic[]>(options, {
                action: "diagnostics",
            });
            this.options = options;
            this.diagnostics = checked.data;
            localStorage.setItem(SETTINGS_KEY, JSON.stringify(options));
            this.workspace = null;
            this.draft = "";
            this.apply(await this.call<Workspace>({ action: "workspace" }));
            if (checked.warnings) this.notify(checked.warnings, "info");
            else if (!this.notice)
                this.notify("Connected to pacev2.", "success");
        } catch (error) {
            this.error(error);
        } finally {
            this.busy = false;
        }
    }

    async checkTools() {
        this.busy = true;
        try {
            this.diagnostics = await this.call<Diagnostic[]>({
                action: "diagnostics",
            });
        } catch (error) {
            this.error(error);
        } finally {
            this.busy = false;
        }
    }

    async reveal(path: string) {
        try {
            await api.reveal(path);
        } catch (error) {
            this.error(error);
        }
    }
}

export const app = new App();
