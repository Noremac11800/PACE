"""pace git command - Execute git commands across all repositories."""

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from pace.config import Config

if TYPE_CHECKING:
    from collections.abc import Callable


class ReposGitStatus:
    """Thread-safe status tracker for each repository."""

    def __init__(self) -> None:
        """Initialize the status tracker."""
        self._lock = threading.Lock()
        self._status: dict[str, Text | Spinner] = {}

    def set(self, repo_name: str, status: Text | Spinner) -> None:
        """Set the status for a repository."""
        with self._lock:
            self._status[repo_name] = status

    def get_table(self) -> Table:
        """Get a table of all repository statuses."""
        with self._lock:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Repository")
            table.add_column("Status")
            for repo_name, status in sorted(self._status.items()):
                table.add_row(repo_name, status)
            return table


def _pull_repo(repo_url: str, dest_dir: Path, statuses: ReposGitStatus) -> None:
    """Pull a single repo and update its status.

    Args:
        repo_url: URL of the repository to pull
        dest_dir: Directory to pull the repository into
        statuses: ReposGitStatus instance to update
    """
    repo_name = repo_url.rsplit("/", maxsplit=1)[-1].replace(".git", "")
    repo_path = dest_dir / repo_name

    statuses.set(repo_name, Spinner("dots", text="Pulling...", style="cyan"))

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "pull"],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if result.returncode == 0:
            statuses.set(repo_name, Text("Done ✓", style="green"))
        else:
            statuses.set(repo_name, Text(f"Failed: {result.stderr[:70]}", style="red"))
    except subprocess.TimeoutExpired:
        statuses.set(repo_name, Text("Timeout", style="red"))
    except OSError as e:
        statuses.set(repo_name, Text(f"Error: {e}", style="red"))


def _clone_repo(repo_url: str, dest_dir: Path, statuses: ReposGitStatus) -> None:
    """Clone a single repo and update its status.

    Args:
        repo_url: URL of the repository to clone
        dest_dir: Directory to clone the repository into
        statuses: ReposGitStatus instance to update
    """
    repo_name = repo_url.rsplit("/", maxsplit=1)[-1].replace(".git", "")
    repo_path = dest_dir / repo_name

    if repo_path.exists():
        statuses.set(repo_name, Text("Skipped (already exists)", style="yellow"))
        return

    statuses.set(repo_name, Spinner("dots", text="Cloning...", style="cyan"))

    try:
        result = subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if result.returncode == 0:
            statuses.set(repo_name, Text("Done ✓", style="green"))
        else:
            statuses.set(repo_name, Text(f"Failed: {result.stderr[:70]}", style="red"))
    except subprocess.TimeoutExpired:
        statuses.set(repo_name, Text("Timeout", style="red"))
    except OSError as e:
        statuses.set(repo_name, Text(f"Error: {e}", style="red"))


def run(console: Console, config: Config, _args: list[str]) -> None:
    """Clone all repositories in parallel.

    Args:
        console: Rich console instance for output
        config: PACE configuration
        args: Additional arguments to pass to git (unused)
    """
    command: Callable[[str, Path, ReposGitStatus], None] | None = None
    if len(_args) > 0:
        if _args[0] == "pull":
            command = _pull_repo
        elif _args[0] == "clone":
            command = _clone_repo
        else:
            console.print(f"Unknown command: {_args[0]}", style="red")
            return
    else:
        console.print("No command specified", style="red")
        return

    statuses = ReposGitStatus()
    for project in config.projects:
        statuses.set(project.name, Spinner("dots", text="Dispatching to thread...", style="dim"))

    with (
        Live(statuses.get_table(), console=console, refresh_per_second=10) as live,
        ThreadPoolExecutor() as executor,
    ):
        futures = {
            executor.submit(command, project.repo_url, config.repodir, statuses): project
            for project in config.projects
            if project.repo_url is not None
        }
        for _ in as_completed(futures):
            live.update(statuses.get_table())
