"""
Synchronizacja lore z zespołem — przez cynober-server.
Pisarz: „Wyślij projekt” / „Pobierz z serwera” / „Synchronizuj”.
Wymaga wcześniejszego lore.zapisz() — czyta z dysku, bez prywatnego API rejestru.
"""

from __future__ import annotations

from dataclasses import dataclass

from cynober_replicate import PeerRegistry, pull_world, push_world, sync_world
from cynober_worlds import WorldRegistry

from lore.paths import ProjectPaths


@dataclass
class WynikSync:
    ok: bool
    komunikat: str
    kierunek: str = ""


class ZespolLore:
    """Ukrywa PULL/PUSH/SYNC i peers.json przed pisarzem."""

    PEER_DOMYSLNY = "zespol_lore"

    def __init__(self, paths: ProjectPaths):
        self._paths = paths
        self.project = paths.name
        self.worlds_dir = paths.root
        self.worlds_dir.mkdir(parents=True, exist_ok=True)
        self._registry = WorldRegistry(self.worlds_dir)
        self._peers = PeerRegistry(self.worlds_dir)

    def ustaw_serwer(self, host: str, port: int = 8080) -> None:
        host = host.strip()
        if not host:
            raise ValueError("Podaj adres serwera (np. 192.168.1.10).")
        self._peers.add(self.PEER_DOMYSLNY, host, int(port))

    def wyslij_na_serwer(self, host: str, port: int = 8080) -> WynikSync:
        self.ustaw_serwer(host, port)
        push_world(self._registry, self._peers, self.project, self.PEER_DOMYSLNY)
        return WynikSync(
            ok=True,
            komunikat=f"Projekt „{self.project}” wysłany na {host}:{port}.",
            kierunek="push",
        )

    def pobierz_z_serwera(self, host: str, port: int = 8080) -> WynikSync:
        self.ustaw_serwer(host, port)
        pull_world(self._registry, self._peers, self.project, self.PEER_DOMYSLNY)
        return WynikSync(
            ok=True,
            komunikat=f"Projekt „{self.project}” pobrany z {host}:{port}.",
            kierunek="pull",
        )

    def synchronizuj(self, host: str, port: int = 8080) -> WynikSync:
        self.ustaw_serwer(host, port)
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