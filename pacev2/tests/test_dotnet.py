"""Solution synchronization, passthrough, framework selection, and real SDK coverage."""

import json
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

import pytest
from pacev2.cli import app
from pacev2.commands.dotnet_solution import sync_solution
from pacev2.execution import Reporter, TaskResult, TaskStatus
from pacev2.models import Config, Project
from typer.testing import CliRunner

runner = CliRunner(env={"COLUMNS": "160"})
SUCCESS = TaskResult(TaskStatus.SUCCEEDED, "Build succeeded.\n", 0)


@pytest.fixture
def dotnet_config(tmp_path: Path) -> Iterator[Config]:
    config = Config(
        repodir=tmp_path / "workspace with spaces",
        projects=[
            Project(
                name="app",
                csproj_path=Path("src/App.csproj"),
                sln_group="Applications",
                depends_on=["base"],
            ),
            Project(
                name="base", csproj_path=Path("Base.csproj"), sln_group="Libraries"
            ),
        ],
    )
    for project in config.projects:
        path = config.repodir / project.name / project.csproj_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>',
            encoding="utf-8",
        )
    with (
        patch(
            "pacev2._context.ConfigStore.load",
            return_value=(tmp_path / "config.toml", config),
        ),
        patch("pacev2.commands.dotnet.shutil.which", return_value="dotnet"),
    ):
        yield config


def _members(path: Path) -> set[Path]:
    return {
        (path.parent / item.attrib["Path"].replace("\\", "/")).resolve()
        for item in ElementTree.parse(path).findall(".//Project")
    }


@pytest.mark.parametrize(
    "args",
    [
        ["build", "-c", "Release", "--no-restore", "-p:Message=spaces;[red]literal"],
        ["test", "--no-build", "--logger", "trx;LogFileName=results.trx"],
        ["restore", "--ignore-failed-sources"],
        ["pack", "--no-restore"],
        ["msbuild", "-t:Build", "/p:Configuration=Release"],
    ],
)
def test_solution_runs_once_with_verbatim_arguments(
    dotnet_config: Config, args: list[str]
) -> None:
    with patch("pacev2.commands.dotnet.run_command", return_value=SUCCESS) as execute:
        result = runner.invoke(app, ["dotnet", *args])
    assert result.exit_code == 0, result.output
    execute.assert_called_once()
    solution = dotnet_config.repodir / "PACE.slnx"
    assert execute.call_args.args[0] == ["dotnet", args[0], str(solution), *args[1:]]
    assert execute.call_args.args[1] == Path.cwd()
    assert _members(solution) == {
        dotnet_config.repodir / p.name / p.csproj_path for p in dotnet_config.projects
    }
    assert {
        folder.attrib["Name"]
        for folder in ElementTree.parse(solution).findall("Folder")
    } == {"/Applications/", "/Libraries/"}


def test_sync_removes_stale_members_and_preserves_metadata(
    dotnet_config: Config,
) -> None:
    solution = dotnet_config.repodir / "PACE.slnx"
    solution.write_text(
        """<Solution>
<!-- Keep this comment -->
<Configurations><Platform Name="Any CPU" /></Configurations>
<Folder Name="/Custom/"><Project Path="app/src/App.csproj"><Build Solution="Debug|*" /></Project>
<Project Path="stale/Stale.csproj" /></Folder></Solution>""",
        encoding="utf-8",
    )
    selected = {
        dotnet_config.repodir / p.name / p.csproj_path: p
        for p in dotnet_config.projects
    }
    sync_solution(dotnet_config, selected)
    assert _members(solution) == set(selected)
    assert "Keep this comment" in solution.read_text()
    assert ElementTree.parse(solution).find(".//Project/Build") is not None
    assert ElementTree.parse(solution).find("Configurations") is not None
    original = solution.read_bytes(), solution.stat().st_mtime_ns
    sync_solution(dotnet_config, selected)
    assert (solution.read_bytes(), solution.stat().st_mtime_ns) == original


@pytest.mark.parametrize(
    "content", ["<broken", "<NotASolution />", "<Solution><Project /></Solution>"]
)
def test_invalid_solution_is_not_overwritten(
    dotnet_config: Config, content: str
) -> None:
    solution = dotnet_config.repodir / "PACE.slnx"
    solution.write_text(content)
    with patch("pacev2.commands.dotnet.run_command") as execute:
        result = runner.invoke(app, ["dotnet", "build"])
    assert result.exit_code == 1
    assert "Invalid solution" in result.output
    assert solution.read_text() == content
    execute.assert_not_called()


