#!/usr/bin/env python3
"""Parses dotnet build output and summarizes warnings by code and description.

Usage:
    python summarize_build_warnings.py <build_output.txt>
"""

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table

WARNING_PATTERN = re.compile(r":\s+(?:\w+ )?warning (\w+):\s+(.+?)(?:\s+See https?://\S+)?\s*\[")
PROJECT_PATTERN = re.compile(r"\[([^\]]+\.csproj)")
EXPECTED_ARGS = 2


@dataclass
class WarningSummary:
    count: int = field(default=0)
    description: str = field(default="")


def parse_warnings(filepath: Path) -> tuple[dict[str, WarningSummary], dict[str, int]]:
    warnings: dict[str, WarningSummary] = defaultdict(WarningSummary)
    by_project: dict[str, int] = defaultdict(int)
    seen: set[str] = set()

    with filepath.open(encoding="utf-8") as f:
        for line in f:
            match = WARNING_PATTERN.search(line)
            if match:
                if line in seen:
                    continue
                seen.add(line)

                code = match.group(1)
                description = match.group(2).strip()
                warnings[code].count += 1
                warnings[code].description = description

                proj_match = PROJECT_PATTERN.search(line)
                if proj_match:
                    proj_path = proj_match.group(1)
                    proj_name = Path(proj_path).stem
                    by_project[proj_name] += 1

    return warnings, by_project


def print_table(warnings: dict[str, WarningSummary], by_project: dict[str, int]) -> None:
    console = Console()

    if not warnings:
        console.print("[yellow]No warnings found.[/yellow]")
        return

    sorted_warnings = sorted(warnings.items(), key=lambda x: x[1].count, reverse=True)

    by_code_table = Table(title="Warnings by Code", show_header=True, header_style="bold cyan")
    by_code_table.add_column("Code", style="bold yellow", no_wrap=True)
    by_code_table.add_column("Count", justify="right", style="bold red")
    by_code_table.add_column("Description")

    for code, data in sorted_warnings:
        by_code_table.add_row(code, str(data.count), data.description)

    console.print(by_code_table)

    sorted_projects = sorted(by_project.items(), key=lambda x: x[1], reverse=True)

    by_project_table = Table(
        title="Warnings by Project", show_header=True, header_style="bold cyan"
    )
    by_project_table.add_column("Project", style="bold blue")
    by_project_table.add_column("Count", justify="right", style="bold red")

    for proj, count in sorted_projects:
        by_project_table.add_row(proj, str(count))

    console.print(by_project_table)
    console.print(f"[bold]Total warnings:[/bold] {sum(v.count for v in warnings.values())}")


def main() -> None:
    if len(sys.argv) != EXPECTED_ARGS:
        print(f"Usage: python {sys.argv[0]} <build_output.txt>")
        sys.exit(1)

    warnings, by_project = parse_warnings(Path(sys.argv[1]))
    print_table(warnings, by_project)


if __name__ == "__main__":
    main()
