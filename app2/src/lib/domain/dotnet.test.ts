import { describe, expect, test } from "bun:test";
import {
    defaultDotnetOptions,
    dotnetArguments,
    dotnetNeedsConfirmation,
    retainPropertyOverrides,
    type BuildProperty,
} from "./dotnet";
import { scopedArgs } from "./commands";

const definitions: BuildProperty[] = [
    { name: "DemoFeature", datatype: "boolean", default: false },
    { name: "DemoLabel", datatype: "string", default: "" },
    { name: "OutputPath", datatype: "path", default: "" },
];

describe("dotnet commands", () => {
    test("configuration edits clear changed and removed property overrides only", () => {
        expect(
            retainPropertyOverrides(
                {
                    DemoFeature: "true",
                    DemoLabel: "override",
                    OutputPath: "/build",
                    Removed: "old",
                },
                definitions,
                [
                    { name: "DemoFeature", datatype: "boolean", default: true },
                    definitions[1],
                    { name: "OutputPath", datatype: "string", default: "" },
                ],
            ),
        ).toEqual({ DemoLabel: "override" });
        expect(
            retainPropertyOverrides(
                { DemoFeature: "true" },
                definitions,
                definitions,
            ),
        ).toEqual({ DemoFeature: "true" });
    });
    test("places PACE options, warning summaries, and dotnet options in the correct order", () => {
        const options = {
            ...defaultDotnetOptions(),
            configuration: "Release" as const,
            framework: "net10.0",
            noRestore: true,
            rebuild: true,
            summarizeWarnings: true,
        };
        expect(
            scopedArgs(
                "/configs/a b.toml",
                "core",
                "app",
                dotnetArguments(options, []),
            ),
        ).toEqual([
            "-C",
            "/configs/a b.toml",
            "--from",
            "core",
            "--to",
            "app",
            "dotnet",
            "-w",
            "build",
            "-c",
            "Release",
            "-f",
            "net10.0",
            "--no-restore",
            "-t:Rebuild",
        ]);
    });
    test("uses restore-compatible configuration and never leaks build-only flags", () => {
        const options = {
            ...defaultDotnetOptions(),
            task: "restore" as const,
            framework: "net10.0",
            noRestore: true,
            rebuild: true,
        };
        expect(dotnetArguments(options, [])).toEqual([
            "dotnet",
            "restore",
            "-p:Configuration=Debug",
        ]);
    });
    test("does not pass a framework to pack or restore flags to clean", () => {
        const options = {
            ...defaultDotnetOptions(),
            framework: "net10.0",
            noRestore: true,
            rebuild: true,
        };
        expect(dotnetArguments({ ...options, task: "pack" }, [])).toEqual([
            "dotnet",
            "pack",
            "-c",
            "Debug",
            "--no-restore",
        ]);
        expect(dotnetArguments({ ...options, task: "clean" }, [])).toEqual([
            "dotnet",
            "clean",
            "-c",
            "Debug",
            "-f",
            "net10.0",
        ]);
    });
    test("only sends enabled, current-config properties with literal MSBuild delimiters", () => {
        const options = {
            ...defaultDotnetOptions(),
            properties: {
                DemoFeature: "false",
                DemoLabel: "space;comma,percent%",
                OutputPath: "C:\\build output",
                RemovedProperty: "ignore",
            },
        };
        expect(dotnetArguments(options, definitions)).toEqual([
            "dotnet",
            "build",
            "-c",
            "Debug",
            "-p:DemoFeature=false",
            "-p:DemoLabel=space%3Bcomma%2Cpercent%25",
            "-p:OutputPath=C:\\build output",
        ]);
        expect(dotnetArguments(defaultDotnetOptions(), definitions)).toEqual([
            "dotnet",
            "build",
            "-c",
            "Debug",
        ]);
    });
    test("preserves empty enabled property values and extra argument boundaries", () => {
        const options = {
            ...defaultDotnetOptions(),
            properties: { DemoLabel: "" },
            additionalArgs: '--output "/tmp/with spaces" -p:Version=1.2.3',
        };
        expect(dotnetArguments(options, definitions)).toEqual([
            "dotnet",
            "build",
            "-c",
            "Debug",
            "-p:DemoLabel=",
            "--output",
            "/tmp/with spaces",
            "-p:Version=1.2.3",
        ]);
    });
    test("custom mode does not append hidden form options", () => {
        const options = {
            ...defaultDotnetOptions(),
            task: "custom" as const,
            summarizeWarnings: true,
            customArgs: 'msbuild -t:Build "-p:Message=hello world"',
            additionalArgs: "--ignored",
            properties: { DemoFeature: "true" },
            noRestore: true,
            rebuild: true,
        };
        expect(dotnetArguments(options, definitions)).toEqual([
            "dotnet",
            "-w",
            "msbuild",
            "-t:Build",
            "-p:Message=hello world",
        ]);
    });
    test("reports invalid input instead of running a partial command", () => {
        expect(() =>
            dotnetArguments(
                { ...defaultDotnetOptions(), additionalArgs: '"unfinished' },
                [],
            ),
        ).toThrow("Close");
        expect(() =>
            dotnetArguments(
                { ...defaultDotnetOptions(), task: "custom", customArgs: " " },
                [],
            ),
        ).toThrow("Enter a dotnet");
        expect(() =>
            dotnetArguments(
                {
                    ...defaultDotnetOptions(),
                    properties: { DemoFeature: "yes" },
                },
                definitions,
            ),
        ).toThrow("true or false");
    });
    test("confirms potentially destructive and advanced operations", () => {
        expect(dotnetNeedsConfirmation(defaultDotnetOptions())).toBe(false);
        expect(
            dotnetNeedsConfirmation({
                ...defaultDotnetOptions(),
                rebuild: true,
            }),
        ).toBe(true);
        for (const task of ["clean", "publish", "custom"] as const)
            expect(
                dotnetNeedsConfirmation({ ...defaultDotnetOptions(), task }),
            ).toBe(true);
        expect(
            dotnetNeedsConfirmation({
                ...defaultDotnetOptions(),
                additionalArgs: "-t:Clean",
            }),
        ).toBe(true);
    });
});
