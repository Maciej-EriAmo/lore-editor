"""Jeden katalog projektu: rozdziały + pliki Cynober (.kafd)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cynober_worlds import validate_world_name

LORE_PROJECT_FILE = ".lore-project"
DEFAULT_PROJECT_NAME = "MojaPowiesc"


@dataclass(frozen=True)
class ProjectPaths:
    """Ścieżki projektu pisarza — lore i rozdziały w jednym folderze."""

    name: str
    root: Path

    @classmethod
    def discover(
        cls,
        project: str | None = None,
        project_dir: str | Path | None = None,
        *,
        cwd: Path | None = None,
    ) -> "ProjectPaths":
        """
        Kolejność:
        1. --project-dir / LORE_PROJECT_DIR
        2. plik .lore-project (cwd lub rodzice)
        3. bieżący katalog (cwd)
        """
        work = (cwd or Path.cwd()).resolve()
        cli_name = (project or "").strip() or None

        if project_dir is not None:
            root = Path(project_dir).expanduser().resolve()
            name = cls._pick_name(root, cli_name)
            return cls._open(name, root)

        env = os.environ.get("LORE_PROJECT_DIR", "").strip()
        if env:
            root = Path(env).expanduser().resolve()
            name = cls._pick_name(root, cli_name)
            return cls._open(name, root)

        marker_root = cls._find_marker_root(work)
        if marker_root is not None:
            file_name = cls._read_marker_name(marker_root / LORE_PROJECT_FILE)
            name = cli_name or file_name or cls._name_from_folder(marker_root)
            return cls._open(name, marker_root)

        name = cli_name or cls._name_from_folder(work)
        return cls._open(name, work)

    @classmethod
    def resolve(cls, name: str, root: str | Path | None = None) -> "ProjectPaths":
        """Bezpośrednie ustawienie (testy, API)."""
        validated = validate_world_name(name)
        if root is not None:
            base = Path(root).expanduser().resolve()
        else:
            env = os.environ.get("LORE_PROJECT_DIR", "").strip()
            if env:
                base = Path(env).expanduser().resolve()
            else:
                base = (Path.home() / ".lore_editor" / "worlds" / validated).resolve()
        return cls._open(validated, base)

    @classmethod
    def _open(cls, name: str, root: Path) -> "ProjectPaths":
        validated = validate_world_name(name)
        root.mkdir(parents=True, exist_ok=True)
        return cls(name=validated, root=root.resolve())

    @classmethod
    def _find_marker_root(cls, start: Path) -> Optional[Path]:
        for parent in [start, *start.parents]:
            if (parent / LORE_PROJECT_FILE).is_file():
                return parent.resolve()
            if parent == Path.home():
                break
        return None

    @classmethod
    def _read_marker_name(cls, path: Path) -> Optional[str]:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("name="):
                val = line.split("=", 1)[1].strip()
                if val:
                    try:
                        return validate_world_name(val)
                    except ValueError:
                        return None
            if "=" not in line and not line.startswith("["):
                try:
                    return validate_world_name(line)
                except ValueError:
                    continue
        return None

    @classmethod
    def _pick_name(cls, root: Path, cli_name: str | None) -> str:
        marker = root / LORE_PROJECT_FILE
        if cli_name:
            return validate_world_name(cli_name)
        if marker.is_file():
            from_file = cls._read_marker_name(marker)
            if from_file:
                return from_file
        return cls._name_from_folder(root)

    @classmethod
    def _name_from_folder(cls, folder: Path) -> str:
        raw = folder.name or DEFAULT_PROJECT_NAME
        try:
            return validate_world_name(raw)
        except ValueError:
            slug = re.sub(r"[^\w]", "_", raw, flags=re.UNICODE)
            slug = re.sub(r"_+", "_", slug).strip("_")[:32]
            return validate_world_name(slug or DEFAULT_PROJECT_NAME)

    def world_kafd(self) -> Path:
        return self.root / f"{self.name}.kafd"

    def plik_wzgledny(self, path: str | Path) -> str:
        p = Path(path).resolve()
        try:
            return str(p.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(p)

    def plik_absolutny(self, stored: str) -> Path:
        p = Path(stored)
        if p.is_absolute():
            return p
        return (self.root / stored).resolve()

    def write_marker(self) -> Path:
        """Utwórz / zaktualizuj .lore-project w katalogu projektu."""
        path = self.root / LORE_PROJECT_FILE
        path.write_text(f"name={self.name}\n", encoding="utf-8")
        return path