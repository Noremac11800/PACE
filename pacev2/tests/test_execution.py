"""Reusable runner coverage without touching real project repositories."""

import json
import sys
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

import pytest
from rich.console import Console
from rich.table import Table

from pacev2.execution import (
    Reporter,
    Task,
    TaskResult,
    TaskStatus,
    run_command,
    run_parallel,
)


def test_tasks_run_concurrently_and_results_keep_input_order() -> None:
    barrier = Barrier(2, timeout=10)
    output = StringIO()

    def action(report: Reporter) -> TaskResult:
        report("Working")
        barrier.wait()
        return TaskResult(TaskStatus.SUCCEEDED, "Finished", 0)

    results = run_parallel(
        [Task("first", action), Task("second", action)],
        Console(file=output, width=160),
        max_workers=2,
    )

    assert len(results) == 2
    assert all(result.status == TaskStatus.SUCCEEDED for result in results)
    assert "2/2 finished" in output.getvalue()
    assert "2 succeeded, 0 failed, 0 skipped" in output.getvalue()
    assert output.getvalue().index("first") < output.getvalue().index("second")


def test_live_table_displays_reported_output_before_completion() -> None:
    render: list[Callable[[], Table]] = []
    snapshots: list[str] = []

    def capture_table(
        *,
        console: Console,
        get_renderable: Callable[[], Table],
        refresh_per_second: int,
        transient: bool,
    ) -> None:
        render.append(get_renderable)

    def action(report: Reporter) -> TaskResult:
        report("Working on [red]literal text")
        snapshot = StringIO()
        Console(file=snapshot, width=160).print(render[0]())
        snapshots.append(snapshot.getvalue())
        return TaskResult(TaskStatus.SUCCEEDED, "All done", 0)

    with patch("pacev2.execution.Live") as live:
        live.side_effect = lambda **kwargs: capture_table(**kwargs) or live.return_value
        run_parallel([Task("project", action)], Console(file=StringIO(), width=160))

    assert "Running" in snapshots[0]
    assert "Working on [red]literal text" in snapshots[0]
    assert "0/1 finished" in snapshots[0]


def test_failures_are_reported_without_losing_other_results(tmp_path: Path) -> None:
    output = StringIO()

    def missing(report: Reporter) -> TaskResult:
        return run_command([str(tmp_path / "missing-executable")], tmp_path, report)

    def success(report: Reporter) -> TaskResult:
        report("Complete")
        return TaskResult(TaskStatus.SUCCEEDED, "Other project succeeded", 0)

    results = run_parallel(
        [Task("missing", missing), Task("working", success)],
        Console(file=output, width=160),
    )

    assert [result.status for result in results] == [
        TaskStatus.FAILED,
        TaskStatus.SUCCEEDED,
    ]
    assert results[0].output
    assert "Other project succeeded" in output.getvalue()
    assert "1 succeeded, 1 failed, 0 skipped" in output.getvalue()


def test_empty_selection_reports_no_work() -> None:
    output = StringIO()

    with patch("pacev2.execution.ThreadPoolExecutor") as executor:
        results = run_parallel([], Console(file=output))

    assert results == []
    executor.assert_not_called()
    assert "No projects selected" in output.getvalue()


def test_nonzero_exit_keeps_complete_output(tmp_path: Path) -> None:
    reported: list[str] = []
    script = (
        "import sys; print('first line', flush=True); "
        "print('[red]error detail', file=sys.stderr, flush=True); "
        "print('last line', flush=True); sys.exit(7)"
    )

    result = run_command([sys.executable, "-c", script], tmp_path, reported.append)

    assert result.status == TaskStatus.FAILED
    assert result.returncode == 7
    assert reported == ["first line", "[red]error detail", "last line"]
    assert result.output == "first line\n[red]error detail\nlast line\n"


def test_failed_exit_code_and_full_output_are_visible() -> None:
    output = StringIO()

    def action(report: Reporter) -> TaskResult:
        return TaskResult(TaskStatus.FAILED, "First error\nLast error\n", 128)

    run_parallel([Task("project", action)], Console(file=output, width=160))

    assert "Exit 128" in output.getvalue()
    assert "First error\nLast error" in output.getvalue()
    assert "0 succeeded, 1 failed, 0 skipped" in output.getvalue()


def test_command_preserves_arguments_without_a_shell(tmp_path: Path) -> None:
    arguments = ["with spaces", "[red]literal", "x; echo not-a-shell", "$(not-a-shell)"]

    result = run_command(
        [
            sys.executable,
            "-c",
            "import json, sys; print(json.dumps(sys.argv[1:]))",
            *arguments,
        ],
        tmp_path,
        lambda _: None,
    )

    assert result.status == TaskStatus.SUCCEEDED
    assert json.loads(result.output) == arguments


def test_output_is_delivered_before_the_process_exits(tmp_path: Path) -> None:
    acknowledgement = tmp_path / "acknowledged"
    script = """
import sys
import time
from pathlib import Path

print('ready', flush=True)
deadline = time.monotonic() + 10
while not Path(sys.argv[1]).exists():
    if time.monotonic() > deadline:
        sys.exit(9)
    time.sleep(0.01)
print('finished', flush=True)
"""

    def report(line: str) -> None:
        if line == "ready":
            acknowledgement.touch()

    result = run_command([sys.executable, "-c", script, str(acknowledgement)], tmp_path, report)

    assert result.returncode == 0
    assert result.output == "ready\nfinished\n"


def test_invalid_output_bytes_do_not_crash_the_runner(tmp_path: Path) -> None:
    result = run_command(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'bad: \\xff\\n')"],
        tmp_path,
        lambda _: None,
    )

    assert result.status == TaskStatus.SUCCEEDED
    assert "bad: \ufffd" in result.output


def test_stdin_is_closed_for_batch_commands(tmp_path: Path) -> None:
    result = run_command(
        [sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"],
        tmp_path,
        lambda _: None,
    )

    assert result.returncode == 0
    assert result.output == "''\n"


def test_unexpected_programming_errors_are_not_hidden() -> None:
    def broken(report: Reporter) -> TaskResult:
        raise RuntimeError("Programming error")

    with pytest.raises(RuntimeError, match="Programming error"):
        run_parallel([Task("broken", broken)], Console(file=StringIO()))
