"""Historia zmian projektu — snapshoty .kafd + rozdziałów do przywracania."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

HISTORY_DIR = ".lore-history"
MANIFEST_FILE = "manifest.json"
README_FILE = "README.txt"
MANIFEST_VERSION = 1
MAX_SNAPSHOTS = 40
AUTO_MIN_INTERVAL_SEC = 120

_README_PL = """\
Lore Editor — historia zmian projektu
=====================================

Ten folder tworzy się automatycznie przy pierwszym uruchomieniu edytora
w katalogu projektu. Nie usuwaj go — to kopia zapasowa całej powieści.

Co jest zapisywane w snapshots/
  • Nazwa.kafd     — graf lore (postacie, relacje)
  • rozdzialy/     — wszystkie pliki .txt i .md z projektu
  • .lore-project  — znacznik projektu (jeśli istnieje)

Kiedy powstają snapshoty
  • Ctrl+S / autosave — zapisuje tekst rozdziału i lore (.kafd)
  • Zapis projektu lore (menu Lore)
  • Przed usunięciem wpisu lub przywróceniem starszej wersji
  • Ręcznie: menu Lore → Utwórz punkt przywracania…
  • Pierwsze otwarcie istniejącego projektu: „Stan początkowy”

Przywracanie: menu Lore → Historia zmian…
Pomoc w edytorze: F1 → temat „Historia zmian”.

BACKUP
Uwzględnij ten folder (.lore-history) w kopii projektu (chmura, dysk
zewnętrzny, git). Razem z plikami .txt i .kafd daje pełny obraz książki.

