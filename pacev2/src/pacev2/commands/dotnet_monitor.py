# Copyright (c) 2026

"""Observe real MSBuild events without changing the project's build graph."""

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from pathlib import Path
from queue import Empty, Queue
from tempfile import TemporaryDirectory
from typing import TextIO

from pacev2.execution import TaskResult, run_command
from pacev2.models import Project
from pacev2.monitor import Monitor

_MIN_SDK_MAJOR = 9


def _logger(executable: str, monitor: Monitor) -> Path:
    sdk = run_command([executable, "--version"], Path.cwd(), lambda _: None)
    if sdk.returncode != 0:
        raise ValueError(f"Could not determine the .NET SDK:\n{sdk.output}")
    version = sdk.output.strip()
    major = version.split(".")[0]
    if not major.isdigit() or int(major) < _MIN_SDK_MAJOR:
        raise ValueError(f"Monitoring requires .NET SDK 9 or newer; found {version}.")
    sources = {
        name: files("pacev2.data").joinpath("monitor", name).read_bytes()
        for name in ("Monitor.csproj", "MonitorLogger.cs")
    }
    key = hashlib.sha256(version.encode() + b"".join(sources.values())).hexdigest()[:20]
    cache = Path.home() / ".pace" / "cache" / "msbuild-monitor" / key
    assembly = cache / "Pace.Monitor.dll"
    if assembly.is_file():
        return assembly
    monitor.log(f"Preparing MSBuild monitor for SDK {version} (cached after first use).")
    cache.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="compile-", dir=cache) as temporary:
        directory = Path(temporary)
        for name, content in sources.items():
            (directory / name).write_bytes(content)
        result = run_command(
            [
                executable,
                "build",
                str(directory / "Monitor.csproj"),
                "-o",
                str(directory / "out"),
                f"-p:PaceMonitorSdkMajor={major}",
                f"-p:RestoreSources={directory}",
                "-p:ImportDirectoryBuildProps=false",
                "-p:ImportDirectoryBuildTargets=false",
                "-p:ImportDirectoryPackagesProps=false",
                "--nologo",
                "-v:q",
            ],
            Path.cwd(),
            monitor.log,
            env={
                **os.environ,
                "DOTNET_GENERATE_ASPNET_CERTIFICATE": "false",
                "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
                "DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE": "true",
            },
        )
        if result.returncode != 0:
            raise ValueError(f"Could not compile the MSBuild monitor:\n{result.output}")
        try:
            (directory / "out" / assembly.name).rename(assembly)
        except FileExistsError:
            # Windows will not replace a logger already cached by another invocation.
            return assembly
    return assembly


class BuildProgress:
    """Aggregate repeated/multi-target project evaluations, retaining failed stages."""

    def __init__(self, monitor: Monitor, operation: str) -> None:
        """Track stage instances separately across MSBuild execution contexts."""
        self.monitor = monitor
        self.operation = operation
        self.ready = False
        self.failed: set[str] = set()
        self.stages: dict[tuple[str, str], dict[str, str]] = {}

    def accept(self, event: dict[str, object]) -> None:
        """Apply an event from the bundled logger."""
        kind = event["kind"]
        if kind == "ready":
            self.ready = True
            return
        path = event["project"]
        if not isinstance(path, str) or Path(path).suffix.lower() not in {
            ".csproj",
            ".fsproj",
            ".vbproj",
        }:
            return
        project_id = str(Path(path).resolve())
        if kind == "project_finished":
            if event["succeeded"] is False:
                self.failed.add(project_id)
            return
        if kind == "project_started":
            project = self.monitor.projects.get(project_id)
            self.monitor.project(
                project_id,
                name=Path(path).stem,
                path=project_id,
                status="running",
                detail=(
                    "Evaluating project / waiting for targets."
                    if project is None or not project.stages
                    else None
                ),
            )
            return
        stage, context = event["stage"], event["context"]
        if not isinstance(stage, str) or not isinstance(context, str):
            raise TypeError("Invalid MSBuild monitor stage event.")
        instances = self.stages.setdefault((project_id, stage), {})
        instances[context] = (
            "running"
            if kind == "stage_started"
            else "succeeded"
            if event["succeeded"]
            else "failed"
        )
        status = (
            "failed"
            if "failed" in instances.values()
            else "running"
            if "running" in instances.values()
            else "succeeded"
        )
        if status == "failed":
            self.failed.add(project_id)
        self.monitor.project(
            project_id,
            name=Path(path).stem,
            path=project_id,
            status="running",
            stage=stage,
            stage_status=status,
            detail=f"{stage.capitalize()}: {status}",
        )

    def finish(self) -> None:
        """Confirm final project outcomes only after all SDK work has ended."""
        if not self.ready:
            raise ValueError(
                "MSBuild did not initialize the monitor; project progress is unavailable."
            )
        for project_id in self.monitor.projects:
            instances = self.stages.get((project_id, self.operation), {})
            completed = bool(instances) and all(
                state == "succeeded" for state in instances.values()
            )
            if project_id in self.failed or completed:
                self.monitor.project(
                    project_id,
                    status="failed" if project_id in self.failed else "succeeded",
                    detail="Project failed."
                    if project_id in self.failed
                    else "Command target completed.",
                )


def _drain_events(stream: TextIO, progress: BuildProgress, pending: str) -> str:
    pending += stream.read()
    lines = pending.split("\n")
    line = ""
    try:
        for line in lines[:-1]:
            event = json.loads(line)
            progress.accept(event)
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(f"Invalid MSBuild monitor event: {line}") from error
    return lines[-1]


def execute_monitored(
    executable: str,
    args: list[str],
    selected: dict[Path, Project],
    monitor: Monitor,
) -> TaskResult:
    """Tail a private event file alongside stdout, including at quiet verbosity."""
    assembly = _logger(executable, monitor)
    for path, project in selected.items():
        monitor.project(str(path), name=project.name, path=str(path))
    progress = BuildProgress(monitor, args[0])
    with TemporaryDirectory(prefix="pace-monitor-") as temporary:
        events = Path(temporary) / "events.jsonl"
        events.touch()
        # Insert before VSTest's runsettings separator, never inside forwarded settings.
        index = args.index("--") if "--" in args else len(args)
        command = [
            executable,
            *args[:index],
            f"-logger:Pace.MonitorLogger,{assembly}",
            "-tl:off",
            *args[index:],
        ]
        output: Queue[str] = Queue()
        with events.open(encoding="utf-8") as stream, ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                run_command,
                command,
                Path.cwd(),
                output.put,
                env={**os.environ, "PACE_MONITOR_EVENTS": str(events)},
            )
            pending = ""
            while True:
                pending = _drain_events(stream, progress, pending)
                try:
                    monitor.log(output.get(timeout=0.03))
                except Empty:
                    if future.done():
                        break
            pending = _drain_events(stream, progress, pending)
            if pending:
                raise ValueError("MSBuild monitor ended with an incomplete event.")
            result = future.result()
        # A failed SDK invocation may exit before the logger is initialized.
        if progress.ready or not result.returncode:
            progress.finish()
        return result
