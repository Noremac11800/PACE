"""Pydantic models for PACE configuration."""

import json
import os
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

import tomli
from pydantic import BaseModel, model_validator

PACE_DIR = Path.home() / ".pace"
SETTINGS_PATH = PACE_DIR / "settings.json"
CONFIGS_DIR = PACE_DIR / "configs"
LAST_ACTIVE_CONFIG_KEY = "lastActiveConfig"


class BuildProp(BaseModel):
    """A configurable MSBuild property defined in the PACE config.

    Attributes:
        name: MSBuild property name (e.g. DevSolution).
        datatype: Value type — "boolean", "string", or "path".
        default: Default value as a string.
    """

    name: str
    datatype: str = "string"
    default: str | bool | Path = ""


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
        nuget_cache_path: Optional path to a custom NuGet package cache directory.
    """

    repodir: Path = Path()
    projects: list[Project]
    build_props: list[BuildProp] = []
    nuget_cache_path: Path | None = None

    @model_validator(mode="after")
    def apply_env_overrides(self) -> "Config":
        """Apply environment variable overrides to the configuration."""
        return self  # Something is not working here
        env_repodir = os.getenv("REPODIR")
        if env_repodir is not None:
            self.repodir = Path(env_repodir)

        if self.repodir.exists() and self.repodir != Path():
            return self
        try:
            self.repodir.mkdir(parents=True, exist_ok=True)
            return self
        except Exception:
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


def resolve_config_path(value: str | Path) -> Path:
    """Resolve a config reference to a filesystem path.

    Bare filenames (no directory component) are resolved against ~/.pace/configs.

    Args:
        value: Config filename or path.

    Returns:
        Path: Resolved path to the configuration file.
    """
    path = Path(value).expanduser()
    if path.parent == Path() and not path.exists():
        return CONFIGS_DIR / path.name
    return path


def get_last_active_config_path() -> Path | None:
    """Read the last active config from ~/.pace/settings.json.

    Returns:
        Path to the config file if it is recorded and exists, otherwise None.
    """
    settings: Any
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(settings, dict):
        return None

    value: Any = settings.get(LAST_ACTIVE_CONFIG_KEY)
    if not isinstance(value, str) or not value:
        return None

    path = resolve_config_path(value)
    return path if path.exists() else None


def set_last_active_config(config_path: Path) -> None:
    """Record the given config as the last active config in ~/.pace/settings.json.

    Configs living in ~/.pace/configs are stored by filename, anything else by
    absolute path. Failures are silently ignored so commands still run.

    Args:
        config_path: Path to the configuration file that was used.
    """
    resolved = config_path.expanduser().resolve()
    value = resolved.name if resolved.parent == CONFIGS_DIR.resolve() else str(resolved)

    settings: dict[str, Any] = {}
    try:
        if SETTINGS_PATH.exists():
            loaded: Any = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                settings = loaded
    except (OSError, json.JSONDecodeError):
        settings = {}

    if settings.get(LAST_ACTIVE_CONFIG_KEY) == value:
        return

    settings[LAST_ACTIVE_CONFIG_KEY] = value
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


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
            # TOML uses "build-props" (hyphen); map to build_props
            if "build-props" in data:
                data["build_props"] = data.pop("build-props")
            config = Config(**data)

            # Filter projects based on dependency chain
            if from_repo is not None or to_repo is not None:
                config.projects = filter_projects_in_dependency_chain(
                    config.projects, from_repo, to_repo
                )

            return config
    except Exception as e:
        raise ValueError(f"Failed to load configuration file {file_path} with error:\n{e}") from e
