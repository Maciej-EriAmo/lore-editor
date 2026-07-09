"""Backend Cynober ukryty przed pisarzem — lokalny (WorldRegistry) lub RPC."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, List, Optional, Protocol

from cynober_worlds import WorldRegistry, validate_world_name


class LoreBackendError(RuntimeError):
    pass


class _EngineBackend(Protocol):
    def execute(self, script: str, *, strict: bool = False) -> List[dict]: ...
    def close(self) -> None: ...


def _esc(name: str) -> str:
    return name.replace("\\", "\\\\").replace('"', '\\"')


def _last(results: List[dict]) -> dict:
    return results[-1] if results else {}


_WORLD_CREATE_RE = re.compile(r'^UTWÓRZ\s+ŚWIAT\s+"([^"]+)"$', re.IGNORECASE)
_WORLD_SELECT_RE = re.compile(
    r'^WYBIERZ\s+ŚWIAT\s+"([^"]+)"(?:\s+CEL\s+"([^"]+)"(?:\s+PROMIEŃ\s+(\d+))?)?$',
    re.IGNORECASE,
)


class LocalLoreBackend:
    """Trwały świat lore lokalnie — bez serwera TCP."""

    def __init__(self, worlds_dir: Path | str, project: str):
        self._worlds_dir = Path(worlds_dir)
        self._worlds_dir.mkdir(parents=True, exist_ok=True)
        os.environ["CYNOBER_WORLDS_DIR"] = str(self._worlds_dir.resolve())
        self._registry = WorldRegistry(self._worlds_dir)
        self._project = validate_world_name(project)
        self._world = None

    def _attach(self):
        if self._world is not None:
            return self._world
        names = {w["name"] for w in self._registry.list_worlds()}
        if self._project not in names:
            self._world = self._registry.create(self._project)
        else:
            self._world = self._registry.attach(self._project)
        return self._world

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
            self._world = self._registry.create(name)
            return [{"status": "ok", "action": "CREATE_WORLD", "name": name}]

        m = _WORLD_SELECT_RE.match(line)
        if m:
            name = validate_world_name(m.group(1))
            self._world = self._registry.attach(name)
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
            return [info]

        if upper == "ZAPISZ ŚWIAT":
            world = self._attach()
            saved = self._registry.flush(world.name)
            return [{"status": "ok", "action": "FLUSH_WORLD", **saved}]

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
        self._registry.mark_dirty(world.name)
        return results

    def close(self) -> None:
        if self._world is not None:
            try:
                if self._world.dirty:
                    self._registry.flush(self._world.name)
            except ValueError:
                pass
            self._registry.release(self._world.name)
            self._world = None


class RpcLoreBackend:
    """Zespół przez cynober-server — pisarz nadal nie widzi KarminQL."""

    def __init__(self, client: Any):
        from cynober_rpc import parse_response_payload

        self._client = client
        self._parse = parse_response_payload

    def execute(self, script: str, *, strict: bool = False) -> List[dict]:
        payload = self._client.query(script)
        results, transport_err = self._parse(payload)
        if transport_err:
            raise LoreBackendError(transport_err)
        for row in results:
            if row.get("status") == "error":
                msg = row.get("message", "nieznany błąd")
                if strict:
                    raise LoreBackendError(msg)
        return results

    def close(self) -> None:
        self._client.close()


def default_lore_worlds_dir(project_name: str = "default") -> Path:
    base = Path.home() / ".lore_editor" / "worlds" / project_name
    base.mkdir(parents=True, exist_ok=True)
    return base


def connect_local(project_name: str = "default") -> LocalLoreBackend:
    wd = default_lore_worlds_dir(project_name)
    return LocalLoreBackend(wd, project_name)


def connect_rpc(
    host: str = "127.0.0.1",
    port: int = 8080,
    *,
    profile: Optional[str] = None,
) -> RpcLoreBackend:
    from cynober_client import connect

    client = connect(profile=profile) if profile else connect(host, port)
    return RpcLoreBackend(client)