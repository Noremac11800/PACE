"""Pydantic models for PACE configuration."""

from pathlib import Path

import tomli
from pydantic import BaseModel


class Project(BaseModel):
    """Project model for PACE."""

    name: str
    csproj_path: str


class Config(BaseModel):
    """Configuration model for PACE."""

    repodir: str
    projects: list[Project]


def load_config(file_path: Path) -> Config:
    """Load a TOML file and return its contents as a Config object."""
    with file_path.open("rb") as f:
        data = tomli.load(f)
    return Config(**data)
