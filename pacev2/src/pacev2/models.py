# Copyright (c) 2026

"""Validated PACE configuration and dependency-chain selection."""

from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from pacev2.paths import normalize_path

ConfigPath = Annotated[Path, BeforeValidator(normalize_path)]


class BuildProp(BaseModel):
    """MSBuild property with its declared datatype and default value."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    datatype: Literal["boolean", "string", "path"] = "string"
    default: str | bool | Path = ""

    @model_validator(mode="after")
    def normalize_default(self) -> Self:
        """Normalize path-valued defaults while preserving empty values."""
        if self.datatype == "path" and self.default != "":
            self.default = normalize_path(self.default)
        return self


class Project(BaseModel):
    """Named repository with its project file and dependencies."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    csproj_path: ConfigPath
    repo_url: str | None = None
    sln_group: str | None = None
    depends_on: list[str] = Field(default_factory=list)


class Config(BaseModel):
    """Workspace paths, projects, and shared build properties."""

    model_config = ConfigDict(extra="forbid", validate_by_name=True)

    repodir: ConfigPath = Path()
    projects: list[Project]
    nuget_cache_path: ConfigPath | None = None
    build_props: list[BuildProp] = Field(default_factory=list, alias="build-props")

    @model_validator(mode="after")
    def validate_dependencies(self) -> Self:
        """Reject duplicate names, missing dependencies, and dependency cycles."""
        dependencies = {project.name: set(project.depends_on) for project in self.projects}
        if len(dependencies) != len(self.projects):
            raise ValueError("Project names must be unique")
        for name, required in dependencies.items():
            missing = required - dependencies.keys()
            if missing:
                raise ValueError(
                    f"Project '{name}' depends on unknown projects: {', '.join(sorted(missing))}"
                )
        try:
            TopologicalSorter(dependencies).prepare()
        except CycleError as error:
            raise ValueError("Project dependencies contain a cycle") from error
        return self

    def filtered(self, from_repo: str | None = None, to_repo: str | None = None) -> Self:
        """Keep the inclusive dependency chain, preserving declaration order."""
        if from_repo is None and to_repo is None:
            return self

        dependencies = {project.name: set(project.depends_on) for project in self.projects}
        for name in (from_repo, to_repo):
            if name is not None and name not in dependencies:
                raise ValueError(f"Project '{name}' not found in configuration")

        included = set(dependencies)
        if from_repo is not None:
            dependents: dict[str, set[str]] = {name: set() for name in dependencies}
            for name, required in dependencies.items():
                for dependency in required:
                    dependents[dependency].add(name)
            included &= _reachable(from_repo, dependents)
        if to_repo is not None:
            included &= _reachable(to_repo, dependencies)

        return self.model_copy(
            update={"projects": [project for project in self.projects if project.name in included]}
        )


def _reachable(start: str, graph: dict[str, set[str]]) -> set[str]:
    visited: set[str] = set()
    pending = [start]
    while pending:
        name = pending.pop()
        if name not in visited:
            visited.add(name)
            pending.extend(graph[name] - visited)
    return visited
