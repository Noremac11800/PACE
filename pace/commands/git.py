"""pace git command - Execute git commands across all repositories."""

from rich.console import Console


def run(console: Console, args: list[str]) -> None:
    """Execute git commands across all repositories.

    Args:
        console: Rich console instance for output
        args: Additional arguments to pass to git
    """
    console.print(f"pace git {' '.join(args)} - Not yet implemented")
