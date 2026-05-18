"""CLI entry point for PACE."""

import argparse
import sys
from argparse import Namespace

from pace.commands import dotnet
from pace.rich_demos import progress_bar

_DEMOS = {
    "progress_bar": progress_bar.run,
}


def main() -> int:
    """Main entry point for the PACE CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="PACE - Project Automation and Configuration Engine"
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    subparsers.add_parser("dotnet", help="Execute dotnet commands across the project graph")

    demo_parser = subparsers.add_parser("demo", help="Run a built-in demo")
    demo_parser.add_argument(
        "name",
        choices=list(_DEMOS),
        metavar="name",
        help=f"Demo to run. Choices: {', '.join(_DEMOS)}",
    )

    args: Namespace = parser.parse_args()

    match args.command:
        case "dotnet":
            dotnet.run(args)
        case "demo":
            _DEMOS[args.name]()
        case _:
            parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
