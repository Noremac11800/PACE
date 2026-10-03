import { describe, expect, test } from "bun:test";
import {
    cleanOutput,
    commandPreview,
    parseArguments,
    scopedArgs,
} from "./commands";

describe("CLI argument handling", () => {
    test("preserves quoted arguments and empty values", () => {
        expect(
            parseArguments(
                `commit -m "a useful message" --author='A Person' ""`,
            ),
        ).toEqual([
            "commit",
            "-m",
            "a useful message",
            "--author=A Person",
            "",
        ]);
    });
    test("preserves Windows paths and literal shell syntax", () => {
        expect(
            parseArguments(String.raw`-C C:\repos\work status && echo $HOME`),
        ).toEqual([
            "-C",
            String.raw`C:\repos\work`,
            "status",
            "&&",
            "echo",
            "$HOME",
        ]);
    });
    test("supports escaped spaces and quotes", () => {
        expect(
            parseArguments(String.raw`checkout branch\ name "a\"b"`),
        ).toEqual(["checkout", "branch name", 'a"b']);
    });
    test("rejects unfinished quotes", () => {
        expect(() => parseArguments('commit -m "unfinished')).toThrow(
            "Close the quoted argument",
        );
    });
    test("puts global scope before the Git subcommand", () => {
        expect(
            scopedArgs("/a b/work.toml", "core", "app", ["git", "status"]),
        ).toEqual([
            "-C",
            "/a b/work.toml",
            "--from",
            "core",
            "--to",
            "app",
            "git",
            "status",
        ]);
    });
    test("quotes the display without changing the executed arguments", () => {
        expect(commandPreview(["git", "commit", "-m", "hello world"])).toBe(
            'pacev2 git commit -m "hello world"',
        );
    });
    test("removes terminal color controls", () => {
        expect(cleanOutput("\x1b[31merror\x1b[0m\r\n")).toBe("error\n");
    });
});
