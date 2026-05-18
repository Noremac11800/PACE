"""pace dotnet command - Execute dotnet commands across the project graph."""

from argparse import Namespace


def run(args: Namespace) -> None:
    """Execute dotnet commands across all projects.

    Args:
        args: Additional arguments to pass to dotnet
    """
    print(f"pace dotnet {' '.join(vars(args))} - Not yet implemented")
