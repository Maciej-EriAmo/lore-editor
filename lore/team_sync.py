"""
Synchronizacja lore z zespołem — przez cynober-server.
Pisarz: „Wyślij projekt” / „Pobierz z serwera” / „Synchronizuj”.
Wymaga wcześniejszego lore.zapisz() — czyta z dysku, bez prywatnego API rejestru.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from cynober_replicate import PeerRegistry, pull_world, push_world, sync_world

from lore.backend import _is_loopback_host, _resolve_rpc_credentials
from lore.cynober_patch import create_world_registry
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
        self._registry = create_world_registry(self.worlds_dir)
        self._peers = PeerRegistry(self.worlds_dir)

    def _credentials(
        self,
        *,
        user: Optional[str] = None,
        token: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        return _resolve_rpc_credentials(user=user, token=token)

    def _require_auth_for_host(self, host: str, user: Optional[str], token: Optional[str]) -> None:
        """Host poza loopback bez creds → błąd (jak RPC)."""
        if user and token:
            return
        allow_anon = os.environ.get("LORE_RPC_ALLOW_ANON", "").strip().lower() in (
            "1", "true", "yes",
        )
        require = os.environ.get("LORE_RPC_REQUIRE_AUTH", "").strip().lower() in (
            "1", "true", "yes",
        )
        if allow_anon and not require:
            return
        if require or not _is_loopback_host(host):
            raise ValueError(
                "Synchronizacja z tym hostem wymaga LORE_RPC_USER + LORE_RPC_TOKEN "
                "(lub pól użytkownik/token w panelu). "
                "Dla serwera bez auth: LORE_RPC_ALLOW_ANON=1."
            )

    def ustaw_serwer(
        self,
        host: str,
        port: int = 8080,
        *,
        user: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        host = host.strip()
        if not host:
            raise ValueError("Podaj adres serwera (np. 192.168.1.10).")
        u, t = self._credentials(user=user, token=token)
        self._require_auth_for_host(host, u, t)
        self._peers.add(self.PEER_DOMYSLNY, host, int(port), user=u, token=t)

    def wyslij_na_serwer(
        self,
        host: str,
        port: int = 8080,
        *,
        user: Optional[str] = None,
        token: Optional[str] = None,
    ) -> WynikSync:
        self.ustaw_serwer(host, port, user=user, token=token)
        push_world(self._registry, self._peers, self.project, self.PEER_DOMYSLNY)
        return WynikSync(
            ok=True,
            komunikat=f"Projekt „{self.project}” wysłany na {host}:{port}.",
            kierunek="push",
        )

    def pobierz_z_serwera(
        self,
        host: str,
        port: int = 8080,
        *,
        user: Optional[str] = None,
        token: Optional[str] = None,
    ) -> WynikSync:
        self.ustaw_serwer(host, port, user=user, token=token)
        pull_world(self._registry, self._peers, self.project, self.PEER_DOMYSLNY)
        return WynikSync(
            ok=True,
            komunikat=f"Projekt „{self.project}” pobrany z {host}:{port}.",
            kierunek="pull",
        )

    def synchronizuj(
        self,
        host: str,
        port: int = 8080,
        *,
        user: Optional[str] = None,
        token: Optional[str] = None,
    ) -> WynikSync:
        self.ustaw_serwer(host, port, user=user, token=token)
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
