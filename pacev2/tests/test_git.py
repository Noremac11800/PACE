"""Git forwarding, configured cloning, warnings, and real local repository tests."""

import json
import shutil
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from pacev2.cli import app
from pacev2.execution import Reporter, TaskResult, TaskStatus
from pacev2.models import Config, Project
from pacev2.paths import project_directory

runner = CliRunner(env={"COLUMNS": "160"})
SUCCESS = TaskResult(TaskStatus.SUCCEEDED, "Completed\n", 0)


@pytest.fixture
def git_config(tmp_path: Path) -> Iterator[Config]:
    config = Config(
        repodir=tmp_path / "checkouts",
        projects=[
            Project(
                name=name,
                csproj_path=Path("src") / "Project.csproj",
                repo_url=f"https://example.invalid/team/remote-{name}.git",
            )
            for name in ("alpha", "beta")
        ],
    )
    for project in config.projects:
        (config.repodir / project.name / ".git").mkdir(parents=True)
    with (
        patch(
            "pacev2._context.ConfigStore.load",
            return_value=(tmp_path / "config.toml", config),
        ),
        patch("pacev2.commands.git.shutil.which", return_value="git"),
    ):
        yield config


@pytest.mark.parametrize(
    "arguments",
    [
        ["status"],
        ["status", "--short", "--untracked-files=all"],
        ["pull", "--ff-only"],
        ["checkout", "main"],
        ["log", "-5", "--oneline"],
        ["config", "--local", "test.value", "value with spaces; [red]literal"],
        ["-c", "alias.custom=!echo hello", "custom"],
        ["-Cpath-with-h", "status"],
        ["status", "--help"],
        ["--version"],
    ],
)
def test_arbitrary_arguments_run_for_every_project(
    git_config: Config, arguments: list[str]
) -> None:
    with patch("pacev2.commands.git.run_command", return_value=SUCCESS) as execute:
        result = runner.invoke(app, ["git", *arguments])

    assert result.exit_code == 0
    assert execute.call_count == 2
    assert {call.args[1] for call in execute.call_args_list} == {
        git_config.repodir / "alpha",
        git_config.repodir / "beta",
    }
    for call in execute.call_args_list:
        assert call.args[0] == ["git", "--no-pager", *arguments]
        assert call.kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"
        assert call.kwargs["env"]["GIT_PAGER"] == ""
        assert call.kwargs["env"]["GIT_CEILING_DIRECTORIES"] == str(git_config.repodir)
    assert "2 succeeded, 0 failed, 0 skipped" in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["clone"],
        ["clone", "--depth", "1", "--branch", "main"],
        ["-c", "protocol.version=2", "clone", "--filter=blob:none"],
        ["-C", ".", "clone"],
        ["--no-optional-locks", "clone"],
        ["clone", "--"],
    ],
)
def test_clone_supplies_configured_urls_and_project_name_destinations(
    git_config: Config, arguments: list[str]
) -> None:
    git_config.repodir = git_config.repodir / "not-created-yet"
    with patch("pacev2.commands.git.run_command", return_value=SUCCESS) as execute:
        result = runner.invoke(app, ["git", *arguments])

    assert result.exit_code == 0
    assert git_config.repodir.is_dir()
    assert execute.call_count == 2
    for call in execute.call_args_list:
        command = call.args[0]
        destination = Path(command[-1])
        assert destination.parent == git_config.repodir
        assert destination.name in {"alpha", "beta"}
        assert (
            command[-2] == f"https://example.invalid/team/remote-{destination.name}.git"
        )
        assert command[:-2] == [
            "git",
            "--no-pager",
            *arguments,
            *([] if arguments[-1] == "--" else ["--"]),
        ]
        assert call.args[1] == git_config.repodir


def test_option_value_named_clone_is_not_treated_as_clone(git_config: Config) -> None:
    with patch("pacev2.commands.git.run_command", return_value=SUCCESS) as execute:
        result = runner.invoke(app, ["git", "-C", "clone", "status"])

    assert result.exit_code == 0
    for call in execute.call_args_list:
        assert call.args[0] == ["git", "--no-pager", "-C", "clone", "status"]
        assert call.args[1].parent == git_config.repodir


def test_existing_clones_are_skipped(git_config: Config) -> None:
    with patch("pacev2.commands.git.run_command") as execute:
        result = runner.invoke(app, ["git", "clone"])

    assert result.exit_code == 0
    execute.assert_not_called()
    assert "Already cloned" in result.output
    assert "0 succeeded, 0 failed, 2 skipped" in result.output


