"""Monitor protocol, concurrency, MSBuild aggregation, and real SDK coverage."""

import json
import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from xml.sax.saxutils import escape

import pytest
from pacev2.cli import app
from pacev2.commands.dotnet_monitor import BuildProgress, execute_monitored
from pacev2.execution import Reporter, Task, TaskResult, TaskStatus, run_parallel
from pacev2.models import Config, Project
from pacev2.monitor import Monitor
from rich.console import Console
from typer.testing import CliRunner

runner = CliRunner()


def events(output: str) -> list[dict]:
    records = [json.loads(line) for line in output.splitlines()]
    assert all(record["protocol"] == "pace.monitor" for record in records)
    assert all(record["version"] == 1 for record in records)
    assert [record["sequence"] for record in records] == list(
        range(1, len(records) + 1)
    )
    return records


def test_monitor_flushes_atomic_ordered_events_from_parallel_tasks() -> None:
    stream = StringIO()
    monitor = Monitor("git", stream)
    barrier = Barrier(2, timeout=10)

    def action(report: Reporter) -> TaskResult:
        report('Working on "quoted"\nUnicode: \u2603')
        barrier.wait()
        return TaskResult(TaskStatus.SUCCEEDED, "Done", 0)

    with (
        patch("pacev2.execution.Live") as live,
        patch.object(stream, "flush", wraps=stream.flush) as flush,
    ):
        run_parallel(
            [Task("first", action), Task("second", action)],
            Console(file=StringIO()),
            monitor=monitor,
        )
        monitor.finish(0)
    live.assert_not_called()
    records = events(stream.getvalue())
    assert records[0]["event"] == "start"
    assert records[-1]["counts"]["succeeded"] == 2
    assert flush.call_count == len(records) - 1
    assert sum(record["event"] == "log" for record in records) == 2
    assert all(
        record["status"] == "succeeded"
        for record in records[-2:]
        if record["event"] == "project"
    )


def test_finish_never_invents_success_for_unobserved_work() -> None:
    stream = StringIO()
    monitor = Monitor("dotnet.build", stream)
    monitor.project("queued")
    monitor.project("active", status="running", stage="build")
    monitor.finish(1)
    records = events(stream.getvalue())
    assert records[-1]["counts"]["incomplete"] == 2
    assert monitor.projects["active"].stages["build"] == "incomplete"


def test_git_monitor_retains_skips_and_errors_without_a_table(tmp_path: Path) -> None:
    config = Config(
        repodir=tmp_path,
        projects=[Project(name="no-url", csproj_path=Path("App.csproj"))],
    )
    with patch(
        "pacev2._context.ConfigStore.load",
        return_value=(tmp_path / "config.toml", config),
    ):
        result = runner.invoke(app, ["--monitor", "--print-config", "git", "status"])
    assert result.exit_code == 0, result.output
    records = events(result.stdout)
    assert records[-1]["counts"]["skipped"] == 1
    assert "no repo_url" in next(
        record["text"] for record in records if record["event"] == "log"
    )
    assert '"projects"' in result.stderr


def test_stage_aggregation_handles_multiple_frameworks_and_sticky_failure(
    tmp_path: Path,
) -> None:
    monitor = Monitor("dotnet.build", StringIO())
    progress = BuildProgress(monitor, "build")
    project = str(tmp_path / "App.csproj")
    progress.accept({"kind": "ready"})
    for context in ("net9", "net10"):
        progress.accept(
            {
                "kind": "stage_started",
                "project": project,
                "stage": "build",
                "context": context,
            }
        )
    progress.accept(
        {
            "kind": "stage_finished",
            "project": project,
            "stage": "build",
            "context": "net9",
            "succeeded": True,
        }
    )
    assert monitor.projects[project].stages["build"] == "running"
    progress.accept(
        {
            "kind": "stage_finished",
            "project": project,
            "stage": "build",
            "context": "net10",
            "succeeded": False,
        }
    )
    progress.finish()
    assert monitor.projects[project].status == "failed"
    assert monitor.projects[project].stages["build"] == "failed"


def test_later_unfinished_framework_cannot_inherit_earlier_success(
    tmp_path: Path,
) -> None:
    monitor = Monitor("dotnet.build", StringIO())
    progress = BuildProgress(monitor, "build")
    project = str(tmp_path / "App.csproj")
    progress.accept({"kind": "ready"})
    progress.accept(
        {
            "kind": "stage_finished",
            "project": project,
            "stage": "build",
            "context": "net9",
            "succeeded": True,
        }
    )
    progress.accept(
        {
            "kind": "stage_started",
            "project": project,
            "stage": "build",
            "context": "net10",
        }
    )
    progress.finish()
    monitor.finish(1)
    assert monitor.projects[project].status == "incomplete"


