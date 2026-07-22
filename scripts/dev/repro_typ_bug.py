#!/usr/bin/env python3
"""Repro: czy dodaj dokument ustawia Typ=Dokument?"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.store import LoreStore
from lore.types import TypLore


def show(lore, label):
    data = lore.podglad("Dok_rozdzial")
    print(f"  [{label}] Typ={data.get('Typ')!r} Plik={data.get('Plik')!r} Opis={data.get('Opis')!r}")


with tempfile.TemporaryDirectory() as tmp:
    proj = f"repro_{os.getpid()}"
    root = Path(tmp)
    (root / "rozdzial.txt").write_text("test", encoding="utf-8")
    lore = LoreStore.open_local(project=proj, project_dir=root)
    path = str(root / "rozdzial.txt")

    print("=== krok po kroku ===")
    lore._run_line('UTRWAL "Dok_rozdzial"')
    show(lore, "po UTRWAL")

    lore._inject("Dok_rozdzial", "Typ", TypLore.DOKUMENT.value)
    show(lore, "po Typ")

    lore._inject("Dok_rozdzial", "Plik", "rozdzial.txt")
    show(lore, "po Plik")

    lore._inject("Dok_rozdzial", "Opis", "rozdzial.txt")
    show(lore, "po Opis")

    print("\n=== otworz_dokument (świeży) ===")
    lore2_root = Path(tmp) / "sub"
    lore2_root.mkdir()
    (lore2_root / "rozdzial.txt").write_text("x", encoding="utf-8")
    lore.close()

    lore = LoreStore.open_local(project=proj + "b", project_dir=root)
    doc = lore.otworz_dokument(path)
    show(lore, f"otworz_dokument -> {doc}")
    print("  lista Dokument:", lore.lista_po_typie(TypLore.DOKUMENT))
    lore.zapisz()
    lore.close()