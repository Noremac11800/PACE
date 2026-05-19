"""CLI entry point for PACE."""

import argparse
import sys
from argparse import Namespace

import rich
from rich.console import Console
from rich.traceback import install

from pace.commands import dotnet, git
from pace.rich_demos import columns, progress_bar

_DEMOS = {
    "columns": columns.run,
    "progress_bar": progress_bar.run,
}


def main() -> int:
    """Main entry point for the PACE CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Enable rich traceback printing
    # Suppress stack frames from these modules:
    install(show_locals=True, suppress=[rich])

    console = Console()

    parser = argparse.ArgumentParser(
        description="PACE - Project Automation and Configuration Engine"
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    subparsers.add_parser("dotnet", help="Execute dotnet commands across the project graph")
    subparsers.add_parser("git", help="Execute git commands across all repositories")

    demo_parser = subparsers.add_parser("demo", help="Run a built-in demo")
    demo_parser.add_argument(
        "name",
        choices=list(_DEMOS),
        metavar="name",
        help=f"Demo to run. Choices: {', '.join(_DEMOS)}",
    )

    args: Namespace
    unknownargs: list[str]
    args, unknownargs = parser.parse_known_args()

    match args.command:
        case "dotnet":
            dotnet.run(console, unknownargs)
        case "git":
            git.run(console, unknownargs)
        case "demo":
            _DEMOS[args.name](console, unknownargs)
        case _:
            parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
