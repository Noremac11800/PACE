"""pace dotnet command - Execute dotnet commands across the project graph."""

import subprocess
from pathlib import Path

from rich.console import Console

from pace.config import Config, Project


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


def is_target_platform_supported(project_path: Path, platform: str) -> bool:
    """Check if a project supports iOS by examining its csproj file."""
    result = subprocess.run(
        ["dotnet", "msbuild", str(project_path), "-getProperty:TargetFrameworks"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project_path.parent,
    )
    if result.returncode != 0:
        return False
    target_frameworks = result.stdout.strip()
    return platform.lower() in target_frameworks.lower()


def filter_projects_by_framework(config: Config, framework: str) -> list[Project]:
    """Filter projects based on framework compatibility."""
    supported_projects: list[Project] = []
    for project in config.projects:
        project_path = config.repodir / project.name / project.csproj_path
        if is_target_platform_supported(project_path, framework):
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
    already_included: set[Path] | None = None,
) -> dict[Path, Project]:
    """Return {absolute_csproj_path: Project} for the projects to include.

    When already_included is provided, projects whose resolved path is in that
    set skip the expensive MSBuild framework check and are included directly.
    """
    desired: dict[Path, Project] = {}
    needs_check: list[tuple[Path, Project]] = []

    for project in config.projects:
        full_path = (config.repodir / project.name / project.csproj_path).resolve()
        if not full_path.exists():
            console.print(f"[yellow]Warning: Project file not found: {full_path}[/yellow]")
            continue
        if not framework:
            desired[full_path] = project
        elif already_included and full_path in already_included:
            desired[full_path] = project  # skip MSBuild check — already validated
        else:
            needs_check.append((full_path, project))

    for full_path, project in needs_check:
        project_path = config.repodir / project.name / project.csproj_path
        if is_target_platform_supported(project_path, framework):  # type: ignore[arg-type]
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

    # Pass existing paths so MSBuild is only called for projects not yet in the solution
    desired = _resolve_desired_projects(console, config, framework, already_included=existing)

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


def sync_slnx_file(console: Console, config: Config, slnx_name: str, framework: str | None) -> None:
    """Sync a solution file so it contains exactly the desired projects.

    If the file already exists, adds missing projects and removes extra ones
    without recreating it. Creates from scratch if missing or malformed.
    """
    console.print(f"Syncing solution file: {slnx_name}")
    slnx_path = config.repodir / slnx_name

    if slnx_path.exists():
        _update_existing_slnx(console, config, slnx_path, slnx_name, framework)
    else:
        desired = _resolve_desired_projects(console, config, framework)
        if not desired:
            console.print("[yellow]No projects found for the specified framework[/yellow]")
            return
        _create_slnx_from_scratch(console, config, slnx_path, slnx_name, desired)


def run(console: Console, config: Config, args: list[str]) -> None:
    """Execute dotnet commands across all projects.

    Args:
        console: Rich console instance for output
        config: PACE configuration
        args: Additional arguments to pass to dotnet
    """
    # Extract framework from arguments
    framework = get_framework_from_args(args)

    # Determine solution file name based on framework
    slnx_name = f"PACE_Temp.{framework}.slnx" if framework else "PACE_Temp.slnx"
    slnx_path = config.repodir / slnx_name

    sync_slnx_file(console, config, slnx_name, framework)

    # Build the solution
    console.print("Building solution...")
    build_cmd = ["dotnet", "build", str(slnx_path), *args]
    build_result = subprocess.run(build_cmd, capture_output=False, text=True, check=False)

    if build_result.stdout:
        console.print(build_result.stdout)
    if build_result.stderr:
        console.print(build_result.stderr, style="red")

    if build_result.returncode == 0:
        console.print("[green]Build succeeded![/green]")
    else:
        console.print(f"[red]Build failed with exit code {build_result.returncode}[/red]")

    # Clean up solution file
    # if slnx_path.exists():
    #     slnx_path.unlink()
    #     console.print(f"Cleaned up solution file: {slnx_name}")
