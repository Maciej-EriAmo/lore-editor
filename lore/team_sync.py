"""
Synchronizacja lore z zespołem — przez cynober-server.
Pisarz: „Wyślij projekt” / „Pobierz z serwera” / „Synchronizuj”.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cynober_replicate import (
    PeerRegistry,
    export_world_payload,
    import_world_payload,
    pull_world,
    push_world,
    sync_world,
)
from cynober_worlds import WorldRegistry, validate_world_name


@dataclass
class WynikSync:
    ok: bool
    komunikat: str
    kierunek: str = ""


class ZespolLore:
    """Ukrywa PULL/PUSH/SYNC i peers.json przed pisarzem."""

    PEER_DOMYSLNY = "zespol_lore"

    def __init__(self, project: str, worlds_dir: Path | str):
        self.project = validate_world_name(project)
        self.worlds_dir = Path(worlds_dir)
        self.worlds_dir.mkdir(parents=True, exist_ok=True)
        self._registry = WorldRegistry(self.worlds_dir)
        self._peers = PeerRegistry(self.worlds_dir)

    def ustaw_serwer(self, host: str, port: int = 8080) -> None:
        host = host.strip()
        if not host:
            raise ValueError("Podaj adres serwera (np. 192.168.1.10).")
        self._peers.add(self.PEER_DOMYSLNY, host, int(port))

    def wyslij_na_serwer(self, host: str, port: int = 8080) -> WynikSync:
        """Lokalny projekt → serwer Cynober (wymaga wcześniejszego lore.zapisz())."""
        self.ustaw_serwer(host, port)
        self._ensure_flushed()
        push_world(self._registry, self._peers, self.project, self.PEER_DOMYSLNY)
        return WynikSync(
            ok=True,
            komunikat=f"Projekt „{self.project}” wysłany na {host}:{port}.",
            kierunek="push",
        )

    def pobierz_z_serwera(self, host: str, port: int = 8080) -> WynikSync:
        """Serwer → lokalny projekt (nadpisuje lokalną kopię)."""
        self.ustaw_serwer(host, port)
        info = pull_world(self._registry, self._peers, self.project, self.PEER_DOMYSLNY)
        return WynikSync(
            ok=True,
            komunikat=f"Projekt „{self.project}” pobrany z {host}:{port}.",
            kierunek="pull",
        )

    def synchronizuj(self, host: str, port: int = 8080) -> WynikSync:
        """Nowsza wersja wygrywa (wg daty modyfikacji)."""
        self.ustaw_serwer(host, port)
        self._ensure_flushed()
        info = sync_world(self._registry, self._peers, self.project, self.PEER_DOMYSLNY)
        kier = info.get("direction", "none")
        if kier == "none":
            msg = "Projekty są już zsynchronizowane."
        elif kier == "pull":
            msg = f"Zaktualizowano z serwera ({host})."
        elif kier == "push":
            msg = f"Wysłano nowszą wersję na serwer ({host})."
        else:
            msg = str(info)
        return WynikSync(ok=True, komunikat=msg, kierunek=kier)

    def eksport_lokalny(self) -> dict:
        """Diagnostyka — pełny payload (nie dla pisarza)."""
        return export_world_payload(self._registry, self.project)

    def _ensure_flushed(self) -> None:
        """Zapis na dysk, jeśli świat jest załadowany w tej instancji rejestru."""
        with self._registry._lock:
            world = self._registry._worlds.get(self.project)
        if world is not None and world.dirty:
            self._registry.flush(self.project)

    def import_lokalny(self, payload: dict) -> None:
        import_world_payload(
            self._registry,
            self.project,
            payload["kafd_b64"],
            payload.get("meta"),
            shards=payload.get("shards"),
            shard_index=payload.get("shard_index"),
        )