def test_filtered_selection_removes_excluded_projects(dotnet_config: Config) -> None:
    with patch("pacev2.commands.dotnet.run_command", return_value=SUCCESS):
        assert runner.invoke(app, ["dotnet", "build"]).exit_code == 0
        dotnet_config.projects = dotnet_config.filtered(to_repo="base").projects
        result = runner.invoke(app, ["--to", "base", "dotnet", "build"])
    assert result.exit_code == 0
    assert _members(dotnet_config.repodir / "PACE.slnx") == {
        dotnet_config.repodir / "base/Base.csproj"
    }


def test_print_flags_precede_solution_command(dotnet_config: Config) -> None:
    with patch("pacev2.commands.dotnet.run_command", return_value=SUCCESS):
        result = runner.invoke(app, ["--print-config", "dotnet", "build"])
    assert result.exit_code == 0
    config, offset = json.JSONDecoder().raw_decode(result.stdout)
    assert config["projects"][0]["name"] == "app"
    assert "Solution:" in result.stdout[offset:]


def test_framework_evaluation_uses_single_and_multiple_targets(
    dotnet_config: Config,
) -> None:
    def execute(args: list[str], *_args: object, **_kwargs: object) -> TaskResult:
        if args[1] != "msbuild":
            return SUCCESS
        value = (
            {"TargetFramework": "", "TargetFrameworks": "net10.0;net10.0-ios"}
            if "app" in args[2]
            else {"TargetFramework": "net10.0", "TargetFrameworks": ""}
        )
        return TaskResult(TaskStatus.SUCCEEDED, json.dumps({"Properties": value}), 0)

    with patch("pacev2.commands.dotnet.run_command", side_effect=execute) as command:
        result = runner.invoke(
            app,
            [
                "dotnet",
                "build",
                "--framework=net10.0-ios",
                "--configuration=Release",
                "-p:Flavor=Mobile",
            ],
        )
    assert result.exit_code == 0, result.output
    assert command.call_count == 3
    for call in command.call_args_list[:2]:
        assert "-p:Configuration=Release" in call.args[0]
        assert "-p:Flavor=Mobile" in call.args[0]
    assert _members(dotnet_config.repodir / "PACE.slnx") == {
        dotnet_config.repodir / "app/src/App.csproj"
    }
    assert "Skipping base" in result.output


@pytest.mark.parametrize(
    "response",
    [
        TaskResult(TaskStatus.FAILED, "Missing workload", 1),
        TaskResult(TaskStatus.SUCCEEDED, "not JSON", 0),
        TaskResult(
            TaskStatus.SUCCEEDED,
            json.dumps(
                {"Properties": {"TargetFramework": "net9.0", "TargetFrameworks": ""}}
            ),
            0,
        ),
    ],
)
def test_failed_or_empty_framework_selection_never_runs_build(
    dotnet_config: Config, response: TaskResult
) -> None:
    with patch("pacev2.commands.dotnet.run_command", return_value=response) as command:
        result = runner.invoke(app, ["dotnet", "build", "-f", "net10.0"])
    assert result.exit_code == 1
    assert all(call.args[0][1] == "msbuild" for call in command.call_args_list)
    assert not (dotnet_config.repodir / "PACE.slnx").exists()


def test_missing_project_warns_and_uses_remaining_projects(
    dotnet_config: Config,
) -> None:
    (dotnet_config.repodir / "app/src/App.csproj").unlink()
    with patch("pacev2.commands.dotnet.run_command", return_value=SUCCESS):
        result = runner.invoke(app, ["dotnet", "build"])
    assert result.exit_code == 0
    assert "project file not found" in result.output
    assert len(_members(dotnet_config.repodir / "PACE.slnx")) == 1


def test_empty_selection_does_not_touch_existing_solution(
    dotnet_config: Config,
) -> None:
    dotnet_config.projects = []
    solution = dotnet_config.repodir / "PACE.slnx"
    solution.write_text("Leave untouched")
    with (
        patch("pacev2.commands.dotnet.run_command") as command,
        patch("pacev2.commands.dotnet.shutil.which", return_value=None),
    ):
        result = runner.invoke(app, ["dotnet", "build"])
    assert result.exit_code == 0
    assert "No projects selected" in result.output
    assert solution.read_text() == "Leave untouched"
    command.assert_not_called()


@pytest.mark.parametrize(
    "args",
    [
        ["--info"],
        ["--list-sdks"],
        ["--", "--version"],
        ["build", "--help"],
        ["help", "build"],
    ],
)
def test_diagnostics_and_forwarded_help_do_not_require_configuration(
    args: list[str],
) -> None:
    with (
        patch("pacev2.commands.dotnet.shutil.which", return_value="dotnet"),
        patch("pacev2.commands.dotnet.run_command", return_value=SUCCESS) as execute,
        patch("pacev2._context.ConfigStore") as store,
    ):
        result = runner.invoke(app, ["-C", "missing.toml", "dotnet", *args])
    assert result.exit_code == 0
    assert execute.call_args.args[0] == [
        "dotnet",
        *[arg for arg in args if arg != "--"],
    ]
    store.assert_not_called()


