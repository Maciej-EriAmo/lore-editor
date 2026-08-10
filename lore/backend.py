"""Backend Cynober ukryty przed pisarzem — lokalny (in-process) lub RPC (Karmazyn/HSL)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, List, Optional, Protocol

from cynober_worlds import validate_world_name

from lore.cynober_patch import create_world_registry, sync_atom_id_counter
from lore.paths import ProjectPaths


class LoreBackendError(RuntimeError):
    pass


class EngineBackend(Protocol):
    def execute(self, script: str, *, strict: bool = False) -> List[dict]: ...
    def close(self, *, flush: bool = False) -> None: ...


def _esc(name: str) -> str:
    """Escape do cudzysłowów KarminQL (backslash + quote)."""
    return name.replace("\\", "\\\\").replace('"', '\\"')


def _last(results: List[dict]) -> dict:
    return results[-1] if results else {}


_WORLD_CREATE_RE = re.compile(r'^UTWÓRZ\s+ŚWIAT\s+"([^"]+)"$', re.IGNORECASE)
_WORLD_SELECT_RE = re.compile(
    r'^WYBIERZ\s+ŚWIAT\s+"([^"]+)"(?:\s+CEL\s+"([^"]+)"(?:\s+PROMIEŃ\s+(\d+))?)?$',
    re.IGNORECASE,
)
# Kanon lore-editor: ROZWIŃ. Aliasy: ROZWIN / ROZWIJ (cynober-server).
_UNFOLD_RE = re.compile(
    r'^ROZWI(?:Ń|N|J)\s+"([^"]+)"(?:\s+PROMIE(?:Ń|N)\s+(\d+))?$',
    re.IGNORECASE,
)

# Prefiksy mutujące stan świata — odczyty NIE powinny ustawiać dirty.
_MUTATING_PREFIXES = (
    "UTRWAL", "WSTRZYKNIJ", "ZAKTUALIZUJ", "USUŃ", "POŁĄCZ", "ROZŁĄCZ",
    "UTWÓRZ", "PRZEMIANUJ", "IMPORT", "EKSPORT", "SCAL", "BEGIN", "COMMIT",
    "ROLLBACK", "TICK", "WCZYTAJ", "ZAPISZ", "UTWÓRZ INDEKS", "USUŃ INDEKS",
    "UTWÓRZ WIDOK", "USUŃ WIDOK", "WYMAGAJ", "USUŃ WYMAGANIE",
    "ROZWIŃ", "ROZWIJ",  # ROZWIŃ = kanon; ROZWIJ = alias serwera
    "GOSSIP IMPORT", "GOSSIP SYNC",
    "MEDIA PUT", "MEDIA DELETE", "MEDIA USUŃ",
)

_READ_ONLY_PREFIXES = (
    "ZNAJDŹ", "POKAŻ", "WYPISZ", "POLICZ", "SZUKAJ", "WYJAŚNIJ", "EXPLAIN",
    "SELECT", "FIND", "SHOW", "DESCRIBE", "OPISZ", "LISTA", "STATYSTYKI",
    "GOSSIP EKSPORT", "ZDROWIE", "METRYKI",
)


def query_may_mutate(upper: str, results: list | None = None) -> bool:
    """Czy zapytanie mogło zmienić stan (i wymaga mark_dirty / flush)."""
    if results is not None and any(
        isinstance(r, dict) and r.get("status") == "error" for r in results
    ):
        return False
    u = (upper or "").strip().upper()
    if not u:
        return False
    for prefix in _READ_ONLY_PREFIXES:
        if u.startswith(prefix):
            return False
    for prefix in _MUTATING_PREFIXES:
        if u.startswith(prefix):
            return True
    # Nieznane komendy — ostrożnie: dirty tylko gdy wynik ma action mutującą
    if results:
        for r in results:
            if not isinstance(r, dict):
                continue
            action = str(r.get("action") or "")
            if action in (
                "SHOW", "FIND_WHERE", "PROJECT_WHERE", "SEARCH", "DESCRIBE_DB",
                "EXPLAIN", "STATS", "LIST_WORLDS", "ATTACH_WORLD",
            ):
                continue
            if action.startswith("AGGREGATE_"):
                continue
            if action and r.get("status") == "ok":
                return True
    return False


class LocalLoreBackend:
    """Trwały świat lore lokalnie — bez serwera TCP."""

    def __init__(self, paths: ProjectPaths):
        self._paths = paths
        self._worlds_dir = paths.root
        self._worlds_dir.mkdir(parents=True, exist_ok=True)
        # NIE ustawiamy globalnego CYNOBER_WORLDS_DIR — rejestr ma jawny base_dir.
        # Globalne env psuło izolację przy dwóch projektach / testach w jednym procesie.
        self._registry = create_world_registry(self._worlds_dir)
        self._project = paths.name
        self._world = None

    @property
    def worlds_dir(self) -> Path:
        return self._worlds_dir

    def _set_world(self, world: Any) -> Any:
        self._world = world
        sync_atom_id_counter(world.runtime.store)
        return world

    def _attach(self):
        if self._world is not None:
            return self._world
        names = {w["name"] for w in self._registry.list_worlds()}
        if self._project not in names:
            return self._set_world(self._registry.create(self._project))
        return self._set_world(self._registry.attach(self._project))

    def execute(self, script: str, *, strict: bool = False) -> List[dict]:
        line = script.strip()
        upper = line.upper()

        if upper == "LISTA ŚWIATÓW":
            return [{"status": "ok", "action": "LIST_WORLDS", "worlds": self._registry.list_worlds()}]

        m = _WORLD_CREATE_RE.match(line)
        if m:
            name = validate_world_name(m.group(1))
            if name in {w["name"] for w in self._registry.list_worlds()}:
                raise LoreBackendError(f"Projekt '{name}' już istnieje.")
            self._set_world(self._registry.create(name))
            return [{"status": "ok", "action": "CREATE_WORLD", "name": name}]

        m = _WORLD_SELECT_RE.match(line)
        if m:
            name = validate_world_name(m.group(1))
            self._set_world(self._registry.attach(name))
            info: dict = {"status": "ok", "action": "ATTACH_WORLD", "world": name}
            cel, prom = m.group(2), m.group(3)
            if cel:
                with self._world.runtime.lock:
                    from cynober_worlds import unfold_runtime

                    unfold = unfold_runtime(
                        self._world.runtime,
                        [cel],
                        radius=int(prom) if prom else None,
                    )
                info.update(unfold)
                # unfold zmienia stan w RAM — wymaga flush przy zapisie
                self._registry.mark_dirty(name)
            return [info]

        if upper == "ZAPISZ ŚWIAT":
            world = self._attach()
            saved = self._registry.flush(world.name)
            return [{"status": "ok", "action": "FLUSH_WORLD", **saved}]

        m = _UNFOLD_RE.match(line)
        if m:
            world = self._attach()
            seed = m.group(1)
            rad = int(m.group(2)) if m.group(2) else None
            from cynober_worlds import unfold_runtime

            with world.runtime.lock:
                unfold = unfold_runtime(
                    world.runtime,
                    [seed],
                    radius=rad,
                )
            # Dirty tylko gdy faktycznie wczytano zwinięte atomy (lazy pack).
            loaded = int(unfold.get("unfolded_atoms") or 0)
            if loaded > 0:
                self._registry.mark_dirty(world.name)
            return [{"status": "ok", "action": "UNFOLD", **unfold}]

        if upper == "STATYSTYKI":
            world = self._attach()
            stats = world.runtime.engine.api.store.stats()
            return [{
                "status": "ok",
                "action": "STATS",
                "data": {
                    "world": world.name,
                    "bubbles": len(world.runtime.engine.api._bubble_index),
                    "total_atoms": stats["total"],
                },
            }]

        world = self._attach()
        with world.runtime.lock:
            results = world.runtime.engine.execute(line, strict=strict)
        if query_may_mutate(upper, results):
            self._registry.mark_dirty(world.name)
        return results

    def reload(self) -> None:
        """Przeładuj świat z dysku (po przywróceniu snapshotu)."""
        if self._world is not None:
            self._world.dirty = False
            try:
                self._registry.release(self._world.name)
            except ValueError:
                pass
            self._world = None
        self._registry = create_world_registry(self._worlds_dir)
        self._attach()

    def close(self, *, flush: bool = False) -> None:
        """
        Zwolnij świat. Domyślnie **bez** flush — inaczej close(zapisz_lore=False)
        i tak zapisywałoby dirty (krytyczny bug).
        Zapis: store.zapisz() / close(flush=True) / ZAPISZ ŚWIAT.
        """
        if self._world is not None:
            flush_err: Exception | None = None
            try:
                if flush and self._world.dirty:
                    self._registry.flush(self._world.name)
                elif not flush and self._world.dirty:
                    # porzuć zmiany w RAM — kolejne attach wczyta z dysku
                    self._world.dirty = False
            except (ValueError, OSError) as e:
                flush_err = e
            try:
                self._registry.release(self._world.name)
            except ValueError:
                pass
            self._world = None
            if flush_err is not None:
                raise LoreBackendError(f"Nie zapisano świata przy zamykaniu: {flush_err}") from flush_err


class RpcLoreBackend:
    """
    Lore na cynober-server (TCP L0 + protokół Karmazyn HSS/HSL, nie HTTP/SQL).
    Rozdziały nadal lokalne na dysku pisarza. Media: put_media/get_media (KAFS).
    """

    def __init__(self, client: Any):
        from cynober_rpc import parse_response_payload

        self._client = client
        self._parse = parse_response_payload
        self._auth_user: str | None = None

    @property
    def client(self) -> Any:
        """SDK CynoberClient (session_info, put_media, query)."""
        return self._client

    def session_info(self) -> dict:
        """Metadane tunelu (L0, KAFS, HSL, KPC) — wymaga cynober-db z session_info()."""
        fn = getattr(self._client, "session_info", None)
        if callable(fn):
            return dict(fn())
        return {
            "connected": True,
            "kafs_enabled": bool(getattr(self._client, "kafs_enabled", False)),
            "legacy_client": True,
        }

    def kafs_enabled(self) -> bool:
        return bool(getattr(self._client, "kafs_enabled", False))

    def login(self, user: str, token: str) -> None:
        """ZALOGUJ na serwerze z włączonym auth.json."""
        user = (user or "").strip()
        token = (token or "").strip()
        if not user or not token:
            raise LoreBackendError("RPC login: wymagane user i token.")
        results = self.execute(
            f'ZALOGUJ "{_esc(user)}" TOKEN "{_esc(token)}"',
            strict=True,
        )
        row = _last(results)
        if row.get("status") != "ok":
            raise LoreBackendError(row.get("message") or "Logowanie RPC nieudane.")
        self._auth_user = user

    def execute(self, script: str, *, strict: bool = False) -> List[dict]:
        # cynober-server rozumie historyczne ROZWIJ; lokalnie kanon to ROZWIŃ
        if not getattr(self._client, "sock", None) and not callable(
            getattr(self._client, "query", None)
        ):
            raise LoreBackendError("RPC: brak aktywnego klienta.")
        wire = _normalize_rpc_script(script)
        try:
            payload = self._client.query(wire)
        except Exception as e:
            # CynoberClientError i błędy tunelu → czytelny komunikat lore
            raise LoreBackendError(f"Tunel RPC: {e}") from e
        results, transport_err = self._parse(payload)
        if transport_err:
            raise LoreBackendError(transport_err)
        for row in results:
            if row.get("status") == "error":
                msg = row.get("message", "nieznany błąd")
                if strict:
                    raise LoreBackendError(msg)
        return results

    def close(self, *, flush: bool = False) -> None:
        # flush ignorowany — stan świata jest po stronie serwera (ZAPISZ ŚWIAT w store.zapisz)
        try:
            self._client.close()
        except Exception:
            pass


def _normalize_rpc_script(script: str) -> str:
    """ROZWIŃ → ROZWIJ na drucie (regex serwera cynober)."""
    line = (script or "").strip()
    m = _UNFOLD_RE.match(line)
    if not m:
        return script
    seed = m.group(1)
    rad = m.group(2)
    if rad:
        return f'ROZWIJ "{_esc(seed)}" PROMIEŃ {int(rad)}'
    return f'ROZWIJ "{_esc(seed)}"'


def _is_loopback_host(host: str) -> bool:
    h = (host or "").strip().lower()
    return h in ("127.0.0.1", "localhost", "::1", "0.0.0.0")


def default_lore_worlds_dir(project_name: str = "default") -> Path:
    """Kompatybilność wsteczna — preferuj ProjectPaths.resolve()."""
    return ProjectPaths.resolve(project_name).root


def connect_local(paths: ProjectPaths) -> LocalLoreBackend:
    return LocalLoreBackend(paths)


def _resolve_rpc_credentials(
    *,
    user: Optional[str] = None,
    token: Optional[str] = None,
    profile: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """user/token: argumenty → env → profil cynober-client."""
    u = (user or "").strip() or os.environ.get("LORE_RPC_USER", "").strip()
    t = (token or "").strip() or os.environ.get("LORE_RPC_TOKEN", "").strip()
    if not u:
        u = os.environ.get("CYNOBER_USER", "").strip()
    if not t:
        t = os.environ.get("CYNOBER_TOKEN", "").strip()
    if not u or not t:
        try:
            from cynober_client_config import get_active_profile, load_config

            cfg = load_config()
            if profile:
                prof = cfg.get("profiles", {}).get(profile) or {}
            else:
                _, prof = get_active_profile(cfg)
            if isinstance(prof, dict):
                if not u:
                    u = str(prof.get("user") or prof.get("username") or "").strip()
                if not t:
                    t = str(prof.get("token") or prof.get("password") or "").strip()
        except Exception:
            pass
    return (u or None, t or None)


def connect_rpc(
    host: str = "127.0.0.1",
    port: int = 8080,
    *,
    profile: Optional[str] = None,
    user: Optional[str] = None,
    token: Optional[str] = None,
    login: bool = True,
    require_auth: Optional[bool] = None,
) -> RpcLoreBackend:
    """
    Połączenie RPC z cynober-server.

    Auth:
      • gdy są user+token → ZALOGUJ
      • host nie-lokalny bez creds → błąd (fail-fast), chyba że
        LORE_RPC_ALLOW_ANON=1 albo require_auth=False
      • loopback bez creds → dozwolone (dev), chyba że LORE_RPC_REQUIRE_AUTH=1
    """
    from cynober_client import CynoberClientError, connect

    try:
        client = connect(profile=profile) if profile else connect(host, port)
    except CynoberClientError as e:
        raise LoreBackendError(
            f"Nie połączono z cynober-server ({host}:{port}): {e}. "
            "Sprawdź czy serwer działa, profil HSS i wersję protokołu (Cynober-Secure-1.2)."
        ) from e
    except OSError as e:
        raise LoreBackendError(
            f"Sieć: nie można dotrzeć do {host}:{port}: {e}"
        ) from e

    backend = RpcLoreBackend(client)
    # Media (portrety) wymagają KAFS — ostrzeżenie wcześnie, nie przy pierwszym pliku
    if not backend.kafs_enabled():
        import warnings

        warnings.warn(
            "Sesja RPC bez kafs-stream — dołączanie grafik (put_media) nie zadziała. "
            "Zaktualizuj cynober-db (serwer + klient).",
            UserWarning,
            stacklevel=2,
        )
    if login:
        u, t = _resolve_rpc_credentials(user=user, token=token, profile=profile)
        if u and t:
            backend.login(u, t)
        else:
            env_require = os.environ.get("LORE_RPC_REQUIRE_AUTH", "").strip().lower() in (
                "1", "true", "yes",
            )
            env_allow_anon = os.environ.get("LORE_RPC_ALLOW_ANON", "").strip().lower() in (
                "1", "true", "yes",
            )
            if require_auth is None:
                must = env_require or (not _is_loopback_host(host) and not env_allow_anon)
            else:
                must = bool(require_auth)
            if must:
                raise LoreBackendError(
                    "RPC: wymagane logowanie (LORE_RPC_USER + LORE_RPC_TOKEN "
                    "lub --rpc-user / --rpc-token). "
                    "Dla serwera bez auth: LORE_RPC_ALLOW_ANON=1."
                )
    return backend