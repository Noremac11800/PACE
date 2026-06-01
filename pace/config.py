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

    @staticmethod
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

    @staticmethod
    def can_reach_downstream(start: str, end: str, dependents: dict[str, set[str]]) -> bool:
        """Check if start can reach end by following dependency edges (start's dependencies can reach start).

        Args:
            start: Starting project name.
            end: Target project name.
            dependents: Reverse dependency graph (project -> projects that depend on it).

        Returns:
            True if start can reach end, False otherwise.
        """
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
                        queue.extend([neighbor])
        return False

    @staticmethod
    def can_reach_upstream(start: str, end: str, dependencies: dict[str, set[str]]) -> bool:
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
                        queue.extend([neighbor])
        return False


def _filter_projects_to_target(
    projects: list[Project], to_repo: str, dependencies: dict[str, set[str]]
) -> set[str]:
    """Filter projects to include target repo and all its dependencies (transitively)."""
    included: set[str] = set()

    for project in projects:
        if Config.can_reach_upstream(to_repo, project.name, dependencies):
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

    return included | all_deps


def _filter_projects_from_source(
    projects: list[Project], from_repo: str, dependents: dict[str, set[str]]
) -> set[str]:
    """Filter projects to include source repo and all projects reachable downstream."""
    included: set[str] = set()

    for project in projects:
        if Config.can_reach_downstream(from_repo, project.name, dependents):
            included.add(project.name)

    return included


def _filter_projects_between(
    projects: list[Project], from_repo: str, to_repo: str, dependents: dict[str, set[str]]
) -> set[str]:
    """Filter projects to include those on paths from from_repo to to_repo."""
    included: set[str] = set()

    for project in projects:
        if Config.can_reach_downstream(
            from_repo, project.name, dependents
        ) and Config.can_reach_downstream(project.name, to_repo, dependents):
            included.add(project.name)

    return included


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
    dependents = Config.build_dependency_graph(projects)

    # Build forward dependency graph (what each project depends on)
    dependencies: dict[str, set[str]] = {p.name: set(p.depends_on) for p in projects}

    # Validate repo names
    if from_repo is not None and from_repo not in project_by_name:
        raise ValueError(f"Project '{from_repo}' not found in configuration")
    if to_repo is not None and to_repo not in project_by_name:
        raise ValueError(f"Project '{to_repo}' not found in configuration")

    # Determine which projects are on valid paths using helper functions
    if from_repo is None and to_repo is not None:
        final_names = _filter_projects_to_target(projects, to_repo, dependencies)
    elif from_repo is not None and to_repo is None:
        final_names = _filter_projects_from_source(projects, from_repo, dependents)
    else:
        final_names = _filter_projects_between(projects, from_repo, to_repo, dependents)

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
