"""
Poprawki Cynober dla Lore Editor — jeden plik .kafd zamiast rozsypki po dysku.

Problem źródłowy (cynober-db v8):
  • store._n resetuje się do 0 po lazy-load → kolizja id atomów przy zapisie
  • sharding rozdziela dane na {świat}.kafd + shards/ + {świat}.meta.json

Format Lore Pack (vfs meta wewnątrz .kafd):
  lore_pack: { version, name, created_at, modified_at, bubbles, query_indexes, ... }
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any, Optional

LORE_PACK_KEY = "lore_pack"
LORE_PACK_VERSION = 1

_PATCHED = False


def configure_cynober_for_lore() -> None:
    """Jeden plik, pełny load — bez shardów i lazy-foldów w trybie pisarskim."""
    os.environ.setdefault("CYNOBER_SHARDED", "0")
    os.environ.setdefault("CYNOBER_LAZY_LOAD", "0")


def sync_atom_id_counter(store: Any) -> None:
    """Ustaw store._n za najwyższym wczytanym aN (naprawa kolizji po load)."""
    counter = getattr(store, "_n", None)
    if counter is None:
        return
    reg = getattr(store, "reg", None)
    if reg is None:
        return
    max_id = -1
    for atom in reg.atoms():
        aid = getattr(atom, "id", "")
        if isinstance(aid, str) and aid.startswith("a") and aid[1:].isdigit():
            max_id = max(max_id, int(aid[1:]))
    if max_id >= 0:
        store._n = max_id + 1


def read_kafd_vfs_meta(kafd_path: Path | str) -> dict[str, Any]:
    if not Path(kafd_path).is_file():
        return {}
    try:
        import karmazyn_store

        stats = karmazyn_store.store_stats(str(kafd_path))
        meta = stats.get("meta")
        return meta if isinstance(meta, dict) else {}
    except Exception:
        return {}


def world_meta_from_disk(base: Path, name: str) -> dict[str, Any]:
    """Metadane świata: najpierw lore_pack z .kafd, potem legacy .meta.json."""
    kafd = base / f"{name}.kafd"
    vfs = read_kafd_vfs_meta(kafd)
    pack = vfs.get(LORE_PACK_KEY)
    if isinstance(pack, dict) and pack.get("version") == LORE_PACK_VERSION:
        return dict(pack)

    sidecar = base / f"{name}.meta.json"
    if sidecar.is_file():
        try:
            import json

            data = json.loads(sidecar.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            pass
    return {}


def cleanup_legacy_sidecars(base: Path, name: str) -> None:
    """Usuń rozproszone pliki po migracji do Lore Pack."""
    sidecar = base / f"{name}.meta.json"
    if sidecar.is_file():
        sidecar.unlink(missing_ok=True)
    shard_root = base / "shards" / name
    if shard_root.is_dir():
        shutil.rmtree(shard_root, ignore_errors=True)


def save_lore_kafd(
    bridge: Any,
    kafd_path: Path | str,
    *,
    lore_pack: dict[str, Any],
    proca_dir: Path | str | None = None,
    proca_cold: bool = True,
) -> int:
    """Zapisz cały świat w jednym .kafd z osadzonym lore_pack w vfs meta."""
    from karmazyn_kafd import vfs_pack
    from karmazyn_store import (
        STORE_META,
        _apply_phi_cipher,
        _atomic_write,
        _atom_phi_vector,
        _encode_atom,
        _is_doc_atom,
        _iter_atoms,
    )

    from cynober_worlds import _proca_index_for

    store = bridge.store
    engine = bridge.engine
    proca_index = _proca_index_for(proca_dir) if proca_cold else None

    syn_ids: list[str] = []
    try:
        for nazwa, bubble in engine.api._bubble_index.items():
            syn = store.atom_new(S="__bubble__", E=nazwa, value=nazwa)
            syn.metadata["bindings"] = bubble.bindings
            syn_ids.append(syn.id)

        kinds = list({a.S for a in store.reg.atoms() if a.S})
        if "__bubble__" not in kinds:
            kinds.append("__bubble__")

        from karmazyn_atom import T_HOT

        atoms_dict: dict[str, bytes] = {}
        for atom in _iter_atoms(store):
            if not _is_doc_atom(atom, kinds):
                continue
            override_data = None
            data = atom.metadata.get("data", b"")
            if proca_index and len(data) > 0:
                use_proca = not proca_cold or float(atom.T) < T_HOT
                if use_proca:
                    phi_vec = _atom_phi_vector(store, atom)
                    typ, res = proca_index.register_or_deduplicate(
                        atom.id, data, phi_vec, float(atom.T)
                    )
                    if typ == "coordinate":
                        override_data = res.to_json_bytes()
            if override_data is not None:
                atoms_dict[atom.id] = _encode_atom(atom, override_data=override_data)
            else:
                atoms_dict[atom.id] = _encode_atom(atom)

        if proca_index:
            proca_index.save_all_sources()

        vfs_meta = {
            "format": STORE_META,
            "saved": time.time(),
            "count": len(atoms_dict),
            LORE_PACK_KEY: lore_pack,
        }
        blob = vfs_pack(atoms_dict, vfs_meta)
        encrypted = _apply_phi_cipher(blob)
        _atomic_write(str(kafd_path), encrypted)
        return len(atoms_dict)
    finally:
        for sid in syn_ids:
            store.reg.delete(sid)


def install_karmazyn_patches() -> None:
    global _PATCHED
    if _PATCHED:
        return
    import karmazyn_store

    _orig_lazy = karmazyn_store.load_documents_lazy
    _orig_full = karmazyn_store.load_documents

    def load_documents_lazy(phi, path, *args, **kwargs):
        n, folded = _orig_lazy(phi, path, *args, **kwargs)
        sync_atom_id_counter(phi)
        return n, folded

    def load_documents(phi, path, *args, **kwargs):
        n = _orig_full(phi, path, *args, **kwargs)
        sync_atom_id_counter(phi)
        return n

    karmazyn_store.load_documents_lazy = load_documents_lazy
    karmazyn_store.load_documents = load_documents
    _PATCHED = True


def apply_lore_persistence_patches() -> None:
    configure_cynober_for_lore()
    install_karmazyn_patches()


def build_lore_pack(world: Any, api: Any) -> dict[str, Any]:
    from cynober_worlds import export_query_indexes

    return {
        "version": LORE_PACK_VERSION,
        "name": world.name,
        "created_at": world.created_at,
        "modified_at": time.time(),
        "bubbles": len(api._bubble_index),
        "user_indexes": sorted(api._user_indexes),
        "query_indexes": export_query_indexes(api),
        "pack": "lore-editor",
        "sharded": False,
    }


class LoreWorldRegistry:
    """WorldRegistry z jednym plikiem .kafd (Lore Pack) i migracją ze starego formatu."""

    def __init__(self, base_dir: Optional[Path | str] = None):
        from cynober_worlds import World, WorldRegistry

        self._World = World
        self._inner = WorldRegistry(base_dir)
        self._patch_registry()

    def _patch_registry(self) -> None:
        inner = self._inner
        if getattr(inner, "_lore_patched", False):
            return

        def patched_load(name: str):
            from cynober_worlds import (
                _kafd_path,
                _load_meta,
                _meta_path,
                _proca_dir,
                load_runtime_from_kafd,
                validate_world_name,
            )

            name = validate_world_name(name)
            runtime = inner._create_runtime()
            kafd = _kafd_path(inner._base, name)
            meta = world_meta_from_disk(inner._base, name)
            legacy_sidecar = _load_meta(_meta_path(inner._base, name))
            is_legacy = bool(legacy_sidecar) and meta.get("version") != LORE_PACK_VERSION

            proca = _proca_dir(inner._base, name)
            runtime.kafd_path = kafd
            runtime.proca_dir = proca
            runtime.shard_index = {}

            if kafd.is_file():
                query_indexes = meta.get("query_indexes")
                if is_legacy:
                    from cynober_world_shards import atom_shard_paths

                    runtime.shard_index = atom_shard_paths(inner._base, name)
                    _, folded = load_runtime_from_kafd(
                        runtime.bridge,
                        kafd,
                        proca_dir=proca,
                        query_indexes=query_indexes,
                        lazy=True,
                        shard_paths=runtime.shard_index,
                    )
                    runtime.folded_atoms = folded
                else:
                    load_runtime_from_kafd(
                        runtime.bridge,
                        kafd,
                        proca_dir=proca,
                        query_indexes=query_indexes,
                        lazy=False,
                        shard_paths=None,
                    )
                    runtime.folded_atoms = set()
                sync_atom_id_counter(runtime.store)

            user_indexes = set(meta.get("user_indexes", []))
            for key in user_indexes:
                runtime.engine.api._user_indexes.add(key)

            world = self._World(
                name=name,
                runtime=runtime,
                created_at=float(meta.get("created_at", time.time())),
                modified_at=float(meta.get("modified_at", time.time())),
                user_indexes=user_indexes,
            )
            if is_legacy:
                world.dirty = True
            return world

        def patched_persist(world) -> int:
            from cynober_worlds import (
                _kafd_path,
                _proca_dir,
                rebuild_all_indexes,
            )

            with world.runtime.lock:
                rebuild_all_indexes(world.runtime.engine.api)
                kafd = _kafd_path(inner._base, world.name)
                proca = _proca_dir(inner._base, world.name)
                lore_pack = build_lore_pack(world, world.runtime.engine.api)
                saved = save_lore_kafd(
                    world.runtime.bridge,
                    kafd,
                    lore_pack=lore_pack,
                    proca_dir=proca,
                    proca_cold=True,
                )
                world.runtime.shard_index = {}
                world.runtime.folded_atoms = set()
                world.modified_at = lore_pack["modified_at"]
                world.user_indexes = set(lore_pack.get("user_indexes", []))
            cleanup_legacy_sidecars(inner._base, world.name)
            return saved

        inner._load_world = patched_load
        inner._persist = patched_persist
        inner._lore_patched = True

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


def create_world_registry(base_dir: Path | str) -> LoreWorldRegistry:
    apply_lore_persistence_patches()
    return LoreWorldRegistry(base_dir)