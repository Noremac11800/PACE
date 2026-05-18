"""
CLI entry point for PACE.
"""

import argparse
from argparse import Namespace
import sys

from pace.commands import dotnet


def main() -> int:
    """
    Main entry point for the PACE CLI.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="PACE - Project Automation and Configuration Engine"
    )
    parser.add_argument("command", help="Command to execute")
    args: Namespace = parser.parse_args()

    print("PACE - Project Automation and Configuration Engine")
    print(f"Command: {args.command}")

    match args.command:
        case "dotnet":
            dotnet.run(args)
        case _:
            print("CLI not yet implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
