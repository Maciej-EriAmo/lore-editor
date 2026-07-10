"""Testy osi czasu, zapytań semantycznych, termodynamiki i zapisu transakcyjnego."""

import os
import tempfile
import unittest
from pathlib import Path

from lore.backend import LocalLoreBackend
from lore.lifecycle import Temperatura
from lore.paths import ProjectPaths
from lore.query import parsuj_zapytanie
from lore.store import LoreStore
from lore.temporal import parse_stany, scal_stan, serialize_stany
from lore.text_io import write_text_atomic
from lore.transaction import zapisz_rozdzial_i_lore
from lore.types import POLE_STANY, TypLore


class TestTemporalAndQuery(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._project = f"temporal_{os.getpid()}"
        self._paths = ProjectPaths.resolve(self._project, self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _store(self) -> LoreStore:
        backend = LocalLoreBackend(self._paths)
        store = LoreStore(backend, self._paths)
        store._ensure_project()
        return store

    def _chapter(self, lore: LoreStore, name: str, text: str = "tekst") -> tuple[str, str]:
        path = str(self._paths.root / name)
        Path(path).write_text(text, encoding="utf-8")
        doc = lore.otworz_dokument(path)
        lore.zapisz()
        return path, doc

    def test_stan_rozdzialowy_as_of(self):
        lore = self._store()
        anna = lore.dodaj_postac("Anna", notatka="sojusznik")
        p1, d1 = self._chapter(lore, "rozdzial_01.txt")
        p10, d10 = self._chapter(lore, "rozdzial_10.txt")

        lore.otworz_dokument(p1)
        lore.ustaw(anna, "Notatka", "sojusznik w akcie I")
        lore.otworz_dokument(p10)
        lore.ustaw(anna, "Notatka", "wróg bez ręki")
        lore.zapisz()
        lore.close()

        lore = self._store()
        early = lore.podglad(anna, as_of=d1)
        late = lore.podglad(anna, as_of=d10)
        self.assertIn("sojusznik", early.get("Notatka", ""))
        self.assertIn("wróg", late.get("Notatka", ""))
        self.assertNotEqual(early.get("Notatka"), late.get("Notatka"))
        lore.close()

    def test_stany_przetrwaja_reload(self):
        lore = self._store()
        anna = lore.dodaj_postac("Anna")
        path, doc = self._chapter(lore, "rozdzial_02.txt")
        lore.otworz_dokument(path)
        lore.ustaw(anna, "Opis", "stan w rozdziale 2")
        lore.zapisz()
        lore.close()

        lore = self._store()
        raw = lore.podglad(anna, surowe=True)
        stany = parse_stany(raw.get(POLE_STANY))
        self.assertIn(doc, stany)
        self.assertEqual(stany[doc].get("Opis"), "stan w rozdziale 2")
        lore.close()

    def test_zapytanie_nie_od_rozdzialu(self):
        lore = self._store()
        lok = lore.dodaj("Twierdza", TypLore.MIEJSCE)
        anna = lore.dodaj_postac("Anna")
        boris = lore.dodaj_postac("Boris")
        lore.polacz(anna, lok, "występuje w")
        lore.polacz(boris, lok, "występuje w")

        p1, d1 = self._chapter(lore, "rozdzial_01.txt")
        p2, d2 = self._chapter(lore, "rozdzial_02.txt")
        p3, d3 = self._chapter(lore, "rozdzial_03.txt")
        p4, d4 = self._chapter(lore, "rozdzial_04.txt")
        p5, d5 = self._chapter(lore, "rozdzial_05.txt")
        p6, d6 = self._chapter(lore, "rozdzial_06.txt")

        lore.powiaz_z_dokumentem(anna, p1)
        lore.powiaz_z_dokumentem(anna, p2)
        lore.powiaz_z_dokumentem(boris, p6)
        lore.zapisz()
        lore.close()

        lore = self._store()
        hits = lore.zapytaj("postacie przy Twierdza nie od 5")
        names = {h["nazwa"] for h in hits}
        self.assertIn(anna, names)
        self.assertNotIn(boris, names)
        lore.close()

    def test_parser_zapytania(self):
        q = parsuj_zapytanie('postacie przy Anna nie od 5')
        self.assertEqual(q.typ, TypLore.POSTAĆ.value)
        self.assertEqual(q.przy, "Anna")
        self.assertEqual(q.nie_od_rozdzialu, 5)

    def test_temperatura_goraca_przy_biezacym_rozdziale(self):
        lore = self._store()
        anna = lore.dodaj_postac("Anna")
        path, doc = self._chapter(lore, "rozdzial_01.txt")
        lore.powiaz_z_dokumentem(anna, path)
        lore.otworz_dokument(path)
        data = lore.podglad(anna, as_of=doc)
        self.assertEqual(data.get("_temperatura"), Temperatura.GORĄCY.value)
        lore.close()

    def test_lore_niezapisane_i_transakcja(self):
        lore = self._store()
        path = str(self._paths.root / "rozdzial.txt")
        lore.dodaj_postac("Anna")
        self.assertTrue(lore.lore_niezapisane())
        zapisz_rozdzial_i_lore(lore, path, "Treść rozdziału\n", "utf-8")
        self.assertFalse(lore.lore_niezapisane())
        self.assertTrue(Path(path).is_file())
        lore.close()

    def test_write_text_atomic(self):
        path = Path(self._paths.root) / "atom.txt"
        write_text_atomic(path, "linia 1\n", "utf-8")
        self.assertEqual(path.read_text(encoding="utf-8"), "linia 1\n")


class TestTemporalHelpers(unittest.TestCase):
    def test_scal_stan_limituje_as_of(self):
        wlasciwosci = {"Notatka": "bazowa"}
        stany = {
            "Dok_a": {"Notatka": "rozdział 1"},
            "Dok_b": {"Notatka": "rozdział 2"},
        }
        kolejnosc = [(1, "Dok_a", "a.txt"), (2, "Dok_b", "b.txt")]
        out = scal_stan(wlasciwosci, stany, as_of="Dok_a", kolejnosc=kolejnosc)
        self.assertEqual(out["Notatka"], "rozdział 1")

    def test_serialize_stany_puste_pola(self):
        raw = serialize_stany({"Dok_x": {"Notatka": "ok", "Opis": ""}})
        self.assertIn("Dok_x", raw)
        self.assertNotIn("Opis", raw)


if __name__ == "__main__":
    unittest.main()