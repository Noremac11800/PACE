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


class CategorizedPaths:
    """Container for paths organized by clean category."""

    def __init__(self) -> None:
        """Initialize empty path categories."""
        self.project: list[Path] = []
        self.cache: list[Path] = []
        self.custom_cache: list[Path] = []

    def all_paths(self) -> list[Path]:
        """Return all paths combined."""
        return self.project + self.cache + self.custom_cache


def _collect_paths_to_delete(
    project: Project,
    repodir: Path,
    do_cache: bool,
    do_custom_cache: bool,
    do_project: bool,
    nuget_cache_path: Path | None,
) -> CategorizedPaths:
    """Collect all paths that would be deleted for a project.

    Args:
        project: Project to collect paths for.
        repodir: Root directory where repositories are cloned.
        do_cache: Whether to include standard NuGet cache paths.
        do_custom_cache: Whether to include custom NuGet cache paths.
        do_project: Whether to include project bin/obj/AppPackages directories.
        nuget_cache_path: Custom NuGet cache path from config (if any).

    Returns:
        CategorizedPaths with paths organized by category.
    """
    result = CategorizedPaths()

    csproj_full_path = repodir / project.name / project.csproj_path
    project_dir = csproj_full_path.parent
    package_name = csproj_full_path.stem

    # --- bin/, obj/, and AppPackages/ directories ---
    if do_project:
        for artifact_dir_name in ("bin", "obj", "AppPackages"):
            artifact_dir = project_dir / artifact_dir_name
            if artifact_dir.exists():
                result.project.append(artifact_dir)

    # --- Standard NuGet package cache (~/.nuget/packages) ---
    if do_cache:
        for candidate in (package_name, package_name.lower()):
            nuget_dir = Path.home() / ".nuget" / "packages" / candidate
            if nuget_dir.exists():
                result.cache.append(nuget_dir)
                break

        # ~/nuget-packages/ flat cache
        alt_nuget_root = Path.home() / "nuget-packages"
        if alt_nuget_root.exists():
            prefix = f"{package_name}.".lower()
            for nupkg in alt_nuget_root.iterdir():
                if nupkg.name.lower().startswith(prefix):
                    result.cache.append(nupkg)

    # --- Custom NuGet cache path ---
    if do_custom_cache and nuget_cache_path:
        for candidate in (package_name, package_name.lower()):
            custom_nuget_dir = nuget_cache_path / candidate
            if custom_nuget_dir.exists():
                result.custom_cache.append(custom_nuget_dir)
                break

        # Also check for flat .nupkg files in custom cache
        if nuget_cache_path.exists():
            prefix = f"{package_name}.".lower()
            for nupkg in nuget_cache_path.iterdir():
                if nupkg.is_file() and nupkg.name.lower().startswith(prefix):
                    result.custom_cache.append(nupkg)

    return result


def _delete_paths(paths: list[Path]) -> list[str]:
    """Delete the given paths and return a list of what was removed.

    Args:
        paths: List of paths to delete.

    Returns:
        List of description strings for what was removed.
    """
    removed: list[str] = []

    for path in paths:
        try:
            if path.is_dir():
                shutil.rmtree(path)
                removed.append(f"dir:{path.name}")
            elif path.is_file():
                path.unlink()
                removed.append(f"file:{path.name}")
        except OSError:
            pass

    return removed


def _clean_project(
    project: Project,
    repodir: Path,
    statuses: ProjectCleanStatus,
    do_cache: bool,
    do_custom_cache: bool,
    do_project: bool,
    dry_run: bool,
    nuget_cache_path: Path | None,
) -> None:
    """Clean build artifacts and NuGet cache for a single project.

    Args:
        project: Project to clean.
        repodir: Root directory where repositories are cloned.
        statuses: ProjectCleanStatus instance to update.
        do_cache: Whether to clean standard NuGet cache.
        do_custom_cache: Whether to clean custom NuGet cache.
        do_project: Whether to clean project bin/obj/AppPackages directories.
        dry_run: If True, only show what would be deleted.
        nuget_cache_path: Custom NuGet cache path from config.
    """
    if dry_run:
        statuses.set(project.name, Text("Analyzing...", style="cyan"))
    else:
        statuses.set(project.name, Spinner("dots", text="Cleaning...", style="cyan"))

    paths_to_delete = _collect_paths_to_delete(
        project, repodir, do_cache, do_custom_cache, do_project, nuget_cache_path
    )

    if dry_run:
        all_paths = paths_to_delete.all_paths()
        if all_paths:
            removed_str = ", ".join(p.name for p in all_paths)
            statuses.set(project.name, Text(f"Would delete: {removed_str}", style="yellow"))
        else:
            statuses.set(project.name, Text("Nothing to delete", style="green"))
    else:
        removed = _delete_paths(paths_to_delete.all_paths())
        if removed:
            removed_str = ", ".join(removed)
            statuses.set(project.name, Text(f"Done (removed: {removed_str})", style="green"))
        else:
            statuses.set(project.name, Text("Done (nothing to clean)", style="yellow"))


