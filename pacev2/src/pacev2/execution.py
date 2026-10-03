# Copyright (c) 2026

"""Reusable parallel command execution with live, per-project output."""

import subprocess
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from threading import Lock

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from pacev2.monitor import Monitor

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


def _progress_table(
    tasks: Sequence[Task],
    progress: list[_Progress],
    title: str,
    lock: Lock,
) -> Table:
    colors = {
        TaskStatus.QUEUED: "dim",
        TaskStatus.SUCCEEDED: "green",
        TaskStatus.FAILED: "red",
        TaskStatus.SKIPPED: "yellow",
    }

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
            result.add_row(Text(task.name), status, detail)
    return result


def _execute_task(
    task: Task,
    progress: _Progress,
    lock: Lock,
    monitor: Monitor | None,
) -> TaskResult:
    reported = False

    def report(line: str) -> None:
        nonlocal reported
        reported = True
        if monitor:
            monitor.log(line, task.name)
            monitor.project(task.name, detail=line)
        with lock:
            progress.detail = line

    with lock:
        progress.status = TaskStatus.RUNNING
    if monitor:
        monitor.project(task.name, status="running")
    try:
        result = task.action(report)
    except (OSError, ValueError) as error:
        result = TaskResult(TaskStatus.FAILED, str(error))
        report(str(error))

    detail = result.output.rstrip().splitlines()
    message = detail[-1] if detail else "No output"
    if result.status == TaskStatus.FAILED and result.returncode is not None:
        message = f"Exit {result.returncode}: {message}"
    with lock:
        progress.status = result.status
        progress.detail = message
    if monitor:
        if not reported and result.output:
            monitor.log(result.output.rstrip(), task.name)
        monitor.project(task.name, status=result.status.value.lower(), detail=message)
    return result


def run_parallel(
    tasks: Sequence[Task],
    console: Console,
    *,
    title: str = "Projects",
    max_workers: int | None = None,
    monitor: Monitor | None = None,
) -> list[TaskResult]:
    """Run independent tasks, keeping live updates and final output separate."""
    if not tasks:
        if monitor:
            monitor.log("No projects selected.")
        else:
            console.print("No projects selected.", style="yellow")
        return []

    if monitor:
        for task in tasks:
            monitor.project(task.name)
    progress = [_Progress() for _ in tasks]
    lock = Lock()

    results: dict[int, TaskResult] = {}
    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = {}
    try:
        with (
            nullcontext()
            if monitor
            else Live(
                console=console,
                get_renderable=lambda: _progress_table(tasks, progress, title, lock),
                refresh_per_second=8,
                transient=True,
            )
        ):
            futures = {
                executor.submit(_execute_task, task, progress[index], lock, monitor): index
                for index, task in enumerate(tasks)
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()
    finally:
        for future in futures:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)

    ordered = [results[index] for index in range(len(tasks))]
    if not monitor:
        console.print(_progress_table(tasks, progress, title, lock))
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
