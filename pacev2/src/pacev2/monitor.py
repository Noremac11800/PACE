# Copyright (c) 2026

"""Versioned, flushed JSON Lines for consumers of long-running commands."""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import TextIO


@dataclass
class ProjectProgress:
    """Latest observed state of a project and its execution stages."""

    name: str
    path: str | None = None
    status: str = "queued"
    detail: str = ""
    stages: dict[str, str] = field(default_factory=dict)


class Monitor:
    """Emit ordered events, safely shared by concurrent project workers."""

    def __init__(self, command: str, stream: TextIO | None = None) -> None:
        """Start an event stream for one command invocation."""
        self.command = command
        self.stream = stream if stream is not None else sys.stdout
        self.projects: dict[str, ProjectProgress] = {}
        self._sequence = 0
        self._lock = RLock()
        self.emit("start")

    def emit(self, event: str, **fields: object) -> None:
        """Write one atomic JSON record and flush it before returning."""
        with self._lock:
            self._sequence += 1
            self.stream.write(
                json.dumps(
                    {
                        "protocol": "pace.monitor",
                        "version": 1,
                        "sequence": self._sequence,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "command": self.command,
                        "event": event,
                        **fields,
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )
            self.stream.flush()

    def project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        path: str | None = None,
        status: str | None = None,
        detail: str | None = None,
        stage: str | None = None,
        stage_status: str = "running",
    ) -> None:
        """Publish a complete project snapshot; stages are observed, not predicted."""
        with self._lock:
            if project_id not in self.projects:
                self.projects[project_id] = ProjectProgress(name or project_id, path)
            project = self.projects[project_id]
            if status is not None:
                project.status = status
            if detail is not None:
                project.detail = detail
            if stage is not None:
                project.stages[stage] = stage_status
            self.emit(
                "project",
                id=project_id,
                name=project.name,
                path=project.path,
                status=project.status,
                detail=project.detail,
                stages=project.stages,
            )

    def log(self, text: str, project_id: str | None = None) -> None:
        """Preserve human-readable diagnostics inside the event stream."""
        self.emit("log", text=text, project_id=project_id)

    def finish(self, returncode: int) -> None:
        """Settle unobserved work and publish the command result."""
        for project_id, project in self.projects.items():
            unfinished_stages = "running" in project.stages.values()
            for stage, status in project.stages.items():
                if status == "running":
                    project.stages[stage] = "incomplete"
            if project.status in {"queued", "running"}:
                self.project(
                    project_id,
                    status="incomplete" if returncode else "skipped",
                    detail=(
                        "Command ended before project completion was observed."
                        if returncode
                        else "No matching command target was executed."
                    ),
                )
            elif unfinished_stages:
                self.project(project_id)
        self.emit(
            "finish",
            status="failed" if returncode else "succeeded",
            returncode=returncode,
            counts={
                status: sum(project.status == status for project in self.projects.values())
                for status in ("succeeded", "failed", "skipped", "incomplete")
            },
        )
