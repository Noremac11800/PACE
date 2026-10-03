import { parseArguments } from "./commands";
import type { PaceConfig } from "./types";

export const dotnetTasks = [
    {
        value: "build",
        label: "Build",
        description:
            "Compile the selected solution and its project references.",
    },
    {
        value: "test",
        label: "Test",
        description: "Build and run tests in the selected solution.",
    },
    {
        value: "restore",
        label: "Restore",
        description: "Restore NuGet dependencies for the selected solution.",
    },
    {
        value: "pack",
        label: "Pack",
        description: "Build NuGet packages for packable projects.",
    },
    {
        value: "publish",
        label: "Publish",
        description: "Produce deployment output for publishable projects.",
    },
    {
        value: "clean",
        label: "Clean",
        description: "Remove build outputs using MSBuild's Clean target.",
    },
    {
        value: "custom",
        label: "Custom command",
        description: "Forward your own arguments through pacev2 dotnet.",
    },
] as const;

export type DotnetTask = (typeof dotnetTasks)[number]["value"];
export type BuildProperty = PaceConfig["build_props"][number];

export interface DotnetOptions {
    task: DotnetTask;
    configuration: "Debug" | "Release";
    framework: string;
    noRestore: boolean;
    rebuild: boolean;
    summarizeWarnings: boolean;
    additionalArgs: string;
    customArgs: string;
    properties: Record<string, string>;
}

export function defaultDotnetOptions(): DotnetOptions {
    return {
        task: "build",
        configuration: "Debug",
        framework: "",
        noRestore: false,
        rebuild: false,
        summarizeWarnings: false,
        additionalArgs: "",
        customArgs: "build -c Release",
        properties: {},
    };
}

export function supportsFramework(task: DotnetTask): boolean {
    return ["build", "test", "publish", "clean"].includes(task);
}

export function supportsNoRestore(task: DotnetTask): boolean {
    return ["build", "test", "pack", "publish"].includes(task);
}

function propertyArgument(property: BuildProperty, value: string): string {
    if (!/^[A-Za-z_][A-Za-z0-9_.-]*$/.test(property.name)) {
        throw new Error(
            `"${property.name}" is not a valid MSBuild property name.`,
        );
    }
    if (
        property.datatype === "boolean" &&
        value !== "true" &&
        value !== "false"
    ) {
        throw new Error(`${property.name} must be true or false.`);
    }
    // MSBuild parses delimiters inside a single argument, independently of shell quoting.
    const escaped = value
        .replace(/%/g, "%25")
        .replace(/;/g, "%3B")
        .replace(/,/g, "%2C");
    return `-p:${property.name}=${escaped}`;
}

export function dotnetArguments(
    options: DotnetOptions,
    properties: BuildProperty[],
): string[] {
    const prefix = ["dotnet", ...(options.summarizeWarnings ? ["-w"] : [])];
    if (options.task === "custom") {
        const args = parseArguments(options.customArgs);
        if (!args.length)
            throw new Error("Enter a dotnet command or SDK option.");
        return [...prefix, ...args];
    }
    const args: string[] = [options.task];
    if (options.task === "restore") {
        args.push(`-p:Configuration=${options.configuration}`);
    } else {
        args.push("-c", options.configuration);
    }
    if (supportsFramework(options.task) && options.framework.trim()) {
        args.push("-f", options.framework.trim());
    }
    if (supportsNoRestore(options.task) && options.noRestore)
        args.push("--no-restore");
    if (options.task === "build" && options.rebuild) args.push("-t:Rebuild");
    for (const property of properties) {
        if (Object.hasOwn(options.properties, property.name)) {
            args.push(
                propertyArgument(property, options.properties[property.name]),
            );
        }
    }
    return [...prefix, ...args, ...parseArguments(options.additionalArgs)];
}

export function dotnetNeedsConfirmation(options: DotnetOptions): boolean {
    return (
        ["clean", "publish", "custom"].includes(options.task) ||
        (options.task === "build" && options.rebuild) ||
        !!options.additionalArgs.trim()
    );
}
