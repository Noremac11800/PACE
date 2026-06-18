"""pace dotnet command - Execute dotnet commands across the project graph."""

import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table

from pace.config import Config, Project

_WARNING_PATTERN = re.compile(r":\s+(?:\w+ )?warning (\w+):\s+(.+?)(?:\s+See https?://\S+)?\s*\[")
_PROJECT_PATTERN = re.compile(r"\[([^\]]+\.csproj)")


@dataclass
class _WarningSummary:
    count: int = field(default=0)
    description: str = field(default="")


def _build_stem_to_repo(config: Config) -> dict[str, str]:
    """Map csproj stem names to their repo/project names from the config."""
    mapping: dict[str, str] = {}
    for project in config.projects:
        stem = Path(project.csproj_path).stem
        mapping[stem] = project.name
    return mapping


def _print_warning_tables(console: Console, config: Config, lines: list[str]) -> None:
    """Parse captured build output lines and print warning summary tables."""
    warnings: dict[str, _WarningSummary] = defaultdict(_WarningSummary)
    by_project: dict[str, int] = defaultdict(int)
    seen: set[str] = set()

    for line in lines:
        match = _WARNING_PATTERN.search(line)
        if match:
            if line in seen:
                continue
            seen.add(line)

            code = match.group(1)
            description = match.group(2).strip()
            warnings[code].count += 1
            warnings[code].description = description

            proj_match = _PROJECT_PATTERN.search(line)
            if proj_match:
                proj_name = Path(proj_match.group(1)).stem
                by_project[proj_name] += 1

    if not warnings:
        console.print("[yellow]No warnings found.[/yellow]")
        return

    stem_to_repo = _build_stem_to_repo(config)

    sorted_warnings = sorted(warnings.items(), key=lambda x: x[1].count, reverse=True)

    by_code_table = Table(title="Warnings by Code", show_header=True, header_style="bold cyan")
    by_code_table.add_column("Code", style="bold yellow", no_wrap=True)
    by_code_table.add_column("Count", justify="right", style="bold red")
    by_code_table.add_column("Description")

    for code, data in sorted_warnings:
        by_code_table.add_row(code, str(data.count), data.description)

    console.print(by_code_table)

    sorted_projects = sorted(by_project.items(), key=lambda x: x[1], reverse=True)

    by_project_table = Table(
        title="Warnings by Project", show_header=True, header_style="bold cyan"
    )
    by_project_table.add_column("Project", style="bold blue")
    by_project_table.add_column("Repo", style="dim")
    by_project_table.add_column("Count", justify="right", style="bold red")

    for proj_stem, count in sorted_projects:
        repo_name = stem_to_repo.get(proj_stem, "")
        by_project_table.add_row(proj_stem, repo_name, str(count))

    console.print(by_project_table)
    console.print(f"[bold]Total warnings:[/bold] {sum(v.count for v in warnings.values())}")


# In-memory cache (loaded from disk)
_tf_cache: dict[str, tuple[str, float]] = {}
_cache_loaded = False
_CACHE_DIR = Path.home() / ".pace" / "cache"
_CACHE_FILE = _CACHE_DIR / "dotnet_cache.json"


