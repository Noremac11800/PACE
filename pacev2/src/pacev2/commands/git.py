"""Arbitrary Git commands across the selected project checkouts."""

import os
import shutil
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from typer.core import TyperCommand

from pacev2._context import configure
from pacev2.execution import (
    Reporter,
    Task,
    TaskResult,
    TaskStatus,
    run_command,
    run_parallel,
)
from pacev2.models import Config, Project
from pacev2.paths import project_directory

if TYPE_CHECKING:
    from typer._click.core import Context


class GitCommand(TyperCommand):
    def parse_args(self, ctx: "Context", args: list[str]) -> list[str]:
        # Prevent Click from splitting Git options such as -Cpath into short flags.
        if args and args[0] not in {"-h", "--help", "--"}:
            args = ["--", *args]
        return super().parse_args(ctx, args)


def _command_index(args: list[str]) -> int | None:
    value_options = {
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--config-env",
        "--super-prefix",
        "--attr-source",
    }
    skip_value = False
    for index, argument in enumerate(args):
        if skip_value:
            skip_value = False
        elif argument in value_options:
            skip_value = True
        elif argument in {
            "--version",
            "--help",
            "-v",
            "-h",
            "--exec-path",
            "--html-path",
            "--man-path",
            "--info-path",
        }:
            return None
        elif not argument.startswith("-"):
            return index
    return None


def _is_checkout(path: Path) -> bool:
    return (path / ".git").exists() or ((path / "HEAD").is_file() and (path / "objects").is_dir())


def _run_project(
    project: Project,
    repodir: Path,
    args: list[str],
    executable: str | None,
    env: dict[str, str],
    report: Reporter,
) -> TaskResult:
    if not project.repo_url or not project.repo_url.strip():
        return TaskResult(TaskStatus.SKIPPED, "Warning: no repo_url configured.")

    directory = project_directory(repodir, project.name)
    command_index = _command_index(args)
    cloning = command_index is not None and args[command_index] == "clone"
    if cloning and _is_checkout(directory):
        return TaskResult(TaskStatus.SKIPPED, f"Already cloned: {directory}")
    if not cloning:
        try:
            directory.stat()
        except FileNotFoundError:
            return TaskResult(
                TaskStatus.SKIPPED,
                f"Warning: not cloned at {directory}. Run 'pacev2 git clone' first.",
            )
        if not directory.is_dir() or not _is_checkout(directory):
            return TaskResult(TaskStatus.FAILED, f"Not a Git checkout: {directory}")
    if executable is None:
        return TaskResult(TaskStatus.FAILED, "Git executable not found on PATH.")

    command = [executable, "--no-pager", *args]
    if cloning:
        directory.parent.mkdir(parents=True, exist_ok=True)
        if args[-1] != "--":
            command.append("--")
        command.extend([project.repo_url, str(directory)])
    return run_command(
        command,
        directory.parent if cloning else directory,
        report,
        env={**env, "GIT_CEILING_DIRECTORIES": str(directory.resolve().parent)},
    )


def run(
    ctx: typer.Context,
    git_args: Annotated[
        list[str] | None,
        typer.Argument(
            metavar="... <git-args>",
            help="Git command and arguments (e.g., 'pull', 'clone', or 'checkout main')",
        ),
    ] = None,
) -> None:
    """Execute git commands across all repositories."""
    if not git_args:
        raise typer.BadParameter(
            "Provide a Git command or options, such as 'status' or 'clone'.",
            param_hint="<git-args>",
        )
    configure(ctx, required=True)
    config = ctx.find_object(Config)
    if config is None:
        raise RuntimeError("No active configuration in the CLI context")

    executable = shutil.which("git")
    env = {
        **os.environ,
        "GIT_PAGER": "",
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "never",
        "GIT_EDITOR": "false",
        "GIT_SEQUENCE_EDITOR": "false",
    }
    tasks = [
        Task(
            project.name,
            partial(_run_project, project, config.repodir, git_args, executable, env),
        )
        for project in config.projects
    ]
    results = run_parallel(tasks, Console(), title="Git")
    if any(result.status == TaskStatus.FAILED for result in results):
        raise typer.Exit(code=1)