def test_logger_options_precede_runsettings_and_preserve_user_arguments(
    tmp_path: Path,
) -> None:
    monitor = Monitor("dotnet.test", StringIO())
    args = [
        "test",
        "PACE.slnx",
        "--no-build",
        "--logger",
        "trx",
        "--",
        "RunConfiguration.MaxCpuCount=2",
    ]
    event_paths: list[Path] = []

    def execute(
        command: list[str], _cwd: Path, report: Reporter, *, env: dict[str, str]
    ) -> TaskResult:
        assert command[:6] == ["dotnet", *args[:5]]
        assert command[-2:] == args[-2:]
        assert "-tl:off" in command
        path = Path(env["PACE_MONITOR_EVENTS"])
        event_paths.append(path)
        path.write_text('{"kind":"ready"}\n')
        report("Test output")
        return TaskResult(TaskStatus.FAILED, "Test output", 7)

    with (
        patch(
            "pacev2.commands.dotnet_monitor._logger",
            return_value=tmp_path / "logger.dll",
        ),
        patch("pacev2.commands.dotnet_monitor.run_command", side_effect=execute),
    ):
        result = execute_monitored("dotnet", args, {}, monitor)
    assert result.returncode == 7
    assert not event_paths[0].exists()


@pytest.fixture
def sdk_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    executable = shutil.which("dotnet")
    if executable is None:
        pytest.skip("A .NET SDK is required")
    version = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    major = int(version.split(".")[0])
    if major < 9 or (major == 9 and int(version.split(".")[2]) < 200):
        pytest.skip("A .slnx-compatible SDK is required")
    monkeypatch.setenv("DOTNET_CLI_HOME", str(tmp_path))
    monkeypatch.setenv("DOTNET_GENERATE_ASPNET_CERTIFICATE", "false")
    monkeypatch.setenv("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
    monkeypatch.setenv("DOTNET_NOLOGO", "1")
    framework = f"net{major}.0"
    root = tmp_path / "repos with spaces"
    root.mkdir()
    (root / "NuGet.Config").write_text(
        "<configuration><packageSources><clear /></packageSources></configuration>"
    )
    for name in ("Base", "App"):
        directory = root / name
        directory.mkdir(parents=True)
        reference = (
            '<ItemGroup><ProjectReference Include="../Base/Base.csproj" /></ItemGroup>'
            if name == "App"
            else ""
        )
        (directory / f"{name}.csproj").write_text(
            '<Project><Import Project="Sdk.props" Sdk="Microsoft.NET.Sdk" />'
            f"<PropertyGroup><TargetFramework>{framework}</TargetFramework></PropertyGroup>"
            + reference
            + '<Import Project="Sdk.targets" Sdk="Microsoft.NET.Sdk" />'
            # Exercise the actual VSTest entry target offline, without a test-framework package.
            '<Target Name="VSTest" DependsOnTargets="Build" Condition="\'$(IsCrossTargetingBuild)\' != \'true\'">'
            '<Message Text="Test target executed" Importance="high" />'
            "<Error Condition=\"'$(FailTests)' == 'true'\" Text=\"Intentional test target failure\" />"
            "</Target></Project>",
        )
        (directory / "Library.cs").write_text(
            "public class BaseType {}"
            if name == "Base"
            else "public class AppType : BaseType {}",
        )
    config = tmp_path / "workspace.toml"
    config.write_text(
        f"repodir = {json.dumps(str(root))}\n"
        '[[projects]]\nname = "App"\ncsproj_path = "App.csproj"\n'
        '[[projects]]\nname = "Missing"\ncsproj_path = "Missing.csproj"\n',
    )
    return config, framework


@pytest.mark.parametrize("command", ["build", "publish", "test"])
def test_real_msbuild_reports_projects_and_stages_at_quiet_verbosity(
    sdk_workspace: tuple[Path, str],
    command: str,
) -> None:
    config, _ = sdk_workspace
    result = runner.invoke(
        app, ["--monitor", "-C", str(config), "dotnet", command, "-v:q"]
    )
    assert result.exit_code == 0, result.output
    records = events(result.stdout)
    projects = {
        record["name"]: record for record in records if record["event"] == "project"
    }
    assert projects["App"]["status"] == "succeeded"
    assert projects["App"]["stages"][command] == "succeeded"
    assert projects["Base"]["stages"]["build"] == "succeeded"
    assert projects["Missing"]["status"] == "skipped"
    assert records[-1]["event"] == "finish"
    assert records[-1]["returncode"] == 0
    assert any(
        record["event"] == "project" and record["status"] == "running"
        for record in records
    )


def test_real_build_progress_arrives_before_process_exit(
    sdk_workspace: tuple[Path, str],
) -> None:
    config, _ = sdk_workspace
    root = config.parent / "repos with spaces"
    acknowledgement = config.parent / "ack"
    waiter = config.parent / "wait.py"
    waiter.write_text(
        "import sys, time\nfrom pathlib import Path\n"
        "deadline = time.monotonic() + 15\n"
        "while not Path(sys.argv[1]).exists():\n"
        "    if time.monotonic() > deadline: sys.exit(9)\n"
        "    time.sleep(0.03)\n",
    )
    project = root / "App/App.csproj"
    command = escape(
        f'"{sys.executable}" "{waiter}" "{acknowledgement}"', {'"': "&quot;"}
    )
    project.write_text(
        project.read_text().replace(
            "</Project>",
            f'<Target Name="AwaitObserver" BeforeTargets="CoreCompile"><Exec Command="{command}" /></Target></Project>',
        )
    )
    original = Monitor.emit

    def observe(self: Monitor, event: str, **fields: object) -> None:
        original(self, event, **fields)
        if event == "project" and fields.get("name") == "Base":
            stages = fields.get("stages")
            if isinstance(stages, dict) and stages.get("compile") == "succeeded":
                acknowledgement.touch()

    with patch.object(Monitor, "emit", observe):
        result = runner.invoke(
            app, ["--monitor", "-C", str(config), "dotnet", "build", "-v:q"]
        )
    assert result.exit_code == 0, result.output
    assert acknowledgement.is_file()


def test_real_multitarget_build_tracks_all_frameworks(
    sdk_workspace: tuple[Path, str],
) -> None:
    config, framework = sdk_workspace
    root = config.parent / "repos with spaces"
    for name in ("App", "Base"):
        project = root / name / f"{name}.csproj"
        project.write_text(
            project.read_text().replace(
                f"<TargetFramework>{framework}</TargetFramework>",
                f"<TargetFrameworks>{framework};{framework}-windows</TargetFrameworks>",
            )
        )
    result = runner.invoke(
        app, ["--monitor", "-C", str(config), "dotnet", "build", "-v:q"]
    )
    assert result.exit_code == 0, result.output
    records = events(result.stdout)
    projects = {
        record["name"]: record for record in records if record["event"] == "project"
    }
    assert projects["App"]["status"] == projects["Base"]["status"] == "succeeded"
    for name in ("App", "Base"):
        for target in (framework, f"{framework}-windows"):
            assert (root / name / "bin/Debug" / target / f"{name}.dll").is_file()


@pytest.mark.parametrize("command", ["publish", "test"])
def test_no_build_does_not_fabricate_compile_stages(
    sdk_workspace: tuple[Path, str],
    command: str,
) -> None:
    config, _ = sdk_workspace
    project = config.parent / "repos with spaces/App/App.csproj"
    content = project.read_text()
    project.write_text(content[: content.index('<Target Name="VSTest"')] + "</Project>")
    result = runner.invoke(
        app, ["--monitor", "-C", str(config), "dotnet", "build", "-v:q"]
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(
        app,
        [
            "--monitor",
            "-C",
            str(config),
            "dotnet",
            command,
            "-c",
            "Debug",
            "--no-build",
            "--no-restore",
            "-v:q",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Preparing MSBuild monitor" not in result.stdout
    records = events(result.stdout)
    projects = {
        record["name"]: record for record in records if record["event"] == "project"
    }
    assert projects["App"]["status"] == "succeeded"
    assert projects["App"]["stages"][command] == "succeeded"
    assert "compile" not in projects["App"]["stages"]


@pytest.mark.parametrize("command", ["build", "test"])
def test_failed_targets_keep_diagnostics_and_actual_exit_code(
    sdk_workspace: tuple[Path, str],
    command: str,
) -> None:
    config, _ = sdk_workspace
    if command == "build":
        (config.parent / "repos with spaces/App/Library.cs").write_text("not valid C#")
    result = runner.invoke(
        app,
        [
            "--monitor",
            "-C",
            str(config),
            "dotnet",
            command,
            "-p:FailTests=true",
            "-v:q",
        ],
    )
    assert result.exit_code != 0
    records = events(result.stdout)
    assert records[-1]["returncode"] == result.exit_code
    projects = {
        record["name"]: record for record in records if record["event"] == "project"
    }
    assert projects["App"]["status"] == "failed"
    assert any(
        record["event"] == "log" and "error" in record["text"].lower()
        for record in records
    )


def test_monitor_preserves_forwarded_dotnet_help_without_configuration() -> None:
    def execute(_args: list[str], _cwd: Path, report: Reporter) -> TaskResult:
        report("SDK help")
        return TaskResult(TaskStatus.SUCCEEDED, "SDK help", 0)

    with (
        patch("pacev2.commands.dotnet.shutil.which", return_value="dotnet"),
        patch("pacev2.commands.dotnet.run_command", side_effect=execute),
        patch("pacev2._context.ConfigStore") as store,
    ):
        result = runner.invoke(app, ["--monitor", "dotnet", "build", "--help"])
    assert result.exit_code == 0
    assert events(result.stdout)[-1]["returncode"] == 0
    store.assert_not_called()