def _ensure_cache_dir() -> None:
    """Create cache directory if it doesn't exist."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_cache() -> None:
    """Load cache from disk."""
    global _cache_loaded, _tf_cache
    if _cache_loaded:
        return
    _ensure_cache_dir()
    if _CACHE_FILE.exists():
        try:
            with _CACHE_FILE.open(encoding="utf-8") as f:
                data = json.load(f)
            # Convert string keys back to the expected format
            _tf_cache = {k: (v[0], v[1]) for k, v in data.items()}
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            _tf_cache = {}
    _cache_loaded = True


def _save_cache() -> None:
    """Save cache to disk."""
    _ensure_cache_dir()
    # Convert Path keys to strings for JSON serialization
    data = {k: list(v) for k, v in _tf_cache.items()}
    with _CACHE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _get_cached_target_frameworks(project_path: Path) -> str | None:
    """Get TargetFrameworks from cache or parse from csproj file.

    Uses file mtime to invalidate cache entries. Cache is persisted to disk.
    """
    _load_cache()

    try:
        mtime = project_path.stat().st_mtime
    except OSError:
        return None

    cache_key = str(project_path.resolve())

    if cache_key in _tf_cache:
        cached_frameworks, cached_mtime = _tf_cache[cache_key]
        if mtime == cached_mtime:
            return cached_frameworks

    # Use dotnet msbuild to evaluate TargetFrameworks (handles MSBuild variables like $(NETAndroidTarget))
    try:
        result = subprocess.run(
            ["dotnet", "msbuild", str(project_path), "-getProperty:TargetFrameworks"],
            capture_output=True,
            text=True,
            check=False,
            cwd=project_path.parent,
        )
        if result.returncode == 0:
            frameworks = result.stdout.strip()
            _tf_cache[cache_key] = (frameworks, mtime)
            _save_cache()
            return frameworks
        _tf_cache[cache_key] = ("", mtime)
        _save_cache()
        return ""
    except Exception:
        _tf_cache[cache_key] = ("", mtime)
        _save_cache()
        return ""


def _is_target_platform_supported(project_path: Path, platform: str) -> bool:
    """Check if a project supports the target platform by parsing its csproj file."""
    target_frameworks = _get_cached_target_frameworks(project_path)
    if target_frameworks is None:
        return False
    return platform.lower() in target_frameworks.lower()


def get_framework_from_args(args: list[str]) -> str | None:
    """Extract framework from command line arguments."""
    for i, arg in enumerate(args):
        if arg in ("-f", "--framework") and i + 1 < len(args):
            framework = args[i + 1]
            if "ios" in framework.lower():
                return "iOS"
            if "android" in framework.lower():
                return "Android"
            if "windows" in framework.lower():
                return "Windows"
            if "maccatalyst" in framework.lower():
                return "Maccatalyst"
    return None


def filter_projects_by_framework(config: Config, framework: str) -> list[Project]:
    """Filter projects based on framework compatibility."""
    supported_projects: list[Project] = []
    for project in config.projects:
        project_path = config.repodir / project.name / project.csproj_path
        if _is_target_platform_supported(project_path, framework):
            supported_projects.append(project)
    return supported_projects


def get_slnx_project_paths(slnx_path: Path) -> set[Path] | None:
    """Return the set of absolute project paths in a .slnx file using dotnet sln list.

    Returns None if the command fails (treats the file as malformed/unusable).
    """
    result = subprocess.run(
        ["dotnet", "sln", str(slnx_path), "list"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    paths: set[Path] = set()
    lines = result.stdout.splitlines()
    # Output format:
    #   Project(s)
    #   ----------
    #   relative\path\to\Project.csproj
    #   ...
    in_list = False
    for line in lines:
        if line.startswith("---"):
            in_list = True
            continue
        if in_list and line.strip():
            paths.add((slnx_path.parent / line.strip()).resolve())
    return paths


def _create_empty_slnx(console: Console, config: Config, slnx_name: str) -> bool:
    """Create an empty solution file. Returns True on success."""
    cmd = [
        "dotnet",
        "new",
        "sln",
        "-n",
        slnx_name.replace(".slnx", ""),
        "-o",
        str(config.repodir),
        "--force",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        console.print(f"[red]Failed to create solution: {result.stderr}[/red]")
        return False
    return True


def _sln_add(console: Console, slnx_path: Path, project_path: Path) -> None:
    result = subprocess.run(
        ["dotnet", "sln", str(slnx_path), "add", str(project_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        console.print(f"[red]Failed to add {project_path.name}: {result.stderr}[/red]")


def _sln_remove(console: Console, slnx_path: Path, project_path: Path) -> None:
    result = subprocess.run(
        ["dotnet", "sln", str(slnx_path), "remove", str(project_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        console.print(f"[red]Failed to remove {project_path.name}: {result.stderr}[/red]")


def _resolve_desired_projects(
    console: Console,
    config: Config,
    framework: str | None,
) -> dict[Path, Project]:
    """Return {absolute_csproj_path: Project} for the projects to include."""
    desired: dict[Path, Project] = {}

    for project in config.projects:
        full_path = (config.repodir / project.name / project.csproj_path).resolve()
        if not full_path.exists():
            console.print(f"[yellow]Warning: Project file not found: {full_path}[/yellow]")
            continue
        if not framework or _is_target_platform_supported(
            config.repodir / project.name / project.csproj_path, framework
        ):
            desired[full_path] = project

    label = f"compatible with {framework}" if framework else "total"
    console.print(f"Found {len(desired)} projects {label}")
    return desired


def _update_existing_slnx(
    console: Console, config: Config, slnx_path: Path, slnx_name: str, framework: str | None
) -> None:
    existing = get_slnx_project_paths(slnx_path)
    if existing is None:
        console.print("Solution file is malformed, recreating...")
        slnx_path.unlink()
        desired = _resolve_desired_projects(console, config, framework)
        _create_slnx_from_scratch(console, config, slnx_path, slnx_name, desired)
        return

    desired = _resolve_desired_projects(console, config, framework)

    to_add = set(desired.keys()) - existing
    to_remove = existing - set(desired.keys())

    if not to_add and not to_remove:
        console.print("Solution is already up-to-date.")
        return

    console.print(f"Updating solution: +{len(to_add)} / -{len(to_remove)} projects")
    for path in to_remove:
        _sln_remove(console, slnx_path, path)
    for path in to_add:
        _sln_add(console, slnx_path, path)


def _create_slnx_from_scratch(
    console: Console, config: Config, slnx_path: Path, slnx_name: str, desired: dict[Path, Project]
) -> None:
    console.print(f"Creating solution at {slnx_path}")
    if not _create_empty_slnx(console, config, slnx_name):
        return
    console.print("Adding projects to solution...")
    for path in desired:
        _sln_add(console, slnx_path, path)


def sync_slnx_file(console: Console, config: Config, slnx_name: str, framework: str | None) -> bool:
    """Sync a solution file so it contains exactly the desired projects.

    If the file already exists, adds missing projects and removes extra ones
    without recreating it. Creates from scratch if missing or malformed.

    Returns True if the solution file exists and is ready to use, False otherwise.
    """
    console.print(f"Syncing solution file: {slnx_name}")
    slnx_path = config.repodir / slnx_name

    if slnx_path.exists():
        _update_existing_slnx(console, config, slnx_path, slnx_name, framework)
        return True
    desired = _resolve_desired_projects(console, config, framework)
    if not desired:
        console.print("[yellow]No projects found for the specified framework[/yellow]")
        return False
    _create_slnx_from_scratch(console, config, slnx_path, slnx_name, desired)
    return True


def run(
    console: Console, config: Config, args: list[str], *, summarize_warnings: bool = False
) -> int:
    """Execute dotnet commands across all projects.

    Args:
        console: Rich console instance for output
        config: PACE configuration
        args: Additional arguments to pass to dotnet (first arg is the dotnet subcommand)
        summarize_warnings: When True, parse build output after completion and print warning tables

    Returns:
        Exit code from the dotnet command (0 for success, non-zero for failure)
    """
    if not args:
        console.print("[red]Error: No dotnet command specified[/red]")
        console.print("Usage: pace dotnet <command> [options]")
        console.print("Example: pace dotnet build -c Release")
        return 1

    dotnet_cmd = args[0]
    dotnet_args = args[1:]

    # Extract framework from arguments
    framework = get_framework_from_args(args)

    # Use a single solution file for all platforms
    slnx_name = "PACE.slnx"
    slnx_path = config.repodir / slnx_name

    if not sync_slnx_file(console, config, slnx_name, framework):
        return 1  # No projects found for the framework

    console.print(f"Running: dotnet {dotnet_cmd} {slnx_name}")
    cmd = ["dotnet", dotnet_cmd, str(slnx_path), *dotnet_args]

    if not summarize_warnings:
        result = subprocess.run(cmd, capture_output=False, text=True, check=False)
        return result.returncode

    # Stream output live while capturing it for post-build warning analysis
    captured: list[str] = []
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert process.stdout is not None
    for line in process.stdout:
        console.out(line, end="")
        captured.append(line)
    process.wait()

    _print_warning_tables(console, config, captured)
    return process.returncode
