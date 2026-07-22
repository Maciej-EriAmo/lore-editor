#!/usr/bin/env python3
"""Repro: czy zapis/odczyt psuje Typ?"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.store import LoreStore
from lore.types import TypLore


def audit(root: Path, label: str):
    meta = json.loads((root / f"{root.name}.meta.json").read_text(encoding="utf-8")) if list(root.glob("*.meta.json")) else {}
    # find meta
    metas = list(root.glob("*.meta.json"))
    if metas:
        meta = json.loads(metas[0].read_text(encoding="utf-8"))
        print(f"\n=== {label} meta inv_index.Typ ===")
        print(json.dumps(meta.get("query_indexes", {}).get("inv_index", {}).get("Typ"), ensure_ascii=False, indent=2))

    lore = LoreStore.open_local(project_dir=root)
    for name in lore.wszystkie_wpisy() or ["Dok_rozdzial"]:
        if lore.encja_istnieje(name):
            d = lore.podglad(name)
            print(f"  {name}: Typ={d.get('Typ')!r} Plik={d.get('Plik')!r}")
    print("  lista Dokument:", lore.lista_po_typie(TypLore.DOKUMENT))
    lore.close()


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "rozdzial.txt").write_text("test", encoding="utf-8")
    # use folder name as project
    from lore.paths import ProjectPaths
    paths = ProjectPaths.resolve("testproj", tmp)
    paths.write_marker()

    lore = LoreStore.open_local(project="testproj", project_dir=tmp)
    lore.otworz_dokument(str(root / "rozdzial.txt"))
    lore.dodaj_postac("Anna", notatka="bohaterka")
    lore.zapisz()
    lore.close()
    audit(Path(tmp), "po zapisie")

    # reload
    lore = LoreStore.open_local(project="testproj", project_dir=tmp)
    lore.close()
    audit(Path(tmp), "po przeładowaniu")