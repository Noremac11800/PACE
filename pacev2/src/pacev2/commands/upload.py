"""App package upload command interface."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from pacev2._context import configure
from pacev2._stubs import not_implemented


class Platform(StrEnum):
    IOS = "iOS"
    ANDROID = "Android"
    WINDOWS = "Windows"


class ReleaseType(StrEnum):
    DEBUG = "Debug"
    RELEASE = "Release"


def run(
    ctx: typer.Context,
    package_path: Annotated[
        Path,
        typer.Argument(
            metavar="<path-to-app-package>",
            help="Path to the app package file (.ipa, .msix, .aab, .apk)",
        ),
    ],
    username: Annotated[
        str,
        typer.Option("--username", metavar="<username>", help="Name of the uploader"),
    ],
    app_name: Annotated[
        str,
        typer.Option("--app-name", metavar="<appname>", help="Name of the application"),
    ],
    platform: Annotated[
        Platform,
        typer.Option("--platform", metavar="<platform>", help="Target platform"),
    ],
    release_type: Annotated[
        ReleaseType,
        typer.Option("--release-type", metavar="<type>", help="Build configuration"),
    ],
    version: Annotated[
        str,
        typer.Option(
            "--version", metavar="<version>", help="Version number or identifier"
        ),
    ],
    endpoint: Annotated[
        str,
        typer.Option(
            "--endpoint", metavar="<url>", help="Base URL of the deployment server"
        ),
    ],
    build_description: Annotated[
        str | None,
        typer.Option(
            "--build-description",
            "-n",
            metavar="<description>",
            help="Build notes/description",
        ),
    ] = None,
    build_description_from_file: Annotated[
        Path | None,
        typer.Option(
            "--build-description-from-file",
            "-N",
            metavar="<filepath>",
            help="Read build description from file",
        ),
    ] = None,
) -> None:
    """Upload app packages to the deployment server."""
    configure(ctx)
    not_implemented("upload")
