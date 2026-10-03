import type { Project } from "./types";

export function dependencyLayers(projects: Project[]): Project[][] {
    const remaining = new Map(
        projects.map((project) => [project.name, project]),
    );
    const layers: Project[][] = [];
    while (remaining.size) {
        const layer = [...remaining.values()].filter((project) =>
            project.depends_on.every((name) => !remaining.has(name)),
        );
        if (!layer.length)
            throw new Error("The configuration contains a dependency cycle.");
        layers.push(layer);
        layer.forEach((project) => remaining.delete(project.name));
    }
    return layers;
}
