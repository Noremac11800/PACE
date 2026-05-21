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


def create_slnx_file(
    console: Console, config: Config, slnx_name: str, framework: str | None
) -> None:
    """Create a solution file for the given projects."""
    slnx_path = config.repodir / slnx_name
    console.print(f"Creating solution at {slnx_path}")

    # Filter projects based on framework
    if framework:
        projects_to_include = filter_projects_by_framework(config, framework)
        console.print(f"Found {len(projects_to_include)} projects compatible with {framework}")
    else:
        projects_to_include = config.projects
        console.print(f"Found {len(projects_to_include)} total projects")

    if not projects_to_include:
        console.print("[yellow]No projects found for the specified framework[/yellow]")
        return

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
        return

    # Add filtered projects to the solution
    console.print("Adding projects to solution...")
    for project in projects_to_include:
        project_full_path = config.repodir / project.name / project.csproj_path
        if project_full_path.exists():
            cmd = ["dotnet", "sln", str(slnx_path), "add", str(project_full_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                console.print(f"[red]Failed to add {project.name}: {result.stderr}[/red]")
        else:
            console.print(f"[yellow]Warning: Project file not found: {project_full_path}[/yellow]")


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

    if not slnx_path.exists():
        create_slnx_file(console, config, slnx_name, framework)

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