Rotacja: przechowywane jest do {max_snapshots} ostatnich snapshotów.
""".format(max_snapshots=MAX_SNAPSHOTS)

_ROZDZIAL_GLOB = ("*.txt", "*.md")
_SKIP_DIRS = {HISTORY_DIR, ".git", "__pycache__", "shards"}


@dataclass(frozen=True)
class SnapshotInfo:
    id: str
    created_at: float
    label: str
    reason: str
    fingerprint: str
    files: tuple[str, ...]

    def data_utworzenia(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.created_at))


def _iter_rozdzialy(root: Path) -> List[Path]:
    found: List[Path] = []
    for pattern in _ROZDZIAL_GLOB:
        for path in root.rglob(pattern):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            if any(part in _SKIP_DIRS or part.startswith(".") for part in rel.parts[:-1]):
                continue
            if HISTORY_DIR in rel.parts:
                continue
            found.append(path)
    return sorted(found, key=lambda p: str(p).lower())


def _fingerprint_projektu(root: Path, kafd: Path) -> str:
    h = hashlib.sha256()
    if kafd.is_file():
        h.update(kafd.read_bytes())
    for path in _iter_rozdzialy(root):
        h.update(str(path.relative_to(root)).encode("utf-8"))
        h.update(path.read_bytes())
    marker = root / ".lore-project"
    if marker.is_file():
        h.update(marker.read_bytes())
    return h.hexdigest()[:24]


def _now_id() -> str:
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    suffix = hashlib.sha256(f"{time.time_ns()}".encode()).hexdigest()[:6]
    return f"{stamp}_{suffix}"


class LoreHistoria:
    """Snapshoty w {projekt}/.lore-history/snapshots/."""

    def __init__(self, root: Path, world_name: str):
        self._root = root.resolve()
        self._world = world_name
        self._base = self._root / HISTORY_DIR
        self._snap_dir = self._base / "snapshots"
        self._last_auto = 0.0
        self._last_fingerprint: Optional[str] = None

    @property
    def katalog(self) -> Path:
        return self._base

    def kafd_path(self) -> Path:
        return self._root / f"{self._world}.kafd"

    def inicjalizuj(self) -> Path:
        """Utwórz .lore-history przy pierwszym uruchomieniu projektu."""
        self._base.mkdir(parents=True, exist_ok=True)
        self._snap_dir.mkdir(parents=True, exist_ok=True)
        readme = self._base / README_FILE
        readme.write_text(_README_PL, encoding="utf-8")
        if not self._manifest_path().is_file():
            self._save_manifest({"version": MANIFEST_VERSION, "snapshots": []})
        return self._base

    def utworz_bazowy_jesli_pusty(self) -> Optional[SnapshotInfo]:
        """Pierwszy snapshot istniejącego projektu — punkt odniesienia do cofania."""
        if self.lista():
            return None
        kafd = self.kafd_path()
        if not kafd.is_file() and not _iter_rozdzialy(self._root):
            return None
        return self.utworz(label="Stan początkowy projektu", reason="bootstrap", force=True)

    def _manifest_path(self) -> Path:
        return self._base / MANIFEST_FILE

    def _load_manifest(self) -> Dict[str, Any]:
        path = self._manifest_path()
        if not path.is_file():
            return {"version": MANIFEST_VERSION, "snapshots": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"version": MANIFEST_VERSION, "snapshots": []}
        if not isinstance(data, dict):
            return {"version": MANIFEST_VERSION, "snapshots": []}
        data.setdefault("version", MANIFEST_VERSION)
        data.setdefault("snapshots", [])
        return data

    def _save_manifest(self, data: Dict[str, Any]) -> None:
        self._base.mkdir(parents=True, exist_ok=True)
        tmp = self._manifest_path().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._manifest_path())

    def _snapshot_info(self, raw: Dict[str, Any]) -> SnapshotInfo:
        return SnapshotInfo(
            id=str(raw.get("id", "")),
            created_at=float(raw.get("created_at", 0)),
            label=str(raw.get("label", "")),
            reason=str(raw.get("reason", "")),
            fingerprint=str(raw.get("fingerprint", "")),
            files=tuple(raw.get("files") or ()),
        )

    def lista(self) -> List[SnapshotInfo]:
        manifest = self._load_manifest()
        out: List[SnapshotInfo] = []
        for row in manifest.get("snapshots") or []:
            if isinstance(row, dict) and row.get("id"):
                info = self._snapshot_info(row)
                if (self._snap_dir / info.id).is_dir():
                    out.append(info)
        return sorted(out, key=lambda s: s.created_at, reverse=True)

    def utworz(
        self,
        *,
        label: str = "",
        reason: str = "manual",
        force: bool = False,
    ) -> Optional[SnapshotInfo]:
        kafd = self.kafd_path()
        fp = _fingerprint_projektu(self._root, kafd)
        if not force and fp == self._last_fingerprint:
            return None

        snap_id = _now_id()
        dest = self._snap_dir / snap_id
        dest.mkdir(parents=True, exist_ok=True)

        copied: List[str] = []
        if kafd.is_file():
            shutil.copy2(kafd, dest / kafd.name)
            copied.append(kafd.name)

        chapters_dir = dest / "rozdzialy"
        for path in _iter_rozdzialy(self._root):
            rel = path.relative_to(self._root)
            target = chapters_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied.append(str(rel).replace("\\", "/"))

        marker = self._root / ".lore-project"
        if marker.is_file():
            shutil.copy2(marker, dest / ".lore-project")
            copied.append(".lore-project")

        info = SnapshotInfo(
            id=snap_id,
            created_at=time.time(),
            label=label.strip() or self._domyslna_etykieta(reason),
            reason=reason,
            fingerprint=fp,
            files=tuple(copied),
        )

        manifest = self._load_manifest()
        rows = list(manifest.get("snapshots") or [])
        rows.append({
            "id": info.id,
            "created_at": info.created_at,
            "label": info.label,
            "reason": info.reason,
            "fingerprint": info.fingerprint,
            "files": list(info.files),
        })
        manifest["snapshots"] = rows
        self._obetnij_stare(manifest)
        self._save_manifest(manifest)
        self._last_fingerprint = fp
        return info

    def moze_auto_snapshot(self) -> Optional[SnapshotInfo]:
        now = time.time()
        if now - self._last_auto < AUTO_MIN_INTERVAL_SEC:
            return None
        info = self.utworz(reason="auto", force=False)
        if info is not None:
            self._last_auto = now
        return info

    def przywroc(self, snap_id: str) -> SnapshotInfo:
        src = self._snap_dir / snap_id
        if not src.is_dir():
            raise FileNotFoundError(f"Nie ma snapshotu „{snap_id}”.")

        self.utworz(label=f"przed przywróceniem {snap_id}", reason="pre_restore", force=True)

        kafd = self.kafd_path()
        snap_kafd = src / kafd.name
        if snap_kafd.is_file():
            shutil.copy2(snap_kafd, kafd)

        chapters = src / "rozdzialy"
        if chapters.is_dir():
            for path in chapters.rglob("*"):
                if path.is_file():
                    rel = path.relative_to(chapters)
                    target = self._root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)

        marker = src / ".lore-project"
        if marker.is_file():
            shutil.copy2(marker, self._root / ".lore-project")

        listed = {s.id: s for s in self.lista()}
        if snap_id in listed:
            return listed[snap_id]
        return SnapshotInfo(
            id=snap_id,
            created_at=time.time(),
            label=snap_id,
            reason="restore",
            fingerprint="",
            files=(),
        )

    def _domyslna_etykieta(self, reason: str) -> str:
        mapping = {
            "auto": "Autosave projektu",
            "manual": "Punkt przywracania",
            "pre_delete": "Przed usunięciem wpisu",
            "pre_restore": "Przed przywróceniem",
            "save": "Zapis rozdziału + lore",
            "bootstrap": "Stan początkowy projektu",
        }
        return mapping.get(reason, "Snapshot")

    def _obetnij_stare(self, manifest: Dict[str, Any]) -> None:
        rows = list(manifest.get("snapshots") or [])
        if len(rows) <= MAX_SNAPSHOTS:
            return
        rows.sort(key=lambda r: float(r.get("created_at", 0)), reverse=True)
        keep = rows[:MAX_SNAPSHOTS]
        drop = rows[MAX_SNAPSHOTS:]
        manifest["snapshots"] = keep
        for row in drop:
            sid = row.get("id")
            if not sid:
                continue
            folder = self._snap_dir / str(sid)
            if folder.is_dir():
                shutil.rmtree(folder, ignore_errors=True)