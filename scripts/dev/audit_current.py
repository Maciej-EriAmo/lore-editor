#!/usr/bin/env python3
"""Stan projektu lore-editor — pliki + runtime."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.cynober_patch import read_kafd_vfs_meta, world_meta_from_disk
from lore.paths import ProjectPaths
from lore.store import LoreStore
from lore.types import TypLore


def main():
    print("=== PLIKI PROJEKTU ===")
    for pattern in ["*.txt", "*.md", "*.kafd", "*.meta.json", ".lore-project"]:
        for p in sorted(ROOT.glob(pattern)):
            print(f"  {p.name}: {p.stat().st_size} B")
    shards = ROOT / "shards"
    if shards.is_dir():
        for p in sorted(shards.rglob("*")):
            if p.is_file():
                print(f"  {p.relative_to(ROOT)}: {p.stat().st_size} B")
    else:
        print("  shards/: brak")

    kafd = ROOT / "lore-editor.kafd"
    if kafd.is_file():
        vfs = read_kafd_vfs_meta(kafd)
        pack = vfs.get("lore_pack") or world_meta_from_disk(ROOT, "lore-editor")
        print("\n=== LORE PACK / META ===")
        print(json.dumps(pack, ensure_ascii=False, indent=2) if pack else "  (pusty)")
    else:
        print("\n=== brak lore-editor.kafd ===")

    print("\n=== RUNTIME ===")
    try:
        paths = ProjectPaths.discover(project_dir=ROOT)
        lore = LoreStore.open_local(project_dir=ROOT)
        print(f"  projekt: {lore.nazwa_projektu()}")
        print(f"  wpisy: {lore.wszystkie_wpisy()}")
        for name in lore.wszystkie_wpisy():
            d = lore.podglad(name)
            rels = d.pop("_relations", [])
            d.pop("BĄBEL", None)
            print(f"  {name}: {d}")
            for r in rels:
                print(f"    rel: {r}")
        print(f"  Dokumenty: {lore.lista_po_typie(TypLore.DOKUMENT)}")
        print(f"  Postacie: {lore.lista_po_typie(TypLore.POSTAĆ)}")
        lore.close()
    except Exception as e:
        print(f"  BŁĄD: {e}")


if __name__ == "__main__":
    main()