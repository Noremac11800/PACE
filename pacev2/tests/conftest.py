"""Configuration fixtures isolated from the developer's files and history."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.chdir(tmp_path)
    return home


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "workspace" / "projects.toml"
    path.parent.mkdir()
    path.write_text(
        r"""
repodir = 'repositories'
nuget_cache_path = '~\nuget-packages'

[[projects]]
name = 'app'
csproj_path = 'src\App\App.csproj'
repo_url = 'git@example.invalid:team/app.git'
sln_group = 'Apps'
depends_on = ['lib', 'branch', 'support']

[[projects]]
name = 'base'
csproj_path = 'src/Base/Base.csproj'

[[projects]]
name = 'lib'
csproj_path = 'src/Lib/Lib.csproj'
depends_on = ['base']

[[projects]]
name = 'support'
csproj_path = 'Support.csproj'

[[projects]]
name = 'other'
csproj_path = 'Other.csproj'

[[projects]]
name = 'branch'
csproj_path = 'Branch.csproj'
depends_on = ['base']

[[projects]]
name = 'side'
csproj_path = 'Side.csproj'
depends_on = ['base']

[[build-props]]
name = 'DevSolution'
datatype = 'boolean'
default = false

[[build-props]]
name = 'PackageOutputPath'
datatype = 'path'
default = '~\packages'

[[build-props]]
name = 'EmptyPath'
datatype = 'path'
default = ''

[[build-props]]
name = 'Label'
default = 'Development'
""",
        encoding="utf-8",
    )
    return path
