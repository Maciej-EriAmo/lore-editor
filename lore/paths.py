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

# Domyślny katalog pracy, gdy nie podano --project-dir / LORE_PROJECT_DIR
# i nie znaleziono .lore-project. Względem korzenia repo: ../dokumenty/lore
DEFAULT_WORK_DIR_REL = Path("dokumenty") / "lore"
ENV_PROJECT_DIR = "LORE_PROJECT_DIR"
ENV_DEFAULT_WORK_DIR = "LORE_DEFAULT_WORK_DIR"

# Ostatni katalog wybrany w GUI (Plik → Katalog projektu…)
SETTINGS_DIR = Path.home() / ".lore_editor"
LAST_WORK_DIR_FILE = SETTINGS_DIR / "last_work_dir.json"


def _repo_or_package_root() -> Path:
    """Katalog z pyproject/run_lore_editor (edytowalna instalacja) albo rodzic pakietu lore/."""
    here = Path(__file__).resolve().parent  # .../lore
    parent = here.parent
    if (parent / "pyproject.toml").is_file() or (parent / "run_lore_editor.py").is_file():
        return parent
    return parent


def default_work_dir(*, cwd: Path | None = None) -> Path:
    """
    Docelowy katalog pracy (powieść), gdy nie wskazano inaczej.

    Kolejność:
    1. LORE_DEFAULT_WORK_DIR (absolutna lub względna względem cwd)
    2. ../dokumenty/lore względem korzenia repo (sibling: <rodzic_repo>/dokumenty/lore)
    3. ~/dokumenty/lore (gdy pakiet zainstalowany bez drzewa repo)
    """
    env = os.environ.get(ENV_DEFAULT_WORK_DIR, "").strip()
    if env:
        p = Path(env).expanduser()
        if not p.is_absolute():
            base = (cwd or Path.cwd()).resolve()
            p = (base / p).resolve()
        else:
            p = p.resolve()
        return p

    repo = _repo_or_package_root()
    # Edytowalny checkout: lore-editor/ → ../dokumenty/lore
    if (repo / "pyproject.toml").is_file() or (repo / "run_lore_editor.py").is_file():
        return (repo.parent / DEFAULT_WORK_DIR_REL).resolve()

    return (Path.home() / DEFAULT_WORK_DIR_REL).resolve()


def load_last_work_dir() -> Optional[Path]:
    """Ostatni katalog pracy zapisany z GUI (jeśli istnieje)."""
    if not LAST_WORK_DIR_FILE.is_file():
        return None
    try:
        import json

        data = json.loads(LAST_WORK_DIR_FILE.read_text(encoding="utf-8"))
        raw = (data.get("path") or "").strip()
        if not raw:
            return None
        p = Path(raw).expanduser().resolve()
        return p
    except (OSError, ValueError, TypeError):
        return None


def save_last_work_dir(path: str | Path) -> Path:
    """Zapisz katalog pracy wybrany w GUI (następne uruchomienia)."""
    import json

    root = Path(path).expanduser().resolve()
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    LAST_WORK_DIR_FILE.write_text(
        json.dumps({"path": str(root), "version": 1}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return root


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
        1. --project-dir (jawny argument)
        2. LORE_PROJECT_DIR
        3. plik .lore-project (cwd lub rodzice)
        4. ostatni katalog z GUI (~/.lore_editor/last_work_dir.json)
        5. domyślny katalog pracy: ../dokumenty/lore (lub LORE_DEFAULT_WORK_DIR)
        """
        work = (cwd or Path.cwd()).resolve()
        cli_name = (project or "").strip() or None

        if project_dir is not None:
            root = Path(project_dir).expanduser().resolve()
            name = cls._pick_name(root, cli_name)
            return cls._open(name, root)

        env = os.environ.get(ENV_PROJECT_DIR, "").strip()
        if env:
            root = Path(env).expanduser().resolve()
            name = cls._pick_name(root, cli_name)
            return cls._open(name, root)

        marker_root = cls._find_marker_root(work)
        if marker_root is not None:
            file_name = cls._read_marker_name(marker_root / LORE_PROJECT_FILE)
            name = cli_name or file_name or cls._name_from_folder(marker_root)
            return cls._open(name, marker_root)

        last = load_last_work_dir()
        if last is not None:
            name = cli_name or cls._name_from_folder(last)
            return cls._open(name, last)

        root = default_work_dir(cwd=work)
        name = cli_name or cls._name_from_folder(root)
        return cls._open(name, root)

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