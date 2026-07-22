#!/usr/bin/env python3
"""Głęboki audyt — bezpośredni dostęp do bubble_index Cynober."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.paths import ProjectPaths
from lore.backend import connect_local


def main() -> None:
    paths = ProjectPaths.discover(project_dir=ROOT)
    backend = connect_local(paths)
    world = backend._attach()
    api = world.runtime.engine.api

    print("=== bubble_index ===")
    for name, bubble in sorted(api._bubble_index.items()):
        print(f"\n{name}:")
        for key, atom_id in sorted(bubble.bindings.items()):
            atom = api.store.get_atom(atom_id) if atom_id else None
            val = None
            if atom:
                val = atom.metadata.get("v", getattr(atom, "E", None))
            print(f"  {key} → {atom_id} = {val!r}")

    print("\n=== inv_index (runtime) ===")
    for key, vals in sorted(api._inv_index.items()):
        for val, bubs in sorted(vals.items()):
            print(f"  {key}: {val!r} → {sorted(bubs)}")

    print("\n=== atom_index (runtime) ===")
    for aid, bubs in sorted(api._atom_index.items()):
        print(f"  {aid} → {sorted(bubs)}")

    print("\n=== POKAŻ queries ===")
    for name in sorted(api._bubble_index.keys()):
        rows = backend.execute(f'POKAŻ "{name}"', strict=False)
        row = rows[-1] if rows else {}
        data = row.get("data") or row.get("bubble") or {}
        if isinstance(data, dict) and "properties" in data:
            props = data.get("properties", {})
            rels = data.get("relations", [])
        else:
            props = data if isinstance(data, dict) else {}
            rels = []
        print(f"  {name}: props={props}, rels={rels}")

    print("\n=== ZNAJDŹ GDZIE Typ ===")
    for typ in ("Postać", "Dokument", "Pomysł", "Wpływ"):
        rows = backend.execute(f'ZNAJDŹ GDZIE "Typ" = "{typ}"', strict=False)
        print(f"  Typ={typ}: {rows[-1].get('matches') if rows else []}")

    meta = json.loads((ROOT / "lore-editor.meta.json").read_text(encoding="utf-8"))
    shard_idx = json.loads((ROOT / "shards" / "lore-editor" / "index.json").read_text(encoding="utf-8"))
    print("\n=== shard_index sync ===")
    print(f"  meta == index.json: {meta.get('shard_index') == shard_idx}")

    backend.close()


if __name__ == "__main__":
    main()