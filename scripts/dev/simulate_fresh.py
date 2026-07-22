#!/usr/bin/env python3
"""Symulacja: pusty projekt → otwórz rozdzial → zapisz → sprawdź meta."""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.paths import ProjectPaths
from lore.store import LoreStore

tmp = tempfile.mkdtemp()
work = Path(tmp)
(work / "rozdzial.txt").write_text("stoi", encoding="utf-8")
paths = ProjectPaths.resolve("lore-editor", work)
paths.write_marker()

def read_meta():
    p = work / "lore-editor.meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None

path = str(work / "rozdzial.txt")
lore = LoreStore.open_local(project="lore-editor", project_dir=work)
lore.otworz_dokument(path)
d = lore.podglad("Dok_rozdzial")
print("PRZED zapisz:", d)
lore.zapisz()
lore.close()

meta = read_meta()
print("\nMETA inv_index Typ:", json.dumps(meta["query_indexes"]["inv_index"].get("Typ"), ensure_ascii=False))
print("META bubbles:", meta.get("bubbles"))

lore2 = LoreStore.open_local(project="lore-editor", project_dir=work)
d2 = lore2.podglad("Dok_rozdzial")
print("\nPO RELOAD podglad:", d2)
print("lista Dokument:", lore2.lista_po_typie("Dokument"))
lore2.close()