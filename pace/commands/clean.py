"""pace clean command - Delete build artifacts and cached NuGet packages for all projects."""

import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from pace.config import Config, Project


class ProjectCleanStatus:
    """Thread-safe status tracker for each project's clean operation."""

    def __init__(self) -> None:
        """Initialize the status tracker."""
        self._lock = threading.Lock()
        self._status: dict[str, Text | Spinner] = {}

    def set(self, project_name: str, status: Text | Spinner) -> None:
        """Set the status for a project."""
        with self._lock:
            self._status[project_name] = status

    def get_table(self) -> Table:
        """Get a table of all project statuses."""
        with self._lock:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Project")
            table.add_column("Status")
            for project_name, status in sorted(self._status.items()):
                table.add_row(project_name, status)
            return table


def _remove_dir(path: Path) -> bool:
    """Remove a directory tree. Returns True if removed, False if it did not exist."""
    if path.exists():
        shutil.rmtree(path)
        return True
    return False


def _clean_project(project: Project, repodir: Path, statuses: ProjectCleanStatus) -> None:
    """Clean build artifacts and NuGet cache for a single project.

    Args:
        project: Project to clean.
        repodir: Root directory where repositories are cloned.
        statuses: ProjectCleanStatus instance to update.
    """
    statuses.set(project.name, Spinner("dots", text="Cleaning...", style="cyan"))

    csproj_full_path = repodir / project.name / project.csproj_path
    project_dir = csproj_full_path.parent

    removed: list[str] = []

    # --- bin/ and obj/ directories ---
    for artifact_dir_name in ("bin", "obj"):
        artifact_dir = project_dir / artifact_dir_name
        if _remove_dir(artifact_dir):
            removed.append(artifact_dir_name)

    # --- NuGet package cache ---
    # The package name is derived from the csproj filename stem,
    # e.g. "Esri.Toolkit.MSBuild.csproj" -> package_name "Esri.Toolkit.MSBuild".

    package_name = csproj_full_path.stem

    # Standard ~/.nuget/packages/<PackageName>/ — NuGet stores these as a subdirectory
    # per package (case-insensitive name on Windows, lower-cased on Linux/macOS).
    for candidate in (package_name, package_name.lower()):
        nuget_dir = Path.home() / ".nuget" / "packages" / candidate
        if _remove_dir(nuget_dir):
            removed.append(f"nuget:{candidate}")
            break  # both paths resolve to the same dir on case-insensitive FSes

    # ~/nuget-packages/ stores flat .nupkg files named "<PackageName>.<Version>.nupkg".
    # Delete every file whose name starts with "<PackageName>." (case-insensitive).
    alt_nuget_root = Path.home() / "nuget-packages"
    if alt_nuget_root.exists():
        prefix = f"{package_name}.".lower()
        matched = [f for f in alt_nuget_root.iterdir() if f.name.lower().startswith(prefix)]
        for nupkg in matched:
            nupkg.unlink()
            removed.append(f"nupkg:{nupkg.name}")

    # --- Build final status message ---
    if removed:
        removed_str = ", ".join(removed)
        statuses.set(project.name, Text(f"Done \u2713 (removed: {removed_str})", style="green"))
    else:
        statuses.set(project.name, Text("Done \u2713 (nothing to clean)", style="yellow"))


def run(console: Console, config: Config) -> None:
    """Delete build artifacts and NuGet cache for all projects in parallel.

    Removes bin/ and obj/ directories next to each project's .csproj file,
    and removes any matching NuGet package cache entries under ~/.nuget/packages/
    and ~/nuget-packages/ (if that directory exists).

    Args:
        console: Rich console instance for output.
        config: PACE configuration.
    """
    statuses = ProjectCleanStatus()
    for project in config.projects:
        statuses.set(project.name, Spinner("dots", text="Dispatching to thread...", style="dim"))

    with (
        Live(statuses.get_table(), console=console, refresh_per_second=10) as live,
        ThreadPoolExecutor() as executor,
    ):
        futures = {
            executor.submit(_clean_project, project, config.repodir, statuses): project
            for project in config.projects
        }
        for _ in as_completed(futures):
            live.update(statuses.get_table())
