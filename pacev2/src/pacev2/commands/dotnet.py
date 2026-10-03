# Copyright (c) 2026

"""Run dotnet against a solution containing the selected configured projects."""

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.text import Text
from typer.core import TyperCommand

from pacev2._context import configure
from pacev2.commands.dotnet_monitor import execute_monitored
from pacev2.commands.dotnet_solution import sync_solution
from pacev2.commands.dotnet_warnings import print_warning_summary
from pacev2.execution import TaskResult, run_command
from pacev2.models import Config, Project
from pacev2.monitor import Monitor
from pacev2.paths import project_directory

if TYPE_CHECKING:
    from typer._click.core import Context


class DotnetCommand(TyperCommand):
    """Parse only leading PACE flags, preserving all forwarded dotnet arguments."""

    def parse_args(self, ctx: "Context", args: list[str]) -> list[str]:
        """Protect compact MSBuild options from Click's short-option parsing."""
        index = 0
        while index < len(args) and args[index] in {"-w", "--summarize-warnings"}:
            index += 1
        if index < len(args) and args[index] not in {"-h", "--help", "--"}:
            args = [*args[:index], "--", *args[index:]]
        return super().parse_args(ctx, args)


def _framework(args: list[str]) -> str | None:
    framework = None
    for index, argument in enumerate(args):
        if argument == "--":
            break
        if argument in {"-f", "--framework"}:
            if index + 1 == len(args) or args[index + 1].startswith("-"):
                raise ValueError(f"{argument} requires a target framework")
            framework = args[index + 1]
        elif argument.startswith("--framework="):
            framework = argument.partition("=")[2]
            if not framework:
                raise ValueError("--framework requires a target framework")
    return framework


def _evaluation_properties(args: list[str]) -> list[str]:
    """Evaluate conditional frameworks with the caller's configuration/properties."""
    properties: list[str] = []
    options = {
        "-c": "Configuration",
        "--configuration": "Configuration",
        "-r": "RuntimeIdentifier",
        "--runtime": "RuntimeIdentifier",
    }
    for index, argument in enumerate(args):
        if argument == "--":
            break
        if argument in options and index + 1 < len(args):
            properties.append(f"-p:{options[argument]}={args[index + 1]}")
        elif argument.startswith(("-p:", "/p:", "-property:", "/property:")):
            properties.append(argument)
        elif argument in {"-p", "--property"} and index + 1 < len(args):
            properties.append(f"-p:{args[index + 1]}")
        elif argument.startswith("--property:"):
            properties.append(f"-p:{argument.partition(':')[2]}")
        elif argument.startswith("--property="):
            properties.append(f"-p:{argument.partition('=')[2]}")
        else:
            option, separator, value = argument.partition("=")
            if separator and option in options:
                properties.append(f"-p:{options[option]}={value}")
    return properties


def _supports_framework(executable: str, path: Path, framework: str, properties: list[str]) -> bool:
    result = run_command(
        [
            executable,
            "msbuild",
            str(path),
            "-nologo",
            "-getProperty:TargetFramework,TargetFrameworks",
            *properties,
        ],
        path.parent,
        lambda _: None,
    )
    if result.returncode != 0:
        raise ValueError(f"Could not evaluate target frameworks for {path}:\n{result.output}")
    try:
        values = json.loads(result.output)["Properties"]
        frameworks = [values["TargetFramework"], *values["TargetFrameworks"].split(";")]
        return framework.casefold() in {value.strip().casefold() for value in frameworks}
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise ValueError(
            f"Invalid target-framework response for {path}:\n{result.output}"
        ) from error