def _format_paths_for_display(paths: list[Path]) -> str:
    """Format a list of paths for display in a table cell.

    Args:
        paths: List of paths to format.

    Returns:
        Formatted string with path names and types, comma-separated.
    """
    if not paths:
        return "[dim]-[/dim]"
    path_strs: list[str] = []
    for path in paths:
        path_type = "dir" if path.is_dir() else "file"
        path_strs.append(f"[{path_type}]{path.name}")
    return ", ".join(path_strs)


def _display_dry_run_results(
    console: Console,
    results: dict[str, CategorizedPaths],
    do_cache: bool,
    do_custom_cache: bool,
    do_project: bool,
    nuget_cache_path: Path | None,
) -> None:
    """Display dry-run results in a table format.

    Args:
        console: Rich console instance for output.
        results: Dictionary mapping project names to categorized paths.
        do_cache: Whether cache cleaning is enabled.
        do_custom_cache: Whether custom cache cleaning is enabled.
        do_project: Whether project cleaning is enabled.
        nuget_cache_path: Custom NuGet cache path from config.
    """
    table = Table(
        show_header=True,
        header_style="bold cyan",
        title="[bold]Dry Run: Items that would be deleted[/bold]",
    )
    table.add_column("Project", overflow="fold")
    if do_project:
        table.add_column("Project (bin/obj)", overflow="fold")
    if do_cache:
        table.add_column("~/.nuget/packages", overflow="fold")
    if do_custom_cache:
        if nuget_cache_path:
            cache_header = f"Custom Cache ({nuget_cache_path})"
        else:
            cache_header = "Custom Cache (not configured)"
        table.add_column(cache_header, overflow="fold")

    total_items = 0
    for project_name in sorted(results.keys()):
        categorized = results[project_name]
        row: list[str] = [project_name]
        if do_project:
            row.append(_format_paths_for_display(categorized.project))
            total_items += len(categorized.project)
        if do_cache:
            row.append(_format_paths_for_display(categorized.cache))
            total_items += len(categorized.cache)
        if do_custom_cache:
            row.append(_format_paths_for_display(categorized.custom_cache))
            total_items += len(categorized.custom_cache)
        table.add_row(*row)

    console.print(table)
    console.print(f"[bold]Total items to delete: {total_items}[/bold]")


def _display_custom_cache_feedback(
    console: Console, nuget_cache_path: Path | None, do_custom_cache: bool
) -> None:
    """Display feedback about custom cache configuration.

    Args:
        console: Rich console instance for output.
        nuget_cache_path: Custom NuGet cache path from config.
        do_custom_cache: Whether custom cache cleaning was requested.
    """
    if do_custom_cache:
        if nuget_cache_path is None:
            console.print(
                "[yellow]Warning: --custom-cache specified but nuget_cache_path is not configured[/yellow]"
            )
        elif not nuget_cache_path.exists():
            console.print(
                f"[yellow]Warning: Custom cache path does not exist: {nuget_cache_path}[/yellow]"
            )


def run(
    console: Console,
    config: Config,
    cache: bool = False,
    custom_cache: bool = False,
    project: bool = False,
    dry_run: bool = False,
) -> None:
    """Delete build artifacts and NuGet cache for all projects in parallel.

    If no specific options are provided (--cache, --custom-cache, --project),
    all cleaning operations are performed.

    Args:
        console: Rich console instance for output.
        config: PACE configuration.
        cache: Clean standard NuGet cache (~/.nuget/packages).
        custom_cache: Clean custom NuGet cache (from nuget_cache_path config).
        project: Clean project bin/, obj/, and AppPackages/ directories.
        dry_run: Show what would be deleted without actually deleting.
    """
    # If no options specified, do all
    do_cache = cache or (not cache and not custom_cache and not project)
    do_custom_cache = custom_cache or (not cache and not custom_cache and not project)
    do_project = project or (not cache and not custom_cache and not project)

    # Display feedback about custom cache configuration
    _display_custom_cache_feedback(console, config.nuget_cache_path, do_custom_cache)

    # For dry-run, we collect all results first then display them
    if dry_run:
        dry_run_results: dict[str, CategorizedPaths] = {}
        for proj in config.projects:
            paths = _collect_paths_to_delete(
                proj,
                config.repodir,
                do_cache,
                do_custom_cache,
                do_project,
                config.nuget_cache_path,
            )
            dry_run_results[proj.name] = paths

        _display_dry_run_results(
            console,
            dry_run_results,
            do_cache,
            do_custom_cache,
            do_project,
            config.nuget_cache_path,
        )
        return

    # Normal execution with live status table
    statuses = ProjectCleanStatus()
    for proj in config.projects:
        statuses.set(proj.name, Spinner("dots", text="Dispatching to thread...", style="dim"))

    with (
        Live(statuses.get_table(), console=console, refresh_per_second=10) as live,
        ThreadPoolExecutor() as executor,
    ):
        futures = {
            executor.submit(
                _clean_project,
                proj,
                config.repodir,
                statuses,
                do_cache,
                do_custom_cache,
                do_project,
                dry_run,
                config.nuget_cache_path,
            ): proj
            for proj in config.projects
        }
        for _ in as_completed(futures):
            live.update(statuses.get_table())