def test_empty_directories_can_be_cloned_into(git_config: Config) -> None:
    for project in git_config.projects:
        (git_config.repodir / project.name / ".git").rmdir()
    with patch("pacev2.commands.git.run_command", return_value=SUCCESS) as execute:
        result = runner.invoke(app, ["git", "clone"])

    assert result.exit_code == 0
    assert execute.call_count == 2


@pytest.mark.parametrize("url", [None, "", "   "])
@pytest.mark.parametrize("command", ["status", "clone"])
def test_projects_without_urls_are_reported_and_skipped(
    git_config: Config, url: str | None, command: str
) -> None:
    for project in git_config.projects:
        project.repo_url = url
    with patch("pacev2.commands.git.run_command") as execute:
        result = runner.invoke(app, ["git", command])

    assert result.exit_code == 0
    execute.assert_not_called()
    assert "no repo_url configured" in result.output
    assert "alpha" in result.output and "beta" in result.output
    assert "2 skipped" in result.output


def test_missing_checkouts_warn_without_creating_directories(
    git_config: Config,
) -> None:
    git_config.repodir = git_config.repodir / "missing"
    with patch("pacev2.commands.git.run_command") as execute:
        result = runner.invoke(app, ["git", "status"])

    assert result.exit_code == 0
    execute.assert_not_called()
    assert "not cloned" in result.output
    assert "pacev2 git clone" in result.output
    assert not git_config.repodir.exists()


def test_non_repository_directories_are_errors(git_config: Config) -> None:
    for project in git_config.projects:
        (git_config.repodir / project.name / ".git").rmdir()
    with patch("pacev2.commands.git.run_command") as execute:
        result = runner.invoke(app, ["git", "status"])

    assert result.exit_code == 1
    execute.assert_not_called()
    assert "Not a Git checkout" in result.output
    assert "2 failed" in result.output


def test_inaccessible_checkout_is_a_failure_not_a_missing_repo(
    git_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_stat = Path.stat

    def stat(path: Path, *, follow_symlinks: bool = True) -> object:
        if path == git_config.repodir / "alpha":
            raise PermissionError("Access denied to alpha")
        return original_stat(path, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "stat", stat)
    with patch("pacev2.commands.git.run_command", return_value=SUCCESS) as execute:
        result = runner.invoke(app, ["git", "status"])

    assert result.exit_code == 1
    assert execute.call_count == 1
    assert "Access denied to alpha" in result.output
    assert "1 succeeded, 1 failed, 0 skipped" in result.output


def test_git_failures_preserve_output_and_do_not_stop_other_projects(
    git_config: Config,
) -> None:
    def execute(
        args: Sequence[str],
        cwd: Path,
        report: Reporter,
        *,
        env: Mapping[str, str] | None = None,
    ) -> TaskResult:
        report("Working")
        if cwd.name == "alpha":
            return SUCCESS
        return TaskResult(TaskStatus.FAILED, "fatal: first detail\nlast detail\n", 128)

    with patch("pacev2.commands.git.run_command", side_effect=execute) as command:
        result = runner.invoke(app, ["git", "pull"])

    assert command.call_count == 2
    assert result.exit_code == 1
    assert "alpha" in result.output and "beta" in result.output
    assert "fatal: first detail\nlast detail" in result.output
    assert "Exit 128" in result.output
    assert "1 succeeded, 1 failed, 0 skipped" in result.output


def test_missing_git_is_reported_per_project(git_config: Config) -> None:
    with patch("pacev2.commands.git.shutil.which", return_value=None):
        result = runner.invoke(app, ["git", "status"])

    assert result.exit_code == 1
    assert "Git executable not found on PATH" in result.output
    assert "2 failed" in result.output


def test_missing_arguments_do_not_load_config() -> None:
    with patch("pacev2._context.ConfigStore") as store:
        result = runner.invoke(app, ["git"])

    assert result.exit_code == 2
    assert "Provide a Git command" in result.output
    store.assert_not_called()


def test_empty_filtered_selection_does_not_execute_git(git_config: Config) -> None:
    git_config.projects = []
    with patch("pacev2.commands.git.run_command") as execute:
        result = runner.invoke(app, ["git", "status"])

    assert result.exit_code == 0
    execute.assert_not_called()
    assert "No projects selected" in result.output


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../outside",
        r"..\outside",
        "/outside",
        r"C:\outside",
        "C:outside",
    ],
)
def test_project_directories_cannot_escape_repodir(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="single directory name"):
        project_directory(tmp_path, name)


