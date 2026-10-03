# Copyright (c) 2026

"""Warning summaries for streamed MSBuild output, adapted from the original PACE command."""

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from pacev2.models import Config
from pacev2.paths import normalize_path, project_directory

_WARNING = re.compile(r"(?:^|:\s*)(?:\w+\s+)?warning\s+([\w-]+):\s*(.+)", re.IGNORECASE)
_PROJECT = re.compile(r"\s+\[([^\]]+\.(?:cs|fs|vb)proj)(?:::[^\]]*)?\]\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class BuildWarning:
    """One distinct warning diagnostic, excluding MSBuild's repeated summary."""

    code: str
    description: str
    project: str
    repository: str


def parse_warnings(config: Config, output: str) -> list[BuildWarning]:
    """Attribute diagnostics by full project path, including projects inside repositories."""
    repositories = {
        project_directory(config.repodir, project.name): project.name for project in config.projects
    }
    warnings: list[BuildWarning] = []
    seen: set[str] = set()
    for raw in output.splitlines():
        line = re.sub(r"^\s*\d+>", "", Text.from_ansi(raw).plain).strip()
        match = _WARNING.search(line)
        if match is None or line in seen:
            continue
        seen.add(line)
        description = match[2]
        project_match = _PROJECT.search(description)
        project_name, repository = "Unknown project", "Unknown repository"
        if project_match:
            path = normalize_path(project_match[1]).resolve()
            directory = config.repodir.resolve()
            project_name = (
                path.relative_to(directory).as_posix()
                if path.is_relative_to(directory)
                else path.as_posix()
            )
            repository = next(
                (
                    name
                    for directory, name in repositories.items()
                    if path.is_relative_to(directory)
                ),
                repository,
            )
            description = description[: project_match.start()].strip()
        warnings.append(BuildWarning(match[1], description, project_name, repository))
    return warnings


def _table(title: str, columns: list[str], rows: list[list[str]]) -> Table:
    table = Table(title=Text(title), header_style="bold cyan")
    for column in columns:
        table.add_column(column, justify="right" if column == "Count" else "left")
    for row in rows:
        table.add_row(*(Text(cell) for cell in row))
    return table


def _tables(warnings: list[BuildWarning]) -> list[Table]:
    by_code = Counter(warning.code for warning in warnings)
    by_project = Counter((warning.repository, warning.project) for warning in warnings)
    descriptions = {warning.code: warning.description for warning in reversed(warnings)}
    tables = [
        _table(
            "Warnings by code",
            ["Code", "Count", "Example description"],
            [[code, str(count), descriptions[code]] for code, count in by_code.most_common()],
        ),
        _table(
            "Warnings by project",
            ["Project", "Repository", "Count"],
            [
                [project, repository, str(count)]
                for (repository, project), count in by_project.most_common()
            ],
        ),
    ]
    by_repository = Counter(warning.repository for warning in warnings)
    for repository, total in by_repository.most_common():
        counts = Counter(
            (warning.project, warning.code)
            for warning in warnings
            if warning.repository == repository
        )
        tables.append(
            _table(
                f"{repository} ({total} warnings)",
                ["Project", "Code", "Count"],
                [[project, code, str(count)] for (project, code), count in counts.most_common()],
            )
        )
    return tables


def print_warning_summary(console: Console, config: Config, output: str) -> None:
    """Print warning tables and save the same summary under ~/.pace/logs."""
    warnings = parse_warnings(config, output)
    if not warnings:
        console.print("No warnings found.", style="yellow")
        return
    tables = _tables(warnings)
    timestamp = datetime.now().astimezone()
    log = Console(file=StringIO(), record=True, width=100, color_system=None)
    log.print("PACE WARNING SUMMARY")
    log.print(f"Generated: {timestamp.isoformat()}")
    for table in tables:
        console.print(table)
        log.print(table)
    total = f"Total warnings: {len(warnings)}"
    console.print(total)
    log.print(total)
    try:
        directory = Path.home() / ".pace" / "logs"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"warnings-{timestamp:%Y%m%d-%H%M%S-%f}.log"
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(log.export_text())
    except OSError as error:
        console.print(f"Could not write warning summary log: {error}", style="yellow", markup=False)
        return
    console.print(f"Warning summary log: {path}", markup=False)
