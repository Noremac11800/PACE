# Copyright (c) 2026

"""Exact, atomic project-membership synchronization for the generated PACE solution."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import DefusedXMLParser

from pacev2.models import Config, Project
from pacev2.paths import normalize_path


def _read_solution(path: Path) -> tuple[ET.Element, bool]:
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        return ET.Element("Solution"), False
    try:
        parser = DefusedXMLParser(target=ET.TreeBuilder(insert_comments=True), forbid_dtd=True)
        parser.feed(content)
        root = parser.close()
    except (ET.ParseError, DefusedXmlException) as error:
        raise ValueError(
            f"Invalid solution {path}; the existing file was left untouched: {error}"
        ) from error
    if root.tag != "Solution":
        raise ValueError(f"Invalid solution {path}: expected a Solution root element")
    return root, True


def _remove_projects(
    root: ET.Element,
    solution: Path,
    selected: dict[Path, Project],
) -> tuple[set[Path], bool]:
    retained: set[Path] = set()
    changed = False
    for parent in root.iter():
        for child in list(parent):
            if child.tag != "Project":
                continue
            value = child.get("Path")
            if not value:
                raise ValueError(f"Invalid solution {solution}: a Project is missing its Path")
            path = (solution.parent / normalize_path(value)).resolve()
            if path not in selected or path in retained:
                parent.remove(child)
                changed = True
            else:
                retained.add(path)
    return retained, changed


def _add_project(root: ET.Element, directory: Path, path: Path, project: Project) -> None:
    parent = root
    if project.sln_group:
        name = f"/{project.sln_group.strip('/')}/"
        folder = next(
            (folder for folder in root.findall("Folder") if folder.get("Name") == name), None
        )
        parent = folder if folder is not None else ET.SubElement(root, "Folder", Name=name)
    try:
        relative_path = Path(os.path.relpath(path, directory)).as_posix()
    except ValueError:
        relative_path = path.as_posix()  # Windows projects may be on another drive.
    ET.SubElement(parent, "Project", Path=relative_path)


def _write_solution(path: Path, root: ET.Element, *, existing: bool) -> None:
    ET.indent(root, space="  ")
    content = ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            dir=path.parent, prefix=".pace-solution-", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        if existing:
            temporary.chmod(path.stat().st_mode)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def sync_solution(config: Config, selected: dict[Path, Project]) -> Path:
    """Sync selected projects without auto-including their project references."""
    path = config.repodir.resolve() / "PACE.slnx"
    root, existing = _read_solution(path)
    retained, removed = _remove_projects(root, path, selected)
    for project_path, project in selected.items():
        if project_path not in retained:
            _add_project(root, path.parent, project_path, project)
    if not existing or removed or retained != selected.keys():
        _write_solution(path, root, existing=existing)
    return path
