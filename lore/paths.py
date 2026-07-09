"""Jeden katalog projektu: rozdziały + pliki Cynober (.kafd)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from cynober_worlds import validate_world_name


@dataclass(frozen=True)
class ProjectPaths:
    """Ścieżki projektu pisarza — lore i rozdziały w jednym folderze."""

    name: str
    root: Path

    @classmethod
    def resolve(cls, name: str, root: str | Path | None = None) -> "ProjectPaths":
        validated = validate_world_name(name)
        if root is not None:
            base = Path(root).expanduser().resolve()
        else:
            env = os.environ.get("LORE_PROJECT_DIR", "").strip()
            if env:
                base = Path(env).expanduser().resolve()
            else:
                base = (Path.home() / ".lore_editor" / "worlds" / validated).resolve()
        base.mkdir(parents=True, exist_ok=True)
        return cls(name=validated, root=base)

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