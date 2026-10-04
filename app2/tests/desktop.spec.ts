import { expect, test } from "@playwright/test";
import { execFileSync, spawn, spawnSync } from "node:child_process";
import {
    mkdtempSync,
    mkdirSync,
    realpathSync,
    readFileSync,
    rmSync,
    writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { resolve, join } from "node:path";

const python = resolve(
    "../pacev2/.venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);
let directory: string;
let configPath: string;

test.beforeEach(async ({ page }) => {
    directory = mkdtempSync(join(tmpdir(), "pace-ui-"));
    configPath = join(directory, "workspace.toml");
    writeFileSync(
        configPath,
        `# Test workspace\nrepodir = "./repos"\n` +
            [
                ["foundation", "Libraries", []],
                ["services", "Libraries", ["foundation"]],
                ["desktop-client", "Applications", ["services"]],
                ["web-client", "Applications", ["services"]],
            ]
                .map(
                    ([name, group, dependencies]) =>
                        `[[projects]]\nname = "${name}"\ncsproj_path = "${name}/${name}.csproj"\nsln_group = "${group}"\nrepo_url = "https://example.invalid/${name}.git"\ndepends_on = ${JSON.stringify(dependencies)}\n`,
                )
                .join("\n") +
            '\n[[build-props]]\nname = "DemoFeature"\ndatatype = "boolean"\ndefault = false\n' +
            '\n[[build-props]]\nname = "DemoLabel"\ndatatype = "string"\ndefault = ""\n' +
            '\n[[build-props]]\nname = "DemoOutputPath"\ndatatype = "path"\ndefault = ""\n',
    );
    mkdirSync(join(directory, ".pace"));
    writeFileSync(
        join(directory, ".pace/settings.json"),
        JSON.stringify({ lastActiveConfig: configPath }),
    );
    mkdirSync(join(directory, "repos/foundation"), { recursive: true });
    execFileSync("git", [
        "init",
        "--quiet",
        join(directory, "repos/foundation"),
    ]);
    const env = {
        ...process.env,
        HOME: directory,
        USERPROFILE: directory,
        NO_COLOR: "1",
        PYTHONIOENCODING: "utf-8",
        TERM: "dumb",
        DOTNET_CLI_HOME: directory,
        DOTNET_NOLOGO: "1",
        DOTNET_GENERATE_ASPNET_CERTIFICATE: "false",
        DOTNET_CLI_TELEMETRY_OPTOUT: "1",
    };

    // Only the native IPC transport is replaced. Commands use real pacev2.
    await page.exposeFunction(
        "testInvoke",
        async (command: string, payload: Record<string, unknown>) => {
            if (command === "environment")
                return { python, directory, appVersion: "0.1.0" };
            if (command === "bridge") {
                const result = spawnSync(
                    python,
                    [resolve("src-tauri/bridge.py")],
                    {
                        input: JSON.stringify(payload.request),
                        encoding: "utf8",
                        cwd: (payload.options as { directory: string })
                            .directory,
                        env,
                    },
                );
                if (result.error) throw result.error;
                if (result.status !== 0) throw new Error(result.stderr);
                return {
                    data: JSON.parse(result.stdout),
                    warnings: result.stderr,
                };
            }
            if (command === "run_pace") {
                const args = payload.args as string[];
                return new Promise((resolve, reject) => {
                    const child = spawn(
                        python,
                        ["-u", "-m", "pacev2", ...args],
                        {
                            cwd: (payload.options as { directory: string })
                                .directory,
                            env,
                            stdio: ["ignore", "pipe", "pipe"],
                        },
                    );
                    let index = 0;
                    let delivery = Promise.resolve();
                    const send = (stream: string, text: string) => {
                        const message = {
                            channelId: Number(payload.outputId),
                            index: index++,
                            stream,
                            text,
                        };
                        delivery = delivery.then(() =>
                            page.evaluate((message) => {
                                const deliver = Reflect.get(
                                    window,
                                    "deliverTestOutput",
                                ) as (message: unknown) => void;
                                deliver(message);
                            }, message),
                        );
                    };
                    for (const [stream, reader] of [
                        ["stdout", child.stdout],
                        ["stderr", child.stderr],
                    ] as const) {
                        reader.setEncoding("utf8");
                        let pending = "";
                        reader.on("data", (chunk: string) => {
                            const lines = (pending + chunk).split("\n");
                            pending = lines.pop() ?? "";
                            for (const line of lines) send(stream, line);
                        });
                        reader.on("end", () => {
                            if (pending) send(stream, pending);
                        });
                    }
                    child.on("error", reject);
                    child.on("close", (code) => {
                        delivery.then(
                            () => resolve({ code, count: index }),
                            reject,
                        );
                    });
                });
            }
            if (command === "plugin:event|listen") return 1;
            if (command === "plugin:event|unlisten") return null;
            if (
                command === "plugin:dialog|open" &&
                (payload.options as { title?: string }).title ===
                    "Open PACE configuration"
            )
                return configPath;
            if (
                command === "plugin:dialog|open" &&
                (payload.options as { directory?: boolean }).directory
            ) {
                const picked = join(directory, "picked directory");
                mkdirSync(picked, { recursive: true });
                return picked;
            }
            throw new Error(`Unexpected native request: ${command}`);
        },
    );
    await page.addInitScript(() => {
        const callbacks = new Map<number, (message: unknown) => void>();
        let nextId = 0;
        Object.assign(window, {
            isTauri: true,
            deliverTestOutput(message: {
                channelId: number;
                index: number;
                stream: string;
                text: string;
            }) {
                callbacks.get(message.channelId)?.({
                    index: message.index,
                    message: { stream: message.stream, text: message.text },
                });
            },
            __TAURI_INTERNALS__: {
                metadata: { currentWindow: { label: "main" } },
                transformCallback(callback: (message: unknown) => void) {
                    callbacks.set(++nextId, callback);
                    return nextId;
                },
                unregisterCallback(id: number) {
                    callbacks.delete(id);
                },
                async invoke(
                    command: string,
                    payload: Record<string, unknown>,
                ) {
                    const transport = Reflect.get(window, "testInvoke") as (
                        command: string,
                        payload: unknown,
                    ) => Promise<unknown>;
                    const result = await transport(
                        command,
                        JSON.parse(
                            JSON.stringify({
                                ...payload,
                                ...(command === "run_pace"
                                    ? {
                                          outputId: (
                                              payload.output as { id: number }
                                          ).id,
                                      }
                                    : {}),
                            }),
                        ),
                    );
                    if (command === "run_pace") {
                        const { code, count } = result as {
                            code: number;
                            count: number;
                        };
                        const channel = payload.output as { id: number };
                        callbacks.get(channel.id)?.({
                            index: count,
                            end: true,
                        });
                        return code;
                    }
                    return result;
                },
            },
            __TAURI_EVENT_PLUGIN_INTERNALS__: { unregisterListener() {} },
        });
    });
    await page.goto("/");
    await expect(
        page.getByRole("heading", { name: "Workspace overview" }),
    ).toBeVisible();
    await expect(page.getByText("CLI connected")).toBeVisible();
});

test.afterEach(() => {
    // Only the exact fixture directory created by this test is removed.
    rmSync(directory, { recursive: true, force: true });
});

test("desktop navigation, real scope filtering, and persistent light/dark themes", async ({
    page,
}, testInfo) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.getByRole("radio", { name: "Light", exact: true }).click();
    await expect(
        page.getByRole("radio", { name: "Light", exact: true }),
    ).toHaveAttribute("aria-checked", "true");
    const glyph = page
        .getByRole("button", { name: "PACE overview" })
        .locator("img");
    await expect(glyph).toHaveAttribute("src", "/appglyph-dark.svg");
    await expect
        .poll(() =>
            glyph.evaluate((image: HTMLImageElement) => image.naturalWidth),
        )
        .toBe(100);
    await expect(page.locator('link[rel="icon"]')).toHaveAttribute(
        "href",
        /appicon\.svg$/,
    );
    await page.screenshot({
        path: testInfo.outputPath("overview-light.png"),
        animations: "disabled",
    });
    await page.getByRole("radio", { name: "Dark", exact: true }).click();
    await expect(
        page.getByRole("radio", { name: "Dark", exact: true }),
    ).toHaveAttribute("aria-checked", "true");
    await expect(glyph).toHaveAttribute("src", "/appglyph.svg");
    await page.screenshot({
        path: testInfo.outputPath("overview-dark.png"),
        animations: "disabled",
    });
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page
        .getByRole("button", { name: "Repositories", exact: false })
        .first()
        .click();
    await page
        .getByRole("textbox", { name: "Search repositories", exact: true })
        .fill("desktop");
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await page
        .getByRole("textbox", { name: "Search repositories", exact: true })
        .fill("");
    await page
        .getByRole("combobox", { name: "From", exact: true })
        .selectOption("services");
    await page
        .getByRole("combobox", { name: "To", exact: true })
        .selectOption("desktop-client");
    await expect(page.locator("tbody tr")).toHaveCount(2);
    await page
        .getByRole("button", { name: "Dependency map", exact: true })
        .click();
    await expect(
        page.getByRole("heading", { name: "Project layers" }),
    ).toBeVisible();
    await page.screenshot({
        path: testInfo.outputPath("dependencies-dark.png"),
    });
    for (const name of [
        "Git operations",
        ".NET operations",
        "Command history",
        "Configuration",
        "Settings",
    ]) {
        await page.getByRole("button", { name, exact: true }).click();
        await expect(
            page.getByRole("heading", { name, exact: true }),
        ).toBeVisible();
        await page.screenshot({
            path: testInfo.outputPath(
                `${name.toLowerCase().replaceAll(" ", "-")}-dark.png`,
            ),
            animations: "disabled",
        });
    }
    await page.setViewportSize({ width: 960, height: 640 });
    expect(
        await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
    ).toBe(true);
    for (const name of [
        "Overview",
        "Repositories",
        "Git operations",
        ".NET operations",
    ]) {
        await page
            .getByRole("navigation")
            .getByRole("button", { name, exact: false })
            .click();
        expect(
            await page
                .locator("main")
                .evaluate((main) => main.scrollWidth <= main.clientWidth),
        ).toBe(true);
    }
    expect(errors).toEqual([]);
});

test("theme follows system changes and repository details use an accessible dialog", async ({
    page,
}) => {
    await page.getByRole("radio", { name: "System", exact: true }).click();
    await page.emulateMedia({ colorScheme: "dark" });
    await expect
        .poll(() =>
            page
                .locator("body")
                .evaluate((body) => getComputedStyle(body).backgroundColor),
        )
        .toBe("rgb(53, 53, 53)");
    await page.emulateMedia({ colorScheme: "light" });
    await expect
        .poll(() =>
            page
                .locator("body")
                .evaluate((body) => getComputedStyle(body).backgroundColor),
        )
        .toBe("rgb(248, 248, 248)");
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Repositories" })
        .click();
    await page.getByRole("button", { name: "Details for foundation" }).click();
    await expect(page.getByRole("dialog")).toContainText("foundation.csproj");
    await page
        .getByRole("dialog")
        .getByRole("button", { name: "Close", exact: true })
        .click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
});

test("unsaved edits survive navigation and invalid files cannot be saved", async ({
    page,
}) => {
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    const editor = page.getByLabel("TOML configuration source");
    const original = await editor.inputValue();
    await editor.fill(original + "\ninvalid = [");
    await page
        .getByRole("button", { name: "Save changes", exact: true })
        .click();
    await expect(page.getByRole("alert")).toBeVisible();
    expect(readFileSync(configPath, "utf8")).toBe(original);
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await expect(
        page.getByRole("button", { name: "Check status", exact: true }),
    ).toBeDisabled();
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await expect(
        page.getByRole("button", { name: "Build solution", exact: true }),
    ).toBeDisabled();
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    await expect(editor).toHaveValue(original + "\ninvalid = [");
    await page.getByRole("button", { name: "Reload from disk" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page
        .getByRole("button", { name: "Discard changes", exact: true })
        .click();
    await expect(editor).toHaveValue(original);
    await editor.fill(original + "\n# saved through the app\n");
    await page
        .getByRole("button", { name: "Save changes", exact: true })
        .click();
    await expect(
        page.getByText("Configuration saved and loaded."),
    ).toBeVisible();
    expect(readFileSync(configPath, "utf8")).toContain(
        "# saved through the app",
    );
});

test("build properties can be added, edited, and deleted without losing the configuration draft", async ({
    page,
}, testInfo) => {
    const original = readFileSync(configPath, "utf8");
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await page
        .getByText("MSBuild properties (0 enabled)", { exact: true })
        .click();
    await page
        .getByRole("checkbox", { name: "DemoFeature", exact: true })
        .check();
    await page
        .getByRole("checkbox", { name: "DemoLabel", exact: true })
        .check();
    await page.getByLabel("DemoLabel value", { exact: true }).fill("retain me");
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    await page
        .getByRole("tab", { name: "Build properties", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Edit DemoFeature", exact: true })
        .click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Property name").fill("RenamedFeature");
    await dialog.getByLabel("Default value").selectOption("true");
    await dialog
        .getByRole("button", { name: "Apply to draft", exact: true })
        .click();
    await expect(dialog).not.toBeVisible();
    await expect(
        page.getByText("Unsaved changes", { exact: true }),
    ).toBeVisible();
    expect(readFileSync(configPath, "utf8")).toBe(original);

    await page
        .getByRole("button", { name: "Edit DemoOutputPath", exact: true })
        .click();
    await dialog.getByLabel("Property type").selectOption("string");
    await dialog
        .getByLabel("Default value")
        .fill('value with "quotes"; percent%');
    await dialog
        .getByRole("button", { name: "Apply to draft", exact: true })
        .click();
    await expect(
        page.getByRole("cell", {
            name: 'value with "quotes"; percent%',
            exact: true,
        }),
    ).toBeVisible();
    await page
        .getByRole("button", { name: "Add property", exact: true })
        .click();
    await dialog.getByLabel("Property name").fill("DEMOLABEL");
    await dialog
        .getByRole("button", { name: "Apply to draft", exact: true })
        .click();
    await expect(dialog.getByRole("alert")).toContainText("unique");
    await dialog.getByLabel("Property name").fill("ArtifactPath");
    await dialog.getByLabel("Property type").selectOption("path");
    await dialog
        .getByRole("button", {
            name: "Browse for property directory",
            exact: true,
        })
        .click();
    await expect(dialog.getByLabel("Default value")).toHaveValue(
        join(directory, "picked directory"),
    );
    await page.screenshot({
        path: testInfo.outputPath("edit-build-property.png"),
    });
    await dialog
        .getByRole("button", { name: "Apply to draft", exact: true })
        .click();
    await expect(dialog).not.toBeVisible();
    await page
        .getByRole("button", { name: "Delete DemoOutputPath", exact: true })
        .click();
    await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
    await expect(
        page.getByRole("button", { name: "Edit DemoOutputPath", exact: true }),
    ).toBeVisible();
    await page
        .getByRole("button", { name: "Delete DemoOutputPath", exact: true })
        .click();
    await dialog
        .getByRole("button", { name: "Delete property", exact: true })
        .click();
    await expect(
        page.getByRole("button", { name: "Edit DemoOutputPath", exact: true }),
    ).not.toBeVisible();

    await page.getByRole("button", { name: "Overview", exact: true }).click();
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    const source = await page
        .getByLabel("TOML configuration source")
        .inputValue();
    expect(source).toContain("RenamedFeature");
    expect(source).toContain("default = true");
    expect(source).toContain("ArtifactPath");
    expect(source).not.toContain("DemoOutputPath");
    expect(
        source.startsWith(
            original.slice(0, original.indexOf("[[build-props]]")),
        ),
    ).toBe(true);
    await page
        .getByRole("button", { name: "Save changes", exact: true })
        .click();
    await expect(
        page.getByText("Configuration saved and loaded."),
    ).toBeVisible();
    expect(readFileSync(configPath, "utf8")).toBe(source);
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await expect(
        page.getByRole("checkbox", { name: "RenamedFeature", exact: true }),
    ).not.toBeChecked();
    await expect(
        page.getByRole("checkbox", { name: "DemoLabel", exact: true }),
    ).toBeChecked();
    await expect(
        page.getByLabel("DemoLabel value", { exact: true }),
    ).toHaveValue("retain me");
    await page
        .getByRole("checkbox", { name: "RenamedFeature", exact: true })
        .check();
    await expect(page.getByTestId("dotnet-preview")).toContainText(
        "-p:RenamedFeature=true",
    );
    await expect(
        page.getByRole("checkbox", { name: "DemoOutputPath", exact: true }),
    ).toHaveCount(0);
    await expect(
        page.getByRole("checkbox", { name: "ArtifactPath", exact: true }),
    ).toBeVisible();
});

test("workspace path edits preserve source and reconnect the runtime without losing the active config", async ({
    page,
}, testInfo) => {
    const original = readFileSync(configPath, "utf8");
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    await page
        .getByLabel("TOML configuration source")
        .fill(original + "\n# unsaved source note\n");
    await page
        .getByRole("tab", { name: "Workspace paths", exact: true })
        .click();
    await page.getByRole("button", { name: "Edit paths", exact: true }).click();
    const dialog = page.getByRole("dialog");
    await dialog
        .getByRole("textbox", { name: "Repository directory" })
        .fill("./new repos");
    await dialog
        .getByRole("button", {
            name: "Browse for NuGet cache directory",
            exact: true,
        })
        .click();
    await expect(
        dialog.getByLabel("NuGet cache directory (optional)"),
    ).toHaveValue(join(directory, "picked directory"));
    await dialog
        .getByRole("button", { name: "Apply to draft", exact: true })
        .click();
    await expect(dialog).not.toBeVisible();
    await expect(
        page.getByText(join(realpathSync(directory), "new repos"), {
            exact: true,
        }),
    ).toBeVisible();
    await expect(
        page.getByRole("button", {
            name: "Change working directory",
            exact: true,
        }),
    ).toBeDisabled();
    expect(readFileSync(configPath, "utf8")).toBe(original);
    await page
        .getByRole("button", { name: "Save changes", exact: true })
        .click();
    await expect(
        page.getByText("Configuration saved and loaded."),
    ).toBeVisible();
    expect(readFileSync(configPath, "utf8")).toContain("# unsaved source note");
    expect(readFileSync(configPath, "utf8")).toContain(
        'repodir = "./new repos"',
    );
    expect(readFileSync(configPath, "utf8")).toContain("nuget_cache_path");
    await page.getByRole("button", { name: "Edit paths", exact: true }).click();
    await dialog.getByLabel("NuGet cache directory (optional)").fill("");
    await dialog
        .getByRole("button", { name: "Apply to draft", exact: true })
        .click();
    await expect(
        page.getByText("Default NuGet cache", { exact: true }),
    ).toBeVisible();
    await page
        .getByRole("button", { name: "Save changes", exact: true })
        .click();
    await expect(
        page.getByRole("button", { name: "Save changes", exact: true }),
    ).toBeDisabled();
    expect(readFileSync(configPath, "utf8")).not.toContain("nuget_cache_path");

    const runtimeDirectory = join(directory, "runtime directory");
    mkdirSync(runtimeDirectory);
    const saved = readFileSync(configPath, "utf8");
    await page
        .getByRole("button", { name: "Change working directory", exact: true })
        .click();
    await dialog.getByLabel("CLI working directory").fill(runtimeDirectory);
    writeFileSync(configPath, "invalid = [");
    await dialog
        .getByRole("button", { name: "Save & reconnect", exact: true })
        .click();
    await expect(dialog.getByRole("alert")).toBeVisible();
    expect(
        await page.evaluate(() => localStorage.getItem("pace.desktop.runtime")),
    ).toBeNull();
    writeFileSync(configPath, saved);
    await dialog
        .getByRole("button", { name: "Save & reconnect", exact: true })
        .click();
    await expect(dialog).not.toBeVisible();
    await expect(
        page.getByText(join(realpathSync(runtimeDirectory), "new repos"), {
            exact: true,
        }),
    ).toHaveCount(2);
    await expect(page.getByRole("alert")).not.toBeVisible();
    expect(readFileSync(configPath, "utf8")).toBe(saved);
    expect(
        JSON.parse(
            (await page.evaluate(() =>
                localStorage.getItem("pace.desktop.runtime"),
            )) ?? "{}",
        ).directory,
    ).toBe(runtimeDirectory);
    await page.screenshot({ path: testInfo.outputPath("workspace-paths.png") });
    await page.reload();
    await expect(page.getByText("CLI connected")).toBeVisible();
    await page.getByRole("button", { name: "Settings", exact: true }).click();
    await expect(
        page.getByLabel("Working directory", { exact: true }),
    ).toHaveValue(runtimeDirectory);
});

test("structured configuration fields follow source edits and refuse invalid TOML without discarding it", async ({
    page,
}) => {
    const original = readFileSync(configPath, "utf8");
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    const editor = page.getByLabel("TOML configuration source");
    await editor.fill(original + "\ninvalid = [");
    await page
        .getByRole("tab", { name: "Build properties", exact: true })
        .click();
    await expect(page.getByRole("alert")).toContainText(
        "Unable to read the configuration draft",
    );
    await expect(
        page.getByRole("button", { name: "Add property", exact: true }),
    ).not.toBeVisible();
    await page.getByRole("tab", { name: "TOML source", exact: true }).click();
    await expect(editor).toHaveValue(original + "\ninvalid = [");
    const changed = original.replace(
        'name = "DemoLabel"',
        'name = "SourceLabel"',
    );
    await editor.fill(changed);
    await page
        .getByRole("tab", { name: "Build properties", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Edit SourceLabel", exact: true })
        .click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Default value").fill("not applied");
    await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
    await page.getByRole("tab", { name: "TOML source", exact: true }).click();
    await expect(editor).toHaveValue(changed);
    expect(readFileSync(configPath, "utf8")).toBe(original);
});

function createDotnetProjects(): string {
    const result = spawnSync("dotnet", ["--version"], { encoding: "utf8" });
    test.skip(
        !!result.error || result.status !== 0,
        "A .NET SDK is required for dotnet UI tests.",
    );
    const version = result.stdout.trim().split(".");
    const major = Number(version[0]);
    test.skip(
        major < 9 || (major === 9 && Number(version[2].split("-")[0]) < 200),
        ".slnx requires SDK 9.0.200+.",
    );
    const framework = `net${major}.0`;
    const projects = [
        { name: "foundation", dependencies: [] },
        { name: "services", dependencies: ["foundation"] },
        { name: "desktop-client", dependencies: ["services"] },
        { name: "web-client", dependencies: ["services"] },
    ];
    for (const project of projects) {
        const root = join(directory, "repos", project.name, project.name);
        mkdirSync(root, { recursive: true });
        const references = project.dependencies
            .map(
                (dependency) =>
                    `<ProjectReference Include="../../${dependency}/${dependency}/${dependency}.csproj" />`,
            )
            .join("");
        writeFileSync(
            join(root, `${project.name}.csproj`),
            `<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>${framework}</TargetFramework></PropertyGroup><ItemGroup>${references}</ItemGroup></Project>`,
        );
        writeFileSync(
            join(root, "Example.cs"),
            `${["foundation", "services"].includes(project.name) ? "#warning Intentional UI test warning\n" : ""}public class Example { }`,
        );
    }
    return framework;
}

test("dotnet form builds a real solution, summarizes warnings, and retains options", async ({
    page,
}, testInfo) => {
    const framework = createDotnetProjects();
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await page
        .getByRole("combobox", { name: "Build configuration" })
        .selectOption("Release");
    await page
        .getByRole("textbox", {
            name: "Target framework (optional)",
            exact: true,
        })
        .fill(framework);
    await page.getByRole("switch", { name: "Rebuild all outputs" }).click();
    await page
        .getByRole("switch", { name: "Summarize build warnings" })
        .click();
    await page
        .getByText("MSBuild properties (0 enabled)", { exact: true })
        .click();
    await page
        .getByRole("checkbox", { name: "DemoFeature", exact: true })
        .check();
    await page
        .getByRole("combobox", { name: "DemoFeature value" })
        .selectOption("true");
    await page
        .getByRole("checkbox", { name: "DemoLabel", exact: true })
        .check();
    await page
        .getByRole("textbox", { name: "DemoLabel value", exact: true })
        .fill("literal;comma,percent% with spaces");
    await page
        .getByRole("textbox", {
            name: "Additional arguments (optional)",
            exact: true,
        })
        .fill("--nologo --verbosity quiet -m:1");
    const preview = page.getByTestId("dotnet-preview");
    await expect(preview).toContainText(
        `dotnet -w build -c Release -f ${framework} -t:Rebuild`,
    );
    await expect(preview).toContainText("-p:DemoFeature=true");
    await expect(preview).toContainText(
        "literal%3Bcomma%2Cpercent%25 with spaces",
    );
    await page.getByRole("radio", { name: "Light", exact: true }).click();
    await page.screenshot({
        path: testInfo.outputPath("dotnet-light.png"),
        fullPage: true,
        animations: "disabled",
    });
    await page
        .getByRole("button", { name: "Rebuild solution", exact: true })
        .click();
    await page
        .getByRole("dialog")
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible({
        timeout: 60_000,
    });
    await expect(
        page.getByRole("heading", { name: ".NET operations", exact: true }),
    ).toBeVisible();
    await expect(
        page.getByRole("heading", { name: "Command history", exact: true }),
    ).not.toBeVisible();
    const output = page.getByRole("region", { name: "Command output" });
    await expect(output).toContainText("Total warnings: 2");
    await expect(output).toContainText("Warning summary log:");
    const progress = page.getByRole("region", { name: "Project progress" });
    await expect(progress.locator("tbody tr")).toHaveCount(4);
    await expect(progress.locator('[data-project="foundation"]')).toContainText(
        "Build: Succeeded",
    );
    await expect(output).not.toContainText('"protocol": "pace.monitor"');
    await page.screenshot({
        path: testInfo.outputPath("dotnet-progress-light.png"),
        animations: "disabled",
    });
    expect(readFileSync(join(directory, "repos/PACE.slnx"), "utf8")).toContain(
        "desktop-client/desktop-client/desktop-client.csproj",
    );
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await expect(
        page.getByRole("region", { name: "Project progress" }),
    ).not.toBeVisible();
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await expect(
        page.getByRole("switch", { name: "Summarize build warnings" }),
    ).toHaveAttribute("aria-checked", "true");
    await expect(
        page.getByRole("combobox", { name: "Build configuration" }),
    ).toHaveValue("Release");
    await expect(
        page.getByRole("textbox", { name: "DemoLabel value", exact: true }),
    ).toHaveValue("literal;comma,percent% with spaces");
    await page.getByRole("switch", { name: "Skip restore" }).click();
    await page
        .getByRole("combobox", { name: "Dotnet task" })
        .selectOption("restore");
    await expect(preview).toContainText(
        "dotnet -w restore -p:Configuration=Release",
    );
    await expect(preview).not.toContainText("--no-restore");
    await expect(preview).not.toContainText("-f ");
    await expect(preview).not.toContainText("-t:Rebuild");
    await expect(
        progress.getByRole("heading", { name: "Build progress", exact: true }),
    ).toBeVisible();

    await page
        .getByRole("button", { name: "Command history", exact: true })
        .click();
    await page
        .getByRole("combobox", { name: "CLI command" })
        .selectOption("--version");
    await page.getByRole("button", { name: "Run", exact: true }).click();
    await expect(
        page.getByRole("heading", { name: "Command history", exact: true }),
    ).toBeVisible();
    await expect(
        page.getByRole("region", { name: "Command output" }),
    ).toContainText("pacev2 ");
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await expect(
        page.getByRole("region", { name: "Command output" }),
    ).toContainText("Total warnings: 2");
    await expect(
        page.getByRole("combobox", { name: "Dotnet task" }),
    ).toHaveValue("restore");
});

test("dotnet custom commands surface failures, reject malformed quotes, and honor scope", async ({
    page,
}) => {
    createDotnetProjects();
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await page
        .getByRole("combobox", { name: "From", exact: true })
        .selectOption("services");
    await page
        .getByRole("combobox", { name: "To", exact: true })
        .selectOption("desktop-client");
    await expect(page.getByText("2 of 4 repositories")).toBeVisible();
    await page
        .getByRole("combobox", { name: "Dotnet task" })
        .selectOption("custom");
    const input = page.getByRole("textbox", {
        name: "Dotnet arguments",
        exact: true,
    });
    await input.fill('build -p:Message="unfinished');
    await expect(page.getByRole("alert")).toContainText(
        "Close the quoted argument",
    );
    await expect(
        page.getByRole("button", { name: "Run command", exact: true }),
    ).toBeDisabled();
    await input.fill("build -t:NotARealTarget --nologo");
    await expect(page.getByTestId("dotnet-preview")).toContainText(
        "--from services --to desktop-client --monitor dotnet build",
    );
    await page
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    await page
        .getByRole("dialog")
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    await expect(page.getByText("Failed", { exact: true }).first()).toBeVisible(
        {
            timeout: 60_000,
        },
    );
    await expect(
        page.getByRole("heading", { name: ".NET operations", exact: true }),
    ).toBeVisible();
    await expect(
        page.getByRole("region", { name: "Command output" }),
    ).toContainText("NotARealTarget");
    const solution = readFileSync(join(directory, "repos/PACE.slnx"), "utf8");
    expect(solution.match(/<Project /g)).toHaveLength(2);
});

test("dotnet options reset when configurations change outside the dotnet view", async ({
    page,
}) => {
    const alternate = join(directory, ".pace/configs/alternate.toml");
    mkdirSync(join(directory, ".pace/configs"), { recursive: true });
    writeFileSync(alternate, readFileSync(configPath, "utf8"));
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Reload from disk", exact: true })
        .click();
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await page
        .getByRole("combobox", { name: "Build configuration" })
        .selectOption("Release");
    await page
        .getByText("MSBuild properties (0 enabled)", { exact: true })
        .click();
    await page
        .getByRole("checkbox", { name: "DemoLabel", exact: true })
        .check();
    await page
        .getByRole("textbox", { name: "DemoLabel value", exact: true })
        .fill("original-only");
    await page.getByRole("button", { name: "Overview", exact: true }).click();
    const config = page.getByRole("combobox", {
        name: "Configuration",
        exact: true,
    });
    await config.selectOption({ label: "alternate" });
    await expect(config).toHaveValue(/alternate\.toml$/);
    await page.getByRole("button", { name: "Open", exact: true }).click();
    await expect(config).toHaveValue(/workspace\.toml$/);
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await expect(
        page.getByRole("combobox", { name: "Build configuration" }),
    ).toHaveValue("Debug");
    await page
        .getByText("MSBuild properties (0 enabled)", { exact: true })
        .click();
    await expect(
        page.getByRole("checkbox", { name: "DemoLabel", exact: true }),
    ).not.toBeChecked();
    await expect(page.getByTestId("dotnet-preview")).not.toContainText(
        "original-only",
    );
});

test("Git status and a failed custom command report real CLI results", async ({
    page,
}, testInfo) => {
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Check status", exact: true })
        .click();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await expect(
        page.getByRole("heading", { name: "Git operations", exact: true }),
    ).toBeVisible();
    const repositories = page.getByRole("region", {
        name: "Git repository results",
    });
    await expect(
        repositories.locator('[data-project="foundation"]'),
    ).toContainText("Checked");
    await expect(
        page.getByRole("region", { name: "Repository output" }),
    ).toContainText("##");
    await page
        .getByRole("button", { name: "Repository services", exact: true })
        .click();
    await expect(
        page.getByRole("region", { name: "Repository output" }),
    ).toContainText("not cloned");
    await page.screenshot({ path: testInfo.outputPath("command-output.png") });
    await page.getByText("Custom Git command", { exact: true }).click();
    await page.getByLabel("Git arguments").fill("not-a-real-git-command");
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await expect(page.getByLabel("Git arguments")).toHaveValue(
        "not-a-real-git-command",
    );
    await expect(
        page.getByRole("button", { name: "Repository services", exact: true }),
    ).toHaveAttribute("aria-pressed", "true");
    await page
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    await page
        .getByRole("dialog")
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    await expect(
        page.getByText("Failed", { exact: true }).first(),
    ).toBeVisible();
    await expect(
        page.getByRole("region", { name: "Command output" }),
    ).toContainText("not-a-real-git-command");
    await expect(
        page.getByRole("heading", { name: "Git operations", exact: true }),
    ).toBeVisible();
    await page
        .getByRole("combobox", { name: "Recent Git commands" })
        .selectOption({ index: 1 });
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await page
        .getByRole("button", { name: "Repository foundation", exact: true })
        .click();
    await expect(
        page.getByRole("region", { name: "Repository output" }),
    ).toContainText("##");
});

test("project stages update live before a quiet build can finish", async ({
    page,
}, testInfo) => {
    test.setTimeout(60_000);
    createDotnetProjects();
    const acknowledged = join(directory, "ui-observed");
    const waiter = join(directory, "wait-for-ui.py");
    writeFileSync(
        waiter,
        "import sys, time\nfrom pathlib import Path\n" +
            "deadline = time.monotonic() + 30\n" +
            "while not Path(sys.argv[1]).exists():\n" +
            "    if time.monotonic() > deadline: sys.exit(9)\n" +
            "    time.sleep(0.05)\n",
    );
    const project = join(directory, "repos/services/services/services.csproj");
    const command = [python, waiter, acknowledged]
        .map((path) => `&quot;${path.replaceAll("&", "&amp;")}&quot;`)
        .join(" ");
    writeFileSync(
        project,
        readFileSync(project, "utf8").replace(
            "</Project>",
            `<Target Name="WaitForUI" BeforeTargets="CoreCompile"><Exec Command="${command}" /></Target></Project>`,
        ),
    );
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await page
        .getByRole("textbox", {
            name: "Additional arguments (optional)",
            exact: true,
        })
        .fill("--verbosity quiet");
    await page
        .getByRole("button", { name: "Build solution", exact: true })
        .click();
    await page
        .getByRole("dialog")
        .getByRole("button", { name: "Run command", exact: true })
        .click();
    try {
        const progress = page.getByRole("region", { name: "Project progress" });
        await expect(
            progress.locator('[data-project="foundation"]'),
        ).toContainText("Compile: Succeeded", { timeout: 30_000 });
        await expect(page.getByText("Running", { exact: true })).toBeVisible();
        await expect(
            page.getByRole("heading", { name: ".NET operations", exact: true }),
        ).toBeVisible();
        await expect(
            page.getByText("Completed", { exact: true }),
        ).not.toBeVisible();
        await page.screenshot({
            path: testInfo.outputPath("live-project-progress.png"),
        });
        await page.setViewportSize({ width: 960, height: 640 });
        expect(
            await page
                .locator("main")
                .evaluate((main) => main.scrollWidth <= main.clientWidth),
        ).toBe(true);
        await page
            .getByRole("button", { name: "Git operations", exact: true })
            .click();
        await expect(
            page.getByRole("button", { name: "Check status", exact: true }),
        ).toBeDisabled();
        await page
            .getByRole("button", {
                name: ".NET build running · Show",
                exact: true,
            })
            .click();
        await expect(
            page.getByRole("heading", { name: ".NET operations", exact: true }),
        ).toBeVisible();
        await expect(
            page.getByRole("textbox", {
                name: "Additional arguments (optional)",
                exact: true,
            }),
        ).toHaveValue("--verbosity quiet");
        await page
            .getByRole("button", { name: "Overview", exact: true })
            .click();
    } finally {
        writeFileSync(acknowledged, "");
    }
    await expect(
        page.getByRole("button", {
            name: ".NET build running · Show",
            exact: true,
        }),
    ).not.toBeVisible({ timeout: 30_000 });
    await expect(
        page.getByRole("heading", { name: "Workspace overview", exact: true }),
    ).toBeVisible();
    await page
        .getByRole("button", { name: ".NET operations", exact: true })
        .click();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await expect(
        page.getByRole("region", { name: "Project progress" }),
    ).toContainText("4 succeeded");
});

test("Git results retain their run scope and stay isolated by configuration", async ({
    page,
}) => {
    const alternate = join(directory, ".pace/configs/alternate.toml");
    mkdirSync(join(directory, ".pace/configs"), { recursive: true });
    writeFileSync(alternate, readFileSync(configPath, "utf8"));
    await page
        .getByRole("navigation")
        .getByRole("button", { name: "Configuration", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Reload from disk", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Check status", exact: true })
        .click();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await page
        .getByRole("combobox", { name: "To", exact: true })
        .selectOption("foundation");
    await expect(
        page.getByText("1 of 4 repositories", { exact: true }),
    ).toBeVisible();
    await expect(
        page.getByRole("region", { name: "Command status", exact: true }),
    ).toContainText("Run scope: 4 repositories");
    await expect(
        page
            .getByRole("region", { name: "Repository list", exact: true })
            .getByRole("button"),
    ).toHaveCount(4);
    await page
        .getByRole("button", { name: "Check status", exact: true })
        .click();
    await expect(
        page.getByRole("region", { name: "Command status", exact: true }),
    ).toContainText("Run scope: 1 repository");
    await expect(
        page
            .getByRole("region", { name: "Repository list", exact: true })
            .getByRole("button"),
    ).toHaveCount(1);
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();
    await page
        .getByRole("combobox", { name: "Recent Git commands" })
        .selectOption({ index: 1 });
    await expect(
        page
            .getByRole("region", { name: "Repository list", exact: true })
            .getByRole("button"),
    ).toHaveCount(4);

    await page
        .getByRole("combobox", { name: "Configuration", exact: true })
        .selectOption({ label: "alternate" });
    await expect(
        page.getByText("Completed", { exact: true }),
    ).not.toBeVisible();
    await expect(page.getByText("Not checked", { exact: true })).toHaveCount(4);
    await page.getByRole("button", { name: "Open", exact: true }).click();
    await expect(page.getByText("Completed", { exact: true })).toBeVisible();

    await page
        .getByRole("button", { name: "Command history", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Open in Git workspace", exact: true })
        .click();
    await expect(
        page.getByRole("heading", { name: "Git operations", exact: true }),
    ).toBeVisible();
    await page
        .getByRole("button", { name: "Command history", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Clear history", exact: true })
        .click();
    await page
        .getByRole("button", { name: "Git operations", exact: true })
        .click();
    await expect(
        page.getByText("Completed", { exact: true }),
    ).not.toBeVisible();
    await expect(page.getByText("Not checked", { exact: true })).toHaveCount(4);
});
