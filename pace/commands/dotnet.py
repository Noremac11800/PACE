"""pace dotnet command - Execute dotnet commands across the project graph."""

import subprocess

from rich.console import Console

from pace.config import Config


def run(console: Console, config: Config, args: list[str]) -> None:
    """Execute dotnet commands across all projects.

    Args:
        console: Rich console instance for output
        config: PACE configuration
        args: Additional arguments to pass to dotnet
    """
    # Create a temporary solution file in the repodir
    slnx_name = "PACE_Temp-dev.slnx"
    slnx_path = config.repodir / slnx_name

    console.print(f"Creating temporary solution at {slnx_path}")

    # Create new solution file using dotnet command
    console.print("Creating solution file...")
    cmd = [
        "dotnet",
        "new",
        "sln",
        "-n",
        slnx_name.split(".", maxsplit=1)[0],
        "-o",
        str(config.repodir),
        "--force",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        console.print(f"[red]Failed to create solution: {result.stderr}[/red]")
        return

    console.print(f"Solution created at: {slnx_path}")

    # Add all projects to the solution
    console.print("Adding projects to solution...")
    for project in config.projects:
        project_full_path = config.repodir / project.name / project.csproj_path
        if project_full_path.exists():
            console.print(
                f"Adding {project.name} at {project_full_path} to solution at {slnx_path}"
            )
            cmd = ["dotnet", "sln", str(slnx_path), "add", str(project_full_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                console.print(f"[red]Failed to add {project.name}: {result.stderr}[/red]")
            else:
                console.print(f"[green]Added {project.name}[/green]")
        else:
            console.print(f"[yellow]Warning: Project file not found: {project_full_path}[/yellow]")

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