@pytest.fixture
def local_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    executable = shutil.which("git")
    if executable is None:
        pytest.skip("Git is required for local repository integration tests")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "no-global-config"))
    for variable in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG_COUNT"):
        monkeypatch.delenv(variable, raising=False)
    return executable


def _git(executable: str, cwd: Path, *arguments: str) -> str:
    result = subprocess.run(
        [executable, "--no-pager", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


@pytest.fixture
def local_config(tmp_path: Path, local_git: str) -> Path:
    lines = [f"repodir = {json.dumps(str(tmp_path / 'checkouts'))}"]
    for name in ("alpha", "beta"):
        origin = tmp_path / f"remote-{name}"
        origin.mkdir()
        _git(local_git, origin, "init", "--initial-branch=main")
        _git(
            local_git,
            origin,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "Initial fixture",
        )
        lines.extend(
            [
                "[[projects]]",
                f"name = {json.dumps(name)}",
                'csproj_path = "Project.csproj"',
                f"repo_url = {json.dumps(str(origin))}",
                'depends_on = ["alpha"]' if name == "beta" else "depends_on = []",
            ]
        )
    config_path = tmp_path / "local.toml"
    config_path.write_text("\n".join(lines), encoding="utf-8")
    return config_path


def test_real_local_clone_status_checkout_pull_and_alias(
    local_config: Path, local_git: str, tmp_path: Path
) -> None:
    result = runner.invoke(app, ["-C", str(local_config), "git", "clone"])
    assert result.exit_code == 0, result.output
    checkouts = tmp_path / "checkouts"
    assert (checkouts / "alpha" / ".git").is_dir()
    assert (checkouts / "beta" / ".git").is_dir()
    assert not (checkouts / "remote-alpha").exists()

    for arguments in (
        ["status"],
        ["checkout", "-b", "feature"],
        ["checkout", "main"],
        ["-c", "alias.project-head=rev-parse --short HEAD", "project-head"],
    ):
        result = runner.invoke(app, ["git", *arguments])
        assert result.exit_code == 0, result.output
        assert "2 succeeded" in result.output

    for name in ("alpha", "beta"):
        origin = tmp_path / f"remote-{name}"
        _git(
            local_git,
            origin,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "Next fixture",
        )
    result = runner.invoke(app, ["git", "pull", "--ff-only"])
    assert result.exit_code == 0, result.output
    for name in ("alpha", "beta"):
        assert _git(local_git, checkouts / name, "rev-parse", "HEAD") == _git(
            local_git, tmp_path / f"remote-{name}", "rev-parse", "HEAD"
        )

    result = runner.invoke(app, ["git", "checkout", "nonexistent-branch"])
    assert result.exit_code == 1
    assert "nonexistent-branch" in result.output
    assert "2 failed" in result.output


def test_real_git_respects_filtered_config(local_config: Path, tmp_path: Path) -> None:
    clone = runner.invoke(app, ["-C", str(local_config), "git", "clone"])
    assert clone.exit_code == 0, clone.output
    checkouts = tmp_path / "checkouts"
    (checkouts / "alpha" / "visible.txt").touch()
    (checkouts / "beta" / "excluded.txt").touch()

    result = runner.invoke(
        app,
        [
            "--from",
            "alpha",
            "--to",
            "alpha",
            "--print-config",
            "git",
            "status",
            "--short",
        ],
    )

    assert result.exit_code == 0, result.output
    printed_config, _ = json.JSONDecoder().raw_decode(result.stdout)
    assert [project["name"] for project in printed_config["projects"]] == ["alpha"]
    assert "visible.txt" in result.output
    assert "excluded.txt" not in result.output
    assert "1 succeeded" in result.output


def test_real_bare_clones_support_other_git_commands(
    local_config: Path, tmp_path: Path
) -> None:
    clone = runner.invoke(app, ["-C", str(local_config), "git", "clone", "--bare"])
    assert clone.exit_code == 0, clone.output
    assert (tmp_path / "checkouts" / "alpha" / "HEAD").is_file()

    result = runner.invoke(app, ["git", "rev-parse", "--is-bare-repository"])

    assert result.exit_code == 0, result.output
    assert "true" in result.output
    assert "2 succeeded" in result.output
