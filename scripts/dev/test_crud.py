#!/usr/bin/env python3
"""Audyt CRUD: tworzenie, edycja, usuwanie — z zapisem i przeładowaniem."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.cynober_patch import LORE_PACK_KEY, read_kafd_vfs_meta
from lore.paths import ProjectPaths
from lore.store import LoreStore
from lore.types import TypLore


def reload_store(paths: ProjectPaths) -> LoreStore:
    return LoreStore.open_local(project=paths.name, project_dir=paths.root)


def check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    msg = f"  [{mark}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return ok


def main() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        paths = ProjectPaths.resolve(f"crud_{os.getpid()}", work)
        paths.write_marker()
        doc_path = str(work / "rozdzial.txt")
        Path(doc_path).write_text("Rozdział testowy.", encoding="utf-8")

        print("=== TWORZENIE ===")
        lore = LoreStore.open_local(project=paths.name, project_dir=work)

        anna = lore.dodaj_postac("Anna", notatka="Bohaterka", opis="Protagonistka")
        fails += not check("dodaj_postac Anna", anna == "Anna")
        fails += not check("Typ=Postać", lore.podglad("Anna").get("Typ") == "Postać")

        homer = lore.dodaj_wplyw("Homer", notatka="Iliada")
        fails += not check("dodaj_wplyw Homer", homer == "Homer")

        pomysl = lore.dodaj_pomysl("Mgła nad rzeką", zrodlo="test")
        fails += not check("dodaj_pomysl", pomysl.startswith("Pomysl_"))

        doc = lore.otworz_dokument(doc_path)
        fails += not check("otworz_dokument", doc == "Dok_rozdzial")
        fails += not check("Typ=Dokument", lore.podglad(doc).get("Typ") == "Dokument")

        lore.polacz("Homer", "Anna", "wpływa na")
        lore.powiaz_z_dokumentem("Anna", doc_path)
        fails += not check("relacje", "Homer" in lore.sasiedzi("Anna"))
        fails += not check(
            "Anna przy dokumencie",
            "Anna" in [x["nazwa"] for x in lore.lore_przy_dokumencie(doc_path)],
        )

        lore.zapisz()
        lore.close()

        print("\n=== PO RELOAD (tworzenie) ===")
        lore = reload_store(paths)
        fails += not check("Anna po reload", lore.encja_istnieje("Anna"))
        fails += not check("Homer po reload", lore.encja_istnieje("Homer"))
        fails += not check("pomysl po reload", lore.encja_istnieje(pomysl))
        fails += not check("dokument po reload", lore.encja_istnieje(doc))
        fails += not check(
            "szukaj Bohaterka",
            "Anna" in lore.szukaj("Bohaterka"),
        )
        fails += not check(
            "lista Postać",
            "Anna" in lore.lista_po_typie(TypLore.POSTAĆ),
        )
        lore.close()

        print("\n=== EDYCJA ===")
        lore = reload_store(paths)
        lore.ustaw("Anna", "Notatka", "Bohaterka — zaktualizowana")
        lore.ustaw("Anna", "Opis", "Teraz antagonistka")
        fails += not check(
            "edycja Notatka",
            lore.podglad("Anna").get("Notatka") == "Bohaterka — zaktualizowana",
        )
        fails += not check(
            "edycja Opis",
            lore.podglad("Anna").get("Opis") == "Teraz antagonistka",
        )
        fails += not check(
            "szukaj po edycji",
            "Anna" in lore.szukaj("zaktualizowana"),
        )

        lore.otworz_dokument(doc_path)
        fails += not check(
            "re-otworz dokument Plik",
            lore.podglad(doc).get("Plik") == "rozdzial.txt",
        )

        lore.zapisz()
        lore.close()

        print("\n=== PO RELOAD (edycja) ===")
        lore = reload_store(paths)
        anna = lore.podglad("Anna")
        fails += not check(
            "Notatka trwała",
            anna.get("Notatka") == "Bohaterka — zaktualizowana",
        )
        fails += not check(
            "Opis trwały",
            anna.get("Opis") == "Teraz antagonistka",
        )
        lore.close()

        print("\n=== USUWANIE (częściowe) ===")
        lore = reload_store(paths)
        lore.odlacz_od_dokumentu("Anna", doc_path)
        fails += not check(
            "odłącz od dokumentu",
            "Anna" not in [x["nazwa"] for x in lore.lore_przy_dokumencie(doc_path)],
        )
        fails += not check("Anna nadal istnieje", lore.encja_istnieje("Anna"))
        lore.zapisz()
        lore.close()

        print("\n=== PO RELOAD (odłączenie) ===")
        lore = reload_store(paths)
        fails += not check(
            "odłączenie trwałe",
            "Anna" not in [x["nazwa"] for x in lore.lore_przy_dokumencie(doc_path)],
        )
        fails += not check("Anna nadal w projekcie", lore.encja_istnieje("Anna"))
        lore.close()

        print("\n=== USUWANIE (trwałe) ===")
        lore = reload_store(paths)
        lore.usun_encje("Homer")
        fails += not check("usun Homer", not lore.encja_istnieje("Homer"))
        fails += not check(
            "Homer poza sąsiadami Anny",
            "Homer" not in lore.sasiedzi("Anna"),
        )

        lore.usun_encje(pomysl)
        fails += not check("usun pomysl", not lore.encja_istnieje(pomysl))

        lore.zapisz()
        lore.close()

        print("\n=== PO RELOAD (usuwanie) ===")
        lore = reload_store(paths)
        fails += not check("Homer usunięty trwale", not lore.encja_istnieje("Homer"))
        fails += not check("pomysl usunięty trwale", not lore.encja_istnieje(pomysl))
        fails += not check("Anna zostaje", lore.encja_istnieje("Anna"))
        fails += not check("dokument zostaje", lore.encja_istnieje(doc))

        vfs = read_kafd_vfs_meta(paths.world_kafd())
        pack = vfs.get(LORE_PACK_KEY) or {}
        inv = pack.get("query_indexes", {}).get("inv_index", {})
        for prop, vals in inv.items():
            for bubbles in vals.values():
                if "Homer" in bubbles or pomysl in bubbles:
                    fails += not check(f"indeks bez usuniętych ({prop})", False, str(bubbles))

        fails += not check("jeden plik kafd", paths.world_kafd().is_file())
        fails += not check(
            "brak meta.json",
            not (paths.root / f"{paths.name}.meta.json").exists(),
        )
        lore.close()

    print(f"\n=== WYNIK: {fails} błędów ===")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())