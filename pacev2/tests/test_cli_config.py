"""End-to-end configuration option behavior through Typer."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from pacev2._context import ConfigOptions, configure
from pacev2.cli import app
from pacev2.models import Config
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner()


@pytest.mark.parametrize("flag", ["-C", "--config"])
@pytest.mark.parametrize("separator", ["/", "\\"])
def test_explicit_config_accepts_either_path_style(
    config_file: Path, flag: str, separator: str
) -> None:
    reference = str(config_file.relative_to(Path.cwd())).replace("\\", "/")
    reference = reference.replace("/", separator)

    result = runner.invoke(app, [flag, reference, "--print-config-path"])

    assert result.exit_code == 0
    assert result.stdout == f"{config_file}\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        ([], ["app", "base", "lib", "support", "other", "branch", "side"]),
        (["--from", "base"], ["app", "base", "lib", "branch", "side"]),
        (["--to", "app"], ["app", "base", "lib", "support", "branch"]),
        (["--from", "base", "--to", "app"], ["app", "base", "lib", "branch"]),
        (["--from", "other", "--to", "app"], []),
    ],
)
def test_print_config_uses_filtered_model(
    config_file: Path, filters: list[str], expected: list[str]
) -> None:
    original = config_file.read_bytes()

    result = runner.invoke(app, ["-C", str(config_file), *filters, "--print-config"])

    assert result.exit_code == 0
    assert result.stderr == ""
    data = json.loads(result.stdout)
    assert [project["name"] for project in data["projects"]] == expected
    assert data["build-props"][0]["default"] is False
    assert config_file.read_bytes() == original


def test_both_print_options_share_selection(config_file: Path) -> None:
    result = runner.invoke(
        app,
        [
            "-C",
            str(config_file),
            "--from",
            "base",
            "--to",
            "app",
            "--print-config",
            "--print-config-path",
        ],
    )

    assert result.exit_code == 0
    path_line, document = result.stdout.split("\n", 1)
    assert path_line == str(config_file)
    assert [project["name"] for project in json.loads(document)["projects"]] == [
        "app",
        "base",
        "lib",
        "branch",
    ]


@pytest.mark.parametrize("print_option", ["--print-config", "--print-config-path"])
@pytest.mark.parametrize("filter_option", ["--from", "--to"])
def test_both_print_options_validate_filters(
    config_file: Path, print_option: str, filter_option: str
) -> None:
    result = runner.invoke(
        app, ["-C", str(config_file), filter_option, "missing", print_option]
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Project 'missing' not found in configuration" in result.stderr


def test_default_template_is_available_from_any_directory(isolated_home: Path) -> None:
    result = runner.invoke(app, ["--print-config-path"])

    path = isolated_home / ".pace" / "configs" / "template.toml"
    assert result.exit_code == 0
    assert result.stdout == f"{path}\n"
    assert path.is_file()

    result = runner.invoke(app, ["--print-config"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["projects"][0]["name"] == "my-class-lib"


def test_config_selection_without_printing_is_remembered(config_file: Path) -> None:
    selected = runner.invoke(app, ["-C", str(config_file)])
    remembered = runner.invoke(app, ["--print-config-path"])

    assert selected.exit_code == 0
    assert "Usage:" in selected.stdout
    assert remembered.exit_code == 0
    assert remembered.stdout == f"{config_file}\n"


@pytest.mark.parametrize("command", ["clean"])
def test_prints_filtered_config_before_command_stub(
    config_file: Path, command: str
) -> None:
    result = runner.invoke(
        app, ["-C", str(config_file), "--to", "lib", "--print-config", command]
    )

    assert result.exit_code == 1
    assert [project["name"] for project in json.loads(result.stdout)["projects"]] == [
        "base",
        "lib",
    ]
    assert f"{command} is not implemented yet" in result.stderr


def test_filtered_config_is_available_in_context(config_file: Path) -> None:
    command = get_command(app)
    ctx = typer.Context(command)
    with ctx:
        ctx.obj = ConfigOptions(path=config_file, from_repo="base", to_repo="app")
        configure(ctx)

        assert isinstance(ctx.obj, Config)
        assert [project.name for project in ctx.obj.projects] == [
            "app",
            "base",
            "lib",
            "branch",
        ]
        assert ctx.meta["config_path"] == config_file


@pytest.mark.parametrize("arguments", [[], ["clean"], ["upload"], ["git"], ["dotnet"]])
@pytest.mark.parametrize("help_flag", ["-h", "--help"])
def test_help_never_loads_config(
    arguments: list[str], help_flag: str, isolated_home: Path
) -> None:
    with patch("pacev2._context.ConfigStore") as store:
        result = runner.invoke(
            app,
            [
                "-C",
                "missing.toml",
                "--from",
                "missing",
                "--print-config",
                *arguments,
                help_flag,
            ],
        )

    assert result.exit_code == 0
    store.assert_not_called()
    assert not (isolated_home / ".pace").exists()


@pytest.mark.parametrize("flag", ["-v", "--version"])
def test_version_never_initializes_config(flag: str, isolated_home: Path) -> None:
    result = runner.invoke(app, [flag, "--print-config"])

    assert result.exit_code == 0
    assert result.stdout.startswith("pacev2 ")
    assert not (isolated_home / ".pace").exists()


def test_update_bypasses_config(isolated_home: Path) -> None:
    result = runner.invoke(app, ["-C", "missing.toml", "--print-config", "update"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "update is not implemented yet" in result.stderr
    assert not (isolated_home / ".pace").exists()


@pytest.mark.parametrize("command", [[], ["clean"]])
def test_explicit_missing_config_reports_error(command: list[str]) -> None:
    result = runner.invoke(
        app, ["--config", "missing.toml", "--print-config", *command]
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "error:" in result.stderr
    assert "missing.toml" in result.stderr
    assert "not implemented" not in result.stderr


@pytest.mark.parametrize("source", ["[broken", "projects = 42"])
def test_invalid_config_reports_its_source(config_file: Path, source: str) -> None:
    config_file.write_text(source, encoding="utf-8")

    result = runner.invoke(app, ["-C", str(config_file), "--print-config-path"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert str(config_file) in result.stderr
    assert "Invalid configuration" in result.stderr
