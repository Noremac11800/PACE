"""PACE command modules."""

from pace.commands import clean as clean_cmd
from pace.commands import dotnet as dotnet_cmd
from pace.commands import format as format_cmd
from pace.commands import git as git_cmd
from pace.commands import init as init_cmd
from pace.commands import test as test_cmd

__all__ = ["clean_cmd", "dotnet_cmd", "format_cmd", "git_cmd", "init_cmd", "test_cmd"]
