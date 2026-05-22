"""Pydantic models for PACE configuration."""

import os
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

import tomli
from pydantic import BaseModel, model_validator


class Project(BaseModel):
    """Project model for PACE.

    Attributes:
        name: Name of the project.
        csproj_path: Path to the project file.
        repo_url: URL of the repository. (Optional)
    """

    name: str
    csproj_path: Path
    repo_url: str | None = None


class Config(BaseModel):
    """Configuration model for PACE.

    Attributes:
        repodir: Directory where repositories are cloned.
        projects: List of projects.
    """

    repodir: Path
    projects: list[Project]

    @model_validator(mode="after")
    def apply_env_overrides(self) -> "Config":
        """Apply environment variable overrides to the configuration."""
        env_repodir = os.getenv("REPODIR")
        if env_repodir is not None:
            self.repodir = Path(env_repodir)

        if self.repodir.exists():
            return self

        raise ValueError(f"Repository directory {self.repodir} does not exist")


def load_config(file_path: Path | Traversable | None = None) -> Config:
    """Load a TOML file and return its contents as a Config object.

    Args:
        file_path: Path to the TOML file.

    Returns:
        Config: Configuration object.
    """
    if file_path is None:
        file_path = files("pace.data").joinpath("pace.toml")

    with file_path.open("rb") as f:
        data = tomli.load(f)
    return Config(**data)