def _selected_projects(
    config: Config,
    executable: str,
    args: list[str],
    console: Console,
    monitor: Monitor | None = None,
) -> dict[Path, Project]:
    framework = _framework(args)
    properties = _evaluation_properties(args)
    selected: dict[Path, Project] = {}
    for project in config.projects:
        path = (project_directory(config.repodir, project.name) / project.csproj_path).resolve()
        if monitor:
            monitor.project(str(path), name=project.name, path=str(path))
        try:
            path.stat()
        except FileNotFoundError:
            console.print(f"Warning: project file not found: {path}", style="yellow", markup=False)
            if monitor:
                monitor.project(str(path), status="skipped", detail="Project file not found.")
            continue
        if not path.is_file():
            raise ValueError(f"Project path is not a file: {path}")
        if framework and not _supports_framework(executable, path, framework, properties):
            console.print(
                f"Skipping {project.name}: does not target {framework}.",
                style="yellow",
                markup=False,
            )
            if monitor:
                monitor.project(str(path), status="skipped", detail=f"Does not target {framework}.")
            continue
        selected[path] = project
    return selected


def _execute(
    executable: str,
    args: list[str],
    console: Console,
    monitor: Monitor | None = None,
) -> TaskResult:
    return run_command(
        [executable, *args],
        Path.cwd(),
        monitor.log
        if monitor
        else lambda line: console.print(Text.from_ansi(line), soft_wrap=True),
    )


def _find_executable() -> str:
    executable = shutil.which("dotnet")
    if executable is None:
        raise ValueError("dotnet executable not found on PATH.")
    return executable


def _run_solution(
    ctx: typer.Context,
    args: list[str],
    console: Console,
    *,
    summarize_warnings: bool,
    monitor: Monitor | None = None,
) -> TaskResult | None:
    configure(ctx, required=True)
    config = ctx.find_object(Config)
    if config is None:
        raise RuntimeError("No active configuration in the CLI context")
    if not config.projects:
        console.print("No projects selected.", style="yellow")
        return None
    executable = _find_executable()
    selected = _selected_projects(
        config,
        executable,
        args,
        console,
        monitor if args[0] in {"build", "publish", "test"} else None,
    )
    if not selected:
        raise ValueError("No existing projects match the selected configuration and framework.")
    solution = sync_solution(config, selected)
    console.print(f"Solution: {solution} ({len(selected)} projects)", markup=False)
    console.print(f"Running dotnet {args[0]} against PACE.slnx", markup=False)
    command = [args[0], str(solution), *args[1:]]
    result = (
        execute_monitored(executable, command, selected, monitor)
        if monitor and args[0] in {"build", "publish", "test"}
        else _execute(executable, command, console, monitor)
    )
    if summarize_warnings:
        print_warning_summary(console, config, result.output)
    return result


def run(
    ctx: typer.Context,
    dotnet_args: Annotated[
        list[str] | None,
        typer.Argument(
            metavar="... <dotnet-args>",
            help="Arguments to pass to dotnet (e.g., 'build -c Release')",
        ),
    ] = None,
    summarize_warnings: Annotated[
        bool,
        typer.Option(
            "--summarize-warnings",
            "-w",
            help="After the command completes, print a warning summary by code and project",
        ),
    ] = False,
) -> None:
    """Sync PACE.slnx and let MSBuild execute the selected project graph."""
    if not dotnet_args:
        raise typer.BadParameter(
            "Provide a dotnet command, such as 'build' or 'test'.", param_hint="<dotnet-args>"
        )
    monitor = Monitor(f"dotnet.{dotnet_args[0]}") if ctx.meta.get("monitor") else None
    console = Console(stderr=monitor is not None)
    try:
        if dotnet_args[0] in {
            "--info",
            "--version",
            "--list-sdks",
            "--list-runtimes",
            "help",
        } or any(arg in {"--help", "-h", "-?"} for arg in dotnet_args):
            result = _execute(_find_executable(), dotnet_args, console, monitor)
        else:
            result = _run_solution(
                ctx,
                dotnet_args,
                console,
                summarize_warnings=summarize_warnings,
                monitor=monitor,
            )
    except typer.Exit as error:
        if monitor:
            monitor.finish(error.exit_code)
        raise
    except (OSError, ValueError) as error:
        if monitor:
            monitor.log(f"error: {error}")
            monitor.finish(1)
        else:
            typer.echo(f"error: {error}", err=True)
        raise typer.Exit(code=1) from error
    returncode = result.returncode if result and result.returncode else 0
    returncode = max(returncode, 1) if returncode else 0
    if monitor:
        monitor.finish(returncode)
    if returncode:
        raise typer.Exit(code=returncode)
