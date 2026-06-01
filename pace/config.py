"""Pydantic models for PACE configuration."""

import os
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

import tomli
from pydantic import BaseModel, model_validator


class Project(BaseModel):
    """Project model for PACE.

    Attributes:
        name: Name of the project.
        csproj_path: Path to the project file.
        repo_url: URL of the repository. (Optional)
        depends_on: List of project names this project depends on.
    """

    name: str
    csproj_path: Path
    repo_url: str | None = None
    depends_on: list[str] = []


class Config(BaseModel):
    """Configuration model for PACE.

    Attributes:
        repodir: Directory where repositories are cloned.
        projects: List of projects.
    """

    repodir: Path = Path()
    projects: list[Project]

    @model_validator(mode="after")
    def apply_env_overrides(self) -> "Config":
        """Apply environment variable overrides to the configuration."""
        env_repodir = os.getenv("REPODIR")
        if env_repodir is not None:
            self.repodir = Path(env_repodir)

        if self.repodir.exists() and self.repodir != Path():
            return self
        try:
            self.repodir.mkdir(parents=True, exist_ok=True)
            return self
        except Exception:  # noqa: BLE001
            raise RuntimeError(
                f"Repository directory {self.repodir} does not exist and could not be created."
            ) from None


def build_dependency_graph(projects: list[Project]) -> dict[str, set[str]]:
    """Build a reverse dependency graph (project -> projects that depend on it).

    Args:
        projects: List of projects.

    Returns:
        Dictionary mapping project names to set of projects that depend on them.
    """
    # Build reverse dependency graph (who depends on whom)
    dependents: dict[str, set[str]] = {p.name: set() for p in projects}
    for project in projects:
        for dep in project.depends_on:
            if dep in dependents:
                dependents[dep].add(project.name)
    return dependents


def filter_projects_in_dependency_chain(
    projects: list[Project], from_repo: str | None, to_repo: str | None
) -> list[Project]:
    """Filter projects to include only those in the dependency chain between from_repo and to_repo.

    This includes:
    1. The from_repo itself
    2. All projects that are on a path from from_repo to to_repo (following dependencies)

    Args:
        projects: List of all projects.
        from_repo: Starting repo name (inclusive).
        to_repo: Ending repo name (inclusive).

    Returns:
        Filtered list of projects in the dependency chain.
    """
    if from_repo is None and to_repo is None:
        return projects

    # Build lookup maps
    project_by_name = {p.name: p for p in projects}

    # Build reverse dependency graph (who depends on whom - edges point from dependency to dependent)
    dependents = build_dependency_graph(projects)

    # Build forward dependency graph (what each project depends on)
    dependencies: dict[str, set[str]] = {p.name: set(p.depends_on) for p in projects}

    # Validate repo names
    if from_repo is not None and from_repo not in project_by_name:
        raise ValueError(f"Project '{from_repo}' not found in configuration")
    if to_repo is not None and to_repo not in project_by_name:
        raise ValueError(f"Project '{to_repo}' not found in configuration")

    def can_reach_downstream(start: str, end: str) -> bool:
        """Check if start can reach end by following dependency edges (start's dependencies can reach start)."""
        if start == end:
            return True
        visited: set[str] = set()
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current == end:
                return True
            if current not in visited:
                visited.add(current)
                # Follow dependents (downstream)
                for neighbor in dependents.get(current, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
        return False

    def can_reach_upstream(start: str, end: str) -> bool:
        """Check if start can reach end by following upstream edges (what start depends on)."""
        if start == end:
            return True
        visited: set[str] = set()
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current == end:
                return True
            if current not in visited:
                visited.add(current)
                # Follow dependencies (upstream)
                for neighbor in dependencies.get(current, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
        return False

    # Determine which projects are on valid paths
    included: set[str] = set()

    if from_repo is None and to_repo is not None:
        # Only --to specified: include to_repo and all its dependencies (transitively)
        # A project is included if to_repo can reach it by going upstream (meaning it's a dependency)
        for project in projects:
            if can_reach_upstream(to_repo, project.name):
                included.add(project.name)

        # Collect all dependencies of included projects (transitively)
        all_deps: set[str] = set()
        queue = list(included)
        while queue:
            current = queue.pop(0)
            for dep in dependencies.get(current, set()):
                if dep not in all_deps and dep not in included:
                    all_deps.add(dep)
                    queue.append(dep)
        final_names = included | all_deps
    elif from_repo is not None and to_repo is None:
        # Only --from specified: include from_repo and all projects reachable downstream
        # A project is included if from_repo can reach it by going downstream
        for project in projects:
            if can_reach_downstream(from_repo, project.name):
                included.add(project.name)
        final_names = included
    else:
        # Both --from and --to specified: include projects on paths from from_repo to to_repo
        # A project is on a path if:
        # - from_repo can reach it downstream (it's reachable from from_repo)
        # - AND it can reach to_repo downstream (to_repo is reachable from it)
        for project in projects:
            if can_reach_downstream(from_repo, project.name) and can_reach_downstream(
                project.name, to_repo
            ):
                included.add(project.name)
        final_names = included

    return [p for p in projects if p.name in final_names]


def load_config(
    file_path: Path | Traversable | None = None,
    from_repo: str | None = None,
    to_repo: str | None = None,
) -> Config:
    """Load a TOML file and return its contents as a Config object.

    Args:
        file_path: Path to the TOML file.
        from_repo: Starting repo name to filter the dependency chain.
        to_repo: Ending repo name to filter the dependency chain.

    Returns:
        Config: Configuration object with filtered projects if from_repo/to_repo specified.
    """
    if file_path is None:
        file_path = files("pace.data").joinpath("pace.toml")

    try:
        with file_path.open("rb") as f:
            data = tomli.load(f)
            config = Config(**data)

            # Filter projects based on dependency chain
            if from_repo is not None or to_repo is not None:
                config.projects = filter_projects_in_dependency_chain(
                    config.projects, from_repo, to_repo
                )

            return config
    except Exception as e:
        raise ValueError(f"Failed to load configuration file {file_path} with error:\n{e}") from e
