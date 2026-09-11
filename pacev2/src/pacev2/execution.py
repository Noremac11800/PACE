# Copyright (c) 2026

"""Reusable parallel command execution with live, per-project output."""

import subprocess
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from threading import Lock

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

Reporter = Callable[[str], None]


class TaskStatus(StrEnum):
    """Lifecycle states displayed for a project task."""

    QUEUED = "Queued"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    SKIPPED = "Skipped"


@dataclass(frozen=True)
class TaskResult:
    """Outcome and combined output of a project task."""

    status: TaskStatus
    output: str = ""
    returncode: int | None = None


@dataclass(frozen=True)
class Task:
    """Named project operation that reports progress while running."""

    name: str
    action: Callable[[Reporter], TaskResult]


@dataclass
class _Progress:
    status: TaskStatus = TaskStatus.QUEUED
    detail: str = ""
    spinner: Spinner = field(default_factory=lambda: Spinner("dots", text="Running", style="cyan"))


def run_command(
    args: Sequence[str],
    cwd: Path,
    report: Reporter,
    *,
    env: Mapping[str, str] | None = None,
) -> TaskResult:
    """Stream merged stdout/stderr without invoking a shell or reading stdin."""
    output: list[str] = []
    with subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    ) as process:
        assert process.stdout is not None
        for line in process.stdout:
            output.append(line)
            if line.strip():
                report(line.rstrip("\r\n"))
        returncode = process.wait()

    return TaskResult(
        TaskStatus.SUCCEEDED if returncode == 0 else TaskStatus.FAILED,
        "".join(output),
        returncode,
    )


def run_parallel(
    tasks: Sequence[Task],
    console: Console,
    *,
    title: str = "Projects",
    max_workers: int | None = None,
) -> list[TaskResult]:
    """Run independent tasks, keeping live updates and final output separate."""
    if not tasks:
        console.print("No projects selected.", style="yellow")
        return []

    progress = [_Progress() for _ in tasks]
    lock = Lock()
    colors = {
        TaskStatus.QUEUED: "dim",
        TaskStatus.SUCCEEDED: "green",
        TaskStatus.FAILED: "red",
        TaskStatus.SKIPPED: "yellow",
    }

    def table() -> Table:
        result = Table(title=Text(title))
        result.add_column("Project", style="bold")
        result.add_column("Status")
        result.add_column("Latest output", ratio=1)
        with lock:
            finished = sum(
                item.status not in {TaskStatus.QUEUED, TaskStatus.RUNNING} for item in progress
            )
            result.caption = f"{finished}/{len(tasks)} finished"
            for task, item in zip(tasks, progress, strict=True):
                status = (
                    item.spinner
                    if item.status == TaskStatus.RUNNING
                    else Text(item.status, style=colors[item.status])
                )
                detail = Text.from_ansi(item.detail)
                detail.no_wrap = True
                detail.overflow = "ellipsis"
                result.add_row(
                    Text(task.name),
                    status,
                    detail,
                )
        return result

    def execute(index: int, task: Task) -> TaskResult:
        def report(line: str) -> None:
            with lock:
                progress[index].detail = line

        with lock:
            progress[index].status = TaskStatus.RUNNING
        try:
            result = task.action(report)
        except (OSError, ValueError) as error:
            result = TaskResult(TaskStatus.FAILED, str(error))

        detail = result.output.rstrip().splitlines()
        message = detail[-1] if detail else "No output"
        if result.status == TaskStatus.FAILED and result.returncode is not None:
            message = f"Exit {result.returncode}: {message}"
        with lock:
            progress[index].status = result.status
            progress[index].detail = message
        return result

    results: dict[int, TaskResult] = {}
    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = {}
    try:
        with Live(
            console=console,
            get_renderable=table,
            refresh_per_second=8,
            transient=True,
        ):
            futures = {
                executor.submit(execute, index, task): index for index, task in enumerate(tasks)
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()
    finally:
        for future in futures:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)

    console.print(table())
    ordered = [results[index] for index in range(len(tasks))]
    _print_results(tasks, ordered, console)
    return ordered


def _print_results(tasks: Sequence[Task], results: Sequence[TaskResult], console: Console) -> None:
    for task, result in zip(tasks, results, strict=True):
        if result.output.strip():
            console.rule(Text(task.name))
            console.print(Text.from_ansi(result.output.rstrip()), soft_wrap=True)
    counts = {
        status: sum(result.status == status for result in results)
        for status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.SKIPPED)
    }
    console.print(
        f"{counts[TaskStatus.SUCCEEDED]} succeeded, "
        f"{counts[TaskStatus.FAILED]} failed, {counts[TaskStatus.SKIPPED]} skipped."
    )
