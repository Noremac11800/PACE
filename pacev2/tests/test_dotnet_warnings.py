"""MSBuild warning attribution, deduplication, and persistent summaries."""

from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pacev2.commands.dotnet_warnings import parse_warnings, print_warning_summary
from pacev2.models import Config, Project
from rich.console import Console


def _config(tmp_path: Path) -> Config:
    return Config(
        repodir=tmp_path,
        projects=[
            Project(name="one", csproj_path=Path("Shared.csproj")),
            Project(name="two", csproj_path=Path("Shared.csproj")),
        ],
    )


def test_warning_codes_and_project_paths_are_not_collapsed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    first = f"file.cs(1,2): warning CS0168: Variable 'x' unused [{tmp_path}/one/Shared.csproj]"
    second = f"file.cs(1,2): warning CS0168: Variable 'x' unused [{tmp_path}/two/Shared.csproj]"
    third = f"file.cs(1,2): warning CA1848: Use LoggerMessage [red]literal [{tmp_path}/one/Other.csproj::TargetFramework=net10.0]"
    warnings = parse_warnings(
        config, f"{first}\n{second}\n1>{first}\n\x1b[33m{third}\x1b[0m\n"
    )
    assert len(warnings) == 3
    assert [warning.repository for warning in warnings] == ["one", "two", "one"]
    assert warnings[2].description == "Use LoggerMessage [red]literal"
    assert warnings[0].project != warnings[1].project


def test_warnings_without_project_paths_are_still_reported(tmp_path: Path) -> None:
    warnings = parse_warnings(
        _config(tmp_path),
        "CSC : warning CS2008: No source files specified.\nwarning NU1901: Package vulnerability\nerror CS1000: Not a warning\n",
    )
    assert [warning.code for warning in warnings] == ["CS2008", "NU1901"]
    assert warnings[0].repository == "Unknown repository"


def test_summary_logs_are_plain_text_and_do_not_overwrite(
    tmp_path: Path, isolated_home: Path
) -> None:
    config = _config(tmp_path)
    output = StringIO()
    warning = (
        f"file.cs(1,1): warning CS0168: [red]unused [{tmp_path}/one/Shared.csproj]"
    )
    for _ in range(2):
        print_warning_summary(Console(file=output, width=160), config, warning)
    logs = list((isolated_home / ".pace/logs").glob("warnings-*.log"))
    assert len(logs) == 2
    text = logs[0].read_text()
    assert "Warnings by code" in text and "Warnings by project" in text
    assert "Total warnings: 1" in text
    assert "[red]unused" in text and "\x1b" not in text
    assert "Warning summary log:" in output.getvalue()


def test_no_warnings_does_not_create_log_directory(
    tmp_path: Path, isolated_home: Path
) -> None:
    output = StringIO()
    print_warning_summary(Console(file=output), _config(tmp_path), "Build succeeded.")
    assert "No warnings found" in output.getvalue()
    assert not (isolated_home / ".pace/logs").exists()


def test_log_failure_is_reported_without_raising(tmp_path: Path) -> None:
    output = StringIO()
    with patch("pathlib.Path.mkdir", side_effect=PermissionError("Not writable")):
        print_warning_summary(
            Console(file=output), _config(tmp_path), "warning CS2008: No source"
        )
    assert "Could not write warning summary log: Not writable" in output.getvalue()
