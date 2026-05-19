"""pace git command - Execute git commands across all repositories."""

import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

REPOS = [
    "git@github.com:Noremac11800/pantry.git",
    "git@github.com:Noremac11800/Ward-of-Whispers.git",
    "git@github.com:Noremac11800/TkDesktop.git",
    "git@github.com:Noremac11800/PoolPy.git",
    "git@github.com:Noremac11800/SDLCanvas.jl.git",
    "git@github.com:Noremac11800/harpoon.git",
    "git@github.com:Noremac11800/Godot.git",
]


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


def _clone_repo(repo_url: str, dest_dir: Path, statuses: ReposGitStatus) -> tuple[str, str, bool]:
    """Clone a single repo and update its status.

    Returns:
        Tuple of (repo_url, message, success)
    """
    repo_name = repo_url.rsplit("/", maxsplit=1)[-1].replace(".git", "")
    repo_path = dest_dir / repo_name

    if repo_path.exists():
        statuses.set(repo_name, Text("Skipped (already exists)", style="yellow"))
        return repo_url, f"[yellow]Skipped: {repo_name} (already exists)[/yellow]", True

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
            return repo_url, f"[green]Cloned: {repo_name}[/green]", True
        statuses.set(repo_name, Text(f"Failed: {result.stderr}", style="red"))
        return repo_url, f"[red]Failed: {repo_name} - {result.stderr}[/red]", False
    except subprocess.TimeoutExpired:
        statuses.set(repo_name, Text("Timeout", style="red"))
        return repo_url, f"[red]Timeout: {repo_name}[/red]", False
    except OSError as e:
        statuses.set(repo_name, Text(f"Error: {e}", style="red"))
        return repo_url, f"[red]Error: {repo_name} - {e}[/red]", False


def run(console: Console, _args: list[str]) -> None:
    """Clone all repositories in parallel.

    Args:
        console: Rich console instance for output
        args: Additional arguments to pass to git (unused)
    """
    tmp_dir = Path(tempfile.gettempdir()) / "PACE"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    statuses = ReposGitStatus()
    for repo in REPOS:
        repo_name = repo.rsplit("/", maxsplit=1)[-1].replace(".git", "")
        statuses.set(repo_name, Spinner("dots", text="Dispatching to thread...", style="dim"))

    with (
        Live(statuses.get_table(), console=console, refresh_per_second=10) as live,
        ThreadPoolExecutor() as executor,
    ):
        futures = {executor.submit(_clone_repo, repo, tmp_dir, statuses): repo for repo in REPOS}
        for _ in as_completed(futures):
            live.update(statuses.get_table())
