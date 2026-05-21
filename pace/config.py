"""Pydantic models for PACE configuration."""

import os
from pathlib import Path

import tomli
from pydantic import BaseModel, model_validator


class Project(BaseModel):
    """Project model for PACE."""

    name: str
    csproj_path: str


class Config(BaseModel):
    """Configuration model for PACE."""

    repodir: Path
    projects: list[Project]

    @model_validator(mode="after")
    def apply_env_overrides(self) -> "Config":
        """Apply environment variable overrides to the configuration."""
        env_repodir = os.getenv("REPODIR")
        if env_repodir is not None:
            self.repodir = Path(env_repodir)
        return self


def load_config(file_path: Path) -> Config:
    """Load a TOML file and return its contents as a Config object."""
    with file_path.open("rb") as f:
        data = tomli.load(f)
    return Config(**data)
