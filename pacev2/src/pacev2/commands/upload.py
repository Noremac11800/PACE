# Copyright (c) 2026

"""App package upload command interface."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from pacev2._context import configure
from pacev2._stubs import not_implemented


class Platform(StrEnum):
    """Target platforms supported by app package uploads."""

    IOS = "iOS"
    ANDROID = "Android"
    WINDOWS = "Windows"


class ReleaseType(StrEnum):
    """Build configurations accepted by package uploads."""

    DEBUG = "Debug"
    RELEASE = "Release"


def run(
    ctx: typer.Context,
    _package_path: Annotated[
        Path,
        typer.Argument(
            metavar="<path-to-app-package>",
            help="Path to the app package file (.ipa, .msix, .aab, .apk)",
        ),
    ],
    _username: Annotated[
        str,
        typer.Option("--username", metavar="<username>", help="Name of the uploader"),
    ],
    _app_name: Annotated[
        str,
        typer.Option("--app-name", metavar="<appname>", help="Name of the application"),
    ],
    _platform: Annotated[
        Platform,
        typer.Option("--platform", metavar="<platform>", help="Target platform"),
    ],
    _release_type: Annotated[
        ReleaseType,
        typer.Option("--release-type", metavar="<type>", help="Build configuration"),
    ],
    _version: Annotated[
        str,
        typer.Option("--version", metavar="<version>", help="Version number or identifier"),
    ],
    _endpoint: Annotated[
        str,
        typer.Option("--endpoint", metavar="<url>", help="Base URL of the deployment server"),
    ],
    _build_description: Annotated[
        str | None,
        typer.Option(
            "--build-description",
            "-n",
            metavar="<description>",
            help="Build notes/description",
        ),
    ] = None,
    _build_description_from_file: Annotated[
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