def test_missing_arguments_do_not_load_configuration() -> None:
    with patch("pacev2._context.ConfigStore") as store:
        result = runner.invoke(app, ["dotnet"])
    assert result.exit_code == 2
    assert "Provide a dotnet command" in result.output
    store.assert_not_called()


def test_sdk_missing_is_reported() -> None:
    with patch("pacev2.commands.dotnet.shutil.which", return_value=None):
        result = runner.invoke(app, ["dotnet", "build"])
    assert result.exit_code == 1
    assert "dotnet executable not found" in result.output


def test_build_exit_code_and_output_are_preserved(dotnet_config: Config) -> None:
    def execute(_args: list[str], _cwd: Path, report: Reporter) -> TaskResult:
        report("first error [red]literal")
        report("last error")
        return TaskResult(TaskStatus.FAILED, "first error\nlast error\n", 7)

    with patch("pacev2.commands.dotnet.run_command", side_effect=execute):
        result = runner.invoke(app, ["dotnet", "build"])
    assert result.exit_code == 7
    assert "first error [red]literal" in result.output
    assert "last error" in result.output


def test_launch_failure_is_reported(dotnet_config: Config) -> None:
    with patch(
        "pacev2.commands.dotnet.run_command", side_effect=OSError("Cannot launch SDK")
    ):
        result = runner.invoke(app, ["dotnet", "build"])
    assert result.exit_code == 1
    assert "Cannot launch SDK" in result.output


def test_real_sdk_builds_a_generated_solution_and_filters_it(tmp_path: Path) -> None:
    dotnet = shutil.which("dotnet")
    if dotnet is None:
        pytest.skip("A .NET SDK is required")
    version = subprocess.run(
        [dotnet, "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    major = int(version.split(".")[0])
    if major < 9 or (major == 9 and int(version.split(".")[2].split("-")[0]) < 200):
        pytest.skip(".slnx requires .NET SDK 9.0.200 or newer")
    projects = []
    for name in ("Base", "App"):
        directory = tmp_path / name
        directory.mkdir()
        reference = (
            '<ItemGroup><ProjectReference Include="../Base/Base.csproj" /></ItemGroup>'
            if name == "App"
            else ""
        )
        (directory / f"{name}.csproj").write_text(
            f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net{major}.0</TargetFramework></PropertyGroup>{reference}</Project>'
        )
        (directory / "Library.cs").write_text(
            "#warning PACE integration warning\npublic class BaseType {}"
            if name == "Base"
            else "public class AppType : BaseType {}"
        )
        projects.append(
            f'[[projects]]\nname = "{name}"\ncsproj_path = "{name}.csproj"\ndepends_on = {json.dumps(["Base"] if name == "App" else [])}\n'
        )
    config_path = tmp_path / "demo.toml"
    config_path.write_text(
        f"repodir = {json.dumps(str(tmp_path))}\n" + "\n".join(projects)
    )
    result = runner.invoke(
        app, ["-C", str(config_path), "dotnet", "-w", "build", "--nologo", "-v:q"]
    )
    assert result.exit_code == 0, result.output
    assert "Total warnings: 1" in result.output
    assert (tmp_path / "App/bin/Debug" / f"net{major}.0/App.dll").is_file()
    result = runner.invoke(
        app,
        [
            "-C",
            str(config_path),
            "--to",
            "Base",
            "dotnet",
            "build",
            "--no-restore",
            "-v:q",
        ],
    )
    assert result.exit_code == 0, result.output
    assert _members(tmp_path / "PACE.slnx") == {tmp_path / "Base/Base.csproj"}


def test_warning_summary_does_not_mask_failed_build_exit_code(
    dotnet_config: Config, isolated_home: Path
) -> None:
    warning = f"file.cs(1,1): warning CS0168: Unused variable [{dotnet_config.repodir}/base/Base.csproj]"
    with patch(
        "pacev2.commands.dotnet.run_command",
        return_value=TaskResult(TaskStatus.FAILED, warning, 7),
    ):
        result = runner.invoke(app, ["dotnet", "-w", "build"])
    assert result.exit_code == 7
    assert "Total warnings: 1" in result.output
    assert len(list((isolated_home / ".pace/logs").glob("*.log"))) == 1


def test_solution_xml_entities_are_rejected(dotnet_config: Config) -> None:
    solution = dotnet_config.repodir / "PACE.slnx"
    content = '<!DOCTYPE Solution [<!ENTITY project "base/Base.csproj">]><Solution><Project Path="&project;" /></Solution>'
    solution.write_text(content)
    with patch("pacev2.commands.dotnet.run_command") as execute:
        result = runner.invoke(app, ["dotnet", "build"])
    assert result.exit_code == 1
    assert "Invalid solution" in result.output
    assert solution.read_text() == content
    execute.assert_not_called()
