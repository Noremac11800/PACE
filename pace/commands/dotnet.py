"""pace dotnet command - Execute dotnet commands across the project graph."""

from argparse import Namespace

from rich.console import Console


def run(console: Console, args: Namespace) -> None:
    """Execute dotnet commands across all projects.

    Args:
        console: Rich console instance for output
        args: Additional arguments to pass to dotnet
    """
    console.print(f"pace dotnet {' '.join(vars(args))} - Not yet implemented")
