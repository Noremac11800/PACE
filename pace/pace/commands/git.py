"""pace git command - Execute git commands across all repositories."""

import subprocess
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from pace.config import Config


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


def _pull_repo(repo_url: str, dest_dir: Path, statuses: ReposGitStatus) -> tuple[bool, str]:
    """Pull a single repo and update its status.

    Args:
        repo_url: URL of the repository to pull
        dest_dir: Directory to pull the repository into
        statuses: ReposGitStatus instance to update

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    repo_name = repo_url.rsplit("/", maxsplit=1)[-1].replace(".git", "")
    repo_path = dest_dir / repo_name

    statuses.set(repo_name, Spinner("dots", text="Pulling...", style="cyan"))

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "pull"],
            capture_output=True,
            timeout=300,
            check=False,
        )
        if result.returncode == 0:
            statuses.set(repo_name, Text("Done ✓", style="green"))
            return True, ""
        # Decode with 'replace' to handle non-UTF-8 bytes from SSH/git
        error_msg = result.stderr.decode("utf-8", errors="replace").strip()[:70]
        statuses.set(repo_name, Text(f"Failed: {error_msg}", style="red"))
        return False, error_msg
    except subprocess.TimeoutExpired:
        statuses.set(repo_name, Text("Timeout", style="red"))
        return False, "Timeout"
    except OSError as e:
        statuses.set(repo_name, Text(f"Error: {e}", style="red"))
        return False, str(e)


def _clone_repo(repo_url: str, dest_dir: Path, statuses: ReposGitStatus) -> tuple[bool, str]:
    """Clone a single repo and update its status.

    Args:
        repo_url: URL of the repository to clone
        dest_dir: Directory to clone the repository into
        statuses: ReposGitStatus instance to update

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    repo_name = repo_url.rsplit("/", maxsplit=1)[-1].replace(".git", "")
    repo_path = dest_dir / repo_name

    if repo_path.exists():
        statuses.set(repo_name, Text("Skipped (already exists)", style="yellow"))
        return True, ""

    statuses.set(repo_name, Spinner("dots", text="Cloning...", style="cyan"))

    try:
        result = subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            capture_output=True,
            timeout=300,
            check=False,
        )
        if result.returncode == 0:
            statuses.set(repo_name, Text("Done ✓", style="green"))
            return True, ""
        # Decode with 'replace' to handle non-UTF-8 bytes from SSH/git
        error_msg = result.stderr.decode("utf-8", errors="replace").strip()[:70]
        statuses.set(repo_name, Text(f"Failed: {error_msg}", style="red"))
        return False, error_msg
    except subprocess.TimeoutExpired:
        statuses.set(repo_name, Text("Timeout", style="red"))
        return False, "Timeout"
    except OSError as e:
        statuses.set(repo_name, Text(f"Error: {e}", style="red"))
        return False, str(e)


def _checkout_repo(
    repo_url: str, dest_dir: Path, statuses: ReposGitStatus, branch: str
) -> tuple[bool, str]:
    """Checkout a specific branch in a single repo and update its status.

    Args:
        repo_url: URL of the repository
        dest_dir: Directory containing the repository
        statuses: ReposGitStatus instance to update
        branch: Branch name to checkout

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    repo_name = repo_url.rsplit("/", maxsplit=1)[-1].replace(".git", "")
    repo_path = dest_dir / repo_name

    if not repo_path.exists():
        statuses.set(repo_name, Text("Skipped (repo not found)", style="yellow"))
        return True, ""

    statuses.set(repo_name, Spinner("dots", text=f"Checking out {branch}...", style="cyan"))

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "checkout", branch],
            capture_output=True,
            timeout=300,
            check=False,
        )
        if result.returncode == 0:
            statuses.set(repo_name, Text("Done ✓", style="green"))
            return True, ""
        # Decode with 'replace' to handle non-UTF-8 bytes from SSH/git
        error_msg = result.stderr.decode("utf-8", errors="replace").strip()[:70]
        statuses.set(repo_name, Text(f"Failed: {error_msg}", style="red"))
        return False, error_msg
    except subprocess.TimeoutExpired:
        statuses.set(repo_name, Text("Timeout", style="red"))
        return False, "Timeout"
    except OSError as e:
        statuses.set(repo_name, Text(f"Error: {e}", style="red"))
        return False, str(e)


_SIMPLE_COMMANDS: dict[str, Callable[[str, Path, ReposGitStatus], tuple[bool, str]]] = {
    "pull": _pull_repo,
    "clone": _clone_repo,
}


def _parse_args(
    console: Console,
    args: list[str],
) -> tuple[Callable[[str, Path, ReposGitStatus], tuple[bool, str]] | None, str | None]:
    """Parse git subcommand arguments and return the command function and optional branch.

    Args:
        console: Rich console instance for error output
        args: Arguments passed to the git command

    Returns:
        A tuple of (command_function, checkout_branch).  Both are None on error (after
        printing a message).  command_function is None and checkout_branch is set when
        the subcommand is ``checkout``.
    """
    if not args:
        console.print("No command specified", style="red")
        return None, None

    subcommand = args[0]
    if subcommand in _SIMPLE_COMMANDS:
        return _SIMPLE_COMMANDS[subcommand], None
    if subcommand == "checkout":
        if len(args) < 2:  # noqa: PLR2004
            console.print("Error: checkout command requires a branch name", style="red")
            return None, None
        return None, args[1]

    console.print(f"Unknown command: {subcommand}", style="red")
    return None, None


def run(console: Console, config: Config, args: list[str]) -> int:
    """Execute git commands across all repositories in parallel.

    Args:
        console: Rich console instance for output
        config: PACE configuration
        args: Additional arguments to pass to git

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    command, checkout_branch = _parse_args(console, args)
    if command is None and checkout_branch is None:
        return 1  # Error: invalid command or arguments

    statuses = ReposGitStatus()
    for project in config.projects:
        statuses.set(project.name, Spinner("dots", text="Dispatching to thread...", style="dim"))

    results: list[tuple[bool, str]] = []
    failed_repos: list[tuple[str, str]] = []

    with (
        Live(statuses.get_table(), console=console, refresh_per_second=10) as live,
        ThreadPoolExecutor() as executor,
    ):
        if checkout_branch:
            futures = {
                executor.submit(
                    _checkout_repo, project.repo_url, config.repodir, statuses, checkout_branch
                ): project
                for project in config.projects
                if project.repo_url is not None
            }
        else:
            assert command is not None
            futures = {
                executor.submit(command, project.repo_url, config.repodir, statuses): project
                for project in config.projects
                if project.repo_url is not None
            }
        for future in as_completed(futures):
            project = futures[future]
            try:
                success, error_msg = future.result()
                results.append((success, error_msg))
                if not success:
                    failed_repos.append((project.name, error_msg))
            except Exception as e:
                results.append((False, str(e)))
                failed_repos.append((project.name, str(e)))
            live.update(statuses.get_table())

    # Report summary if there were failures
    if failed_repos:
        console.print(f"\n[red]Failed to process {len(failed_repos)} repository(s):[/red]")
        for repo_name, error in failed_repos:
            console.print(f"  [red]- {repo_name}: {error}[/red]")
        return 1

    return 0
