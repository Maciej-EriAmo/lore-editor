"""Testy LoreStore — API pisarza bez serwera."""

import os
import tempfile
import unittest
from pathlib import Path

from lore.backend import LocalLoreBackend, default_lore_worlds_dir
from lore.store import LoreStore
from lore.types import TypLore


class TestLoreStoreLocal(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["CYNOBER_WORLDS_DIR"] = self._tmp.name
        self._project = f"test_{os.getpid()}"

    def tearDown(self):
        os.environ.pop("CYNOBER_WORLDS_DIR", None)
        self._tmp.cleanup()

    def _store(self) -> LoreStore:
        wd = Path(self._tmp.name)
        backend = LocalLoreBackend(wd, self._project)
        store = LoreStore(backend, self._project)
        store._ensure_project()
        return store

    def test_dodaj_postac_i_szukaj(self):
        lore = self._store()
        lore.dodaj_postac("Anna", notatka="Bohaterka")
        hits = lore.szukaj("Bohaterka")
        self.assertIn("Anna", hits)
        lore.zapisz()
        lore.close()

    def test_dokument_i_pomysl(self):
        lore = self._store()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Rozdział pierwszy.")
            path = f.name
        try:
            lore.otworz_dokument(path)
            name = lore.wklej_pomysl_do_dokumentu("Mgła nad rzeką")
            items = lore.lore_przy_dokumencie(path)
            names = [i["nazwa"] for i in items]
            self.assertIn(name, names)
        finally:
            Path(path).unlink(missing_ok=True)
        lore.close()

    def test_polacz_wplyw(self):
        lore = self._store()
        lore.dodaj_postac("Jan")
        lore.dodaj_wplyw("Homer", notatka="Iliada")
        lore.polacz("Homer", "Jan", "wpływa na")
        neighbors = lore.sasiedzi("Jan")
        self.assertIn("Homer", neighbors)
        lore.close()

    def test_graf_powiazan(self):
        lore = self._store()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Rozdział.")
            path = f.name
        try:
            lore.otworz_dokument(path)
            anna = lore.dodaj_postac("Anna")
            lore.powiaz_z_dokumentem(anna, path)
            doc = lore.otworz_dokument(path)
            graph = lore.graf_powiazan(doc, promien=2)
            node_ids = {n["id"] for n in graph["nodes"]}
            self.assertIn(anna, node_ids)
            self.assertIn(doc, node_ids)
            self.assertTrue(any(e["from"] == anna or e["to"] == anna for e in graph["edges"]))
        finally:
            Path(path).unlink(missing_ok=True)
        lore.close()


class TestDefaultPaths(unittest.TestCase):
    def test_worlds_dir(self):
        p = default_lore_worlds_dir("demo")
        self.assertTrue(p.is_dir())


if __name__ == "__main__":
    unittest.main()