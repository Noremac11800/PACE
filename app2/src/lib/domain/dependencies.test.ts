import { expect, test } from "bun:test";
import { dependencyLayers } from "./dependencies";
import type { Project } from "./types";

const project = (name: string, depends_on: string[] = []): Project => ({
    name,
    depends_on,
    csproj_path: `${name}.csproj`,
    repo_url: null,
    sln_group: null,
});

test("orders dependency layers without changing declaration order within a layer", () => {
    const projects = [
        project("app", ["ui", "api"]),
        project("ui", ["core"]),
        project("api", ["core"]),
        project("core"),
    ];
    expect(
        dependencyLayers(projects).map((layer) =>
            layer.map((item) => item.name),
        ),
    ).toEqual([["core"], ["ui", "api"], ["app"]]);
});
test("handles empty and filtered configurations", () => {
    expect(dependencyLayers([])).toEqual([]);
    expect(
        dependencyLayers([project("app", ["outside-scope"])])[0][0].name,
    ).toBe("app");
});
test("rejects cycles rather than looping", () => {
    expect(() =>
        dependencyLayers([project("a", ["b"]), project("b", ["a"])]),
    ).toThrow("cycle");
});
