"""CLI contract tests that do not require configuration or external tools."""

import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest
from pacev2.cli import app
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner(env={"COLUMNS": "160"})

UPLOAD_ARGUMENTS = [
    "upload",
    "app.msix",
    "--username",
    "Developer",
    "--app-name",
    "Example App",
    "--platform",
    "Windows",
    "--release-type",
    "Release",
    "--version",
    "1.2.3",
    "--endpoint",
    "https://deploy.example.invalid",
]


@pytest.mark.parametrize("arguments", [[], ["-h"], ["--help"]])
def test_roothelp_listsinterface(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 0
    for name in ("clean", "dotnet", "git", "upload", "update"):
        assert name in result.output
    for option in (
        "--debug",
        "-C",
        "--config",
        "--print-config",
        "--print-config-path",
        "-v",
        "--version",
        "--from",
        "--to",
        "-h",
        "--help",
    ):
        assert option in result.output
    assert "--install-completion" not in result.output


@pytest.mark.parametrize("help_flag", ["-h", "--help"])
@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("clean", ["--cache", "--custom-cache", "--project", "-n", "--dry-run"]),
        ("dotnet", ["--summarize-warnings", "-w", "<dotnet-args>"]),
        ("git", ["<git-args>"]),
        (
            "upload",
            [
                "<path-to-app-package>",
                "--username",
                "--app-name",
                "--platform",
                "--release-type",
                "--version",
                "--endpoint",
                "-n",
                "--build-description",
                "-N",
                "--build-description-from-file",
            ],
        ),
        ("update", ["Update pace-dotnet"]),
    ],
)
def test_commandhelp_listsinterface(
    command: str, expected: list[str], help_flag: str
) -> None:
    result = runner.invoke(app, [command, help_flag])

    assert result.exit_code == 0
    for text in expected:
        assert text in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["clean"],
        ["clean", "--cache", "--custom-cache", "--project", "-n"],
        ["clean", "--dry-run"],
        ["update"],
        UPLOAD_ARGUMENTS,
        [*UPLOAD_ARGUMENTS, "-n", "Build notes", "-N", "missing-notes.txt"],
        [
            *UPLOAD_ARGUMENTS,
            "--build-description",
            "Build notes",
            "--build-description-from-file",
            "missing-notes.txt",
        ],
    ],
)
def test_commands_reportunimplemented(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 1
    assert result.stdout == ""
    assert f"{arguments[0]} is not implemented yet in pacev2." in result.stderr


@pytest.mark.parametrize(
    ("command", "feature"), [([], "Global option handling"), (["clean"], "clean")]
)
def test_debug_remainsstub(command: list[str], feature: str) -> None:
    result = runner.invoke(app, ["--debug", *command])

    assert result.exit_code == 1
    assert f"{feature} is not implemented yet in pacev2." in result.stderr


@pytest.mark.parametrize("flag", ["-v", "--version"])
def test_version_matchesprojectversion(flag: str) -> None:
    project_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with project_path.open("rb") as project_file:
        expected_version = tomllib.load(project_file)["project"]["version"]

    result = runner.invoke(app, [flag])

    assert result.exit_code == 0
    assert result.stdout == f"pacev2 {expected_version}\n"
    assert result.stderr == ""


@pytest.mark.parametrize("flag", ["-v", "--version"])
@pytest.mark.parametrize(
    "other_options",
    [
        [],
        [
            "--debug",
            "-C",
            "missing-config.toml",
            "--print-config",
            "--print-config-path",
            "--from",
            "FirstRepo",
            "--to",
            "LastRepo",
        ],
    ],
)
def test_version_readsinstalledmetadata(flag: str, other_options: list[str]) -> None:
    with patch("pacev2.cli.get_version", return_value="2.3.4rc1") as get_version:
        result = runner.invoke(app, [*other_options, flag])

    get_version.assert_called_once_with("pacev2")
    assert result.exit_code == 0
    assert result.stdout == "pacev2 2.3.4rc1\n"
    assert result.stderr == ""


@pytest.mark.parametrize("flag", ["-v", "--version"])
def test_version_withcommand_preservescommand(flag: str) -> None:
    result = runner.invoke(app, [flag, "clean"])

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "clean is not implemented yet in pacev2." in result.stderr


@pytest.mark.parametrize(
    "missing",
    [
        "app.msix",
        "--username",
        "--app-name",
        "--platform",
        "--release-type",
        "--version",
        "--endpoint",
    ],
)
def test_upload_requiresmetadata(missing: str) -> None:
    arguments = UPLOAD_ARGUMENTS.copy()
    index = arguments.index(missing)
    del arguments[index : index + (2 if missing.startswith("--") else 1)]

    result = runner.invoke(app, arguments)

    assert result.exit_code == 2
    assert "Missing" in result.output
    assert "not implemented" not in result.output


@pytest.mark.parametrize("global_flag", ["-v", "--version"])
@pytest.mark.parametrize("include_upload_version", [True, False])
def test_versionflags_keepscopes(
    global_flag: str, include_upload_version: bool
) -> None:
    arguments = [global_flag, *UPLOAD_ARGUMENTS]
    if not include_upload_version:
        index = arguments.index("--version", 2)
        del arguments[index : index + 2]

    result = runner.invoke(app, arguments)

    if include_upload_version:
        assert result.exit_code == 1
        assert "upload is not implemented yet in pacev2." in result.stderr
    else:
        assert result.exit_code == 2
        assert "Missing option" in result.output


@pytest.mark.parametrize("platform", ["iOS", "Android", "Windows"])
@pytest.mark.parametrize("release_type", ["Debug", "Release"])
def test_upload_acceptslegacychoices(platform: str, release_type: str) -> None:
    arguments = UPLOAD_ARGUMENTS.copy()
    arguments[arguments.index("--platform") + 1] = platform
    arguments[arguments.index("--release-type") + 1] = release_type

    result = runner.invoke(app, arguments)

    assert result.exit_code == 1
    assert "upload is not implemented yet in pacev2." in result.stderr


@pytest.mark.parametrize(
    ("option", "value"),
    [
        ("--platform", "Linux"),
        ("--platform", "ios"),
        ("--release-type", "debug"),
        ("--release-type", "Production"),
    ],
)
def test_upload_rejectsinvalidchoices(option: str, value: str) -> None:
    arguments = UPLOAD_ARGUMENTS.copy()
    arguments[arguments.index(option) + 1] = value

    result = runner.invoke(app, arguments)

    assert result.exit_code == 2
    assert "Invalid value" in result.output
    assert "not implemented" not in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["unknown-command"],
        ["--unknown-option"],
        ["clean", "--unknown-option"],
        ["update"],
    ],
)
def test_invalidarguments_showusageerror(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 2
    assert "Usage:" in result.output
    assert "not implemented" not in result.output


@pytest.mark.parametrize(
    ("arguments", "expected", "summarize"),
    [
        ([], [], False),
        (["--info"], ["--info"], False),
        (
            ["-w", "build", "-c", "Release", "--no-restore"],
            ["build", "-c", "Release", "--no-restore"],
            True,
        ),
        (["--summarize-warnings", "test"], ["test"], True),
        (["build", "-w", "--help"], ["build", "-w", "--help"], False),
        (["--", "--version"], ["--version"], False),
        (
            ["-p:MyProperty=value with spaces"],
            ["-p:MyProperty=value with spaces"],
            False,
        ),
    ],
)
def test_dotnet_preservesarguments(
    arguments: list[str], expected: list[str], summarize: bool
) -> None:
    command = get_command(app)
    assert isinstance(command, TyperGroup)

    with command.commands["dotnet"].make_context("dotnet", arguments.copy()) as ctx:
        assert list(ctx.params["dotnet_args"]) == expected
        assert ctx.params["summarize_warnings"] is summarize


@pytest.mark.parametrize(
    ("name", "arguments", "argument_name", "expected"),
    [
        ("git", ["--version"], "git_args", ["--version"]),
        ("git", ["pull", "--help"], "git_args", ["pull", "--help"]),
        ("git", ["checkout", "main", "-h"], "git_args", ["checkout", "main", "-h"]),
        ("git", ["-Cpath-with-h", "status"], "git_args", ["-Cpath-with-h", "status"]),
        ("git", ["--", "--help"], "git_args", ["--help"]),
        (
            "git",
            ["-c", "alias.custom=!echo hello", "custom"],
            "git_args",
            ["-c", "alias.custom=!echo hello", "custom"],
        ),
        (
            "git",
            ["checkout", "feature-branch", "--no-track"],
            "git_args",
            ["checkout", "feature-branch", "--no-track"],
        ),
    ],
)
def test_passthrough_preservesarguments(
    name: str, arguments: list[str], argument_name: str, expected: list[str]
) -> None:
    command = get_command(app)
    assert isinstance(command, TyperGroup)

    with command.commands[name].make_context(name, arguments.copy()) as ctx:
        assert list(ctx.params[argument_name]) == expected
