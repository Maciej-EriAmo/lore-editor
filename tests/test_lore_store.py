"""Testy LoreStore — API pisarza bez serwera."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lore.backend import LocalLoreBackend, LoreBackendError
from lore.paths import ProjectPaths
from lore.store import LoreStore


class TestLoreStoreLocal(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._project = f"test_{os.getpid()}"
        self._paths = ProjectPaths.resolve(self._project, self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _store(self) -> LoreStore:
        backend = LocalLoreBackend(self._paths)
        store = LoreStore(backend, self._paths)
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
        path = str(self._paths.root / "rozdzial_01.txt")
        Path(path).write_text("Rozdział pierwszy.", encoding="utf-8")
        lore.otworz_dokument(path)
        name = lore.wklej_pomysl_do_dokumentu("Mgła nad rzeką")
        items = lore.lore_przy_dokumencie(path)
        names = [i["nazwa"] for i in items]
        self.assertIn(name, names)
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
        path = str(self._paths.root / "rozdzial.txt")
        Path(path).write_text("Rozdział.", encoding="utf-8")
        lore.otworz_dokument(path)
        anna = lore.dodaj_postac("Anna")
        lore.powiaz_z_dokumentem(anna, path)
        doc = lore.otworz_dokument(path)
        graph = lore.graf_powiazan(doc, promien=2)
        node_ids = {n["id"] for n in graph["nodes"]}
        self.assertIn(anna, node_ids)
        self.assertIn(doc, node_ids)
        self.assertTrue(any(e["from"] == anna or e["to"] == anna for e in graph["edges"]))
        lore.close()

    def test_dokument_rozne_sciezki(self):
        """Dwa pliki o tej samej nazwie w różnych podfolderach — różne bąble."""
        lore = self._store()
        (self._paths.root / "akt1").mkdir()
        (self._paths.root / "akt2").mkdir()
        p1 = str(self._paths.root / "akt1" / "intro.txt")
        p2 = str(self._paths.root / "akt2" / "intro.txt")
        Path(p1).write_text("Akt I", encoding="utf-8")
        Path(p2).write_text("Akt II", encoding="utf-8")
        d1 = lore.otworz_dokument(p1)
        d2 = lore.otworz_dokument(p2)
        self.assertNotEqual(d1, d2)
        lore.close()

    def test_pomysl_powiazany_przez_sciezke(self):
        lore = self._store()
        path = str(self._paths.root / "rozdzial.txt")
        Path(path).write_text("Rozdział.", encoding="utf-8")
        name = lore.wklej_pomysl_do_dokumentu("Mgła nad rzeką", sciezka_pliku=path)
        items = lore.lore_przy_dokumencie(path)
        self.assertIn(name, [i["nazwa"] for i in items])
        lore.close()

    def test_sasiedzi_bidirekcja(self):
        lore = self._store()
        lore.dodaj_postac("Anna")
        lore.dodaj_postac("Boris")
        lore.polacz("Anna", "Boris", "koliguje z")
        self.assertIn("Boris", lore.sasiedzi("Anna"))
        self.assertIn("Anna", lore.sasiedzi("Boris"))
        lore.close()

    def test_powiaz_wymaga_istniejacej_encji(self):
        lore = self._store()
        path = str(self._paths.root / "rozdzial.txt")
        Path(path).write_text("Rozdział.", encoding="utf-8")
        lore.otworz_dokument(path)
        with self.assertRaises(LoreBackendError):
            lore.powiaz_z_dokumentem("Nieistniejacy", path)
        lore.close()

    def test_usun_encje(self):
        lore = self._store()
        lore.dodaj_postac("DoUsuniecia", notatka="test")
        self.assertIn("DoUsuniecia", lore.szukaj("test"))
        lore.usun_encje("DoUsuniecia")
        self.assertNotIn("DoUsuniecia", lore.szukaj("test"))
        lore.close()

    def test_odlacz_od_dokumentu(self):
        lore = self._store()
        path = str(self._paths.root / "rozdzial.txt")
        Path(path).write_text("Rozdział.", encoding="utf-8")
        lore.otworz_dokument(path)
        anna = lore.dodaj_postac("Anna")
        lore.powiaz_z_dokumentem(anna, path)
        self.assertIn(anna, [i["nazwa"] for i in lore.lore_przy_dokumencie(path)])
        lore.odlacz_od_dokumentu(anna, path)
        self.assertNotIn(anna, [i["nazwa"] for i in lore.lore_przy_dokumencie(path)])
        self.assertEqual(lore.podglad(anna).get("Typ"), "Postać")
        lore.close()

    def test_plik_wzgledny_w_projekcie(self):
        lore = self._store()
        path = str(self._paths.root / "rozdzial.txt")
        Path(path).write_text("Tekst", encoding="utf-8")
        doc = lore.otworz_dokument(path)
        data = lore.podglad(doc)
        self.assertEqual(data.get("Plik"), "rozdzial.txt")
        lore.close()


class TestProjectPaths(unittest.TestCase):
    def test_resolve_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = ProjectPaths.resolve("demo", tmp)
            self.assertTrue(p.root.is_dir())
            self.assertEqual(p.name, "demo")

    def test_plik_wzgledny(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = ProjectPaths.resolve("demo", tmp)
            inside = Path(tmp) / "rozdzial.txt"
            self.assertEqual(p.plik_wzgledny(inside), "rozdzial.txt")


class TestOpenRpc(unittest.TestCase):
    @patch("lore.store.connect_rpc")
    def test_open_rpc_factory(self, mock_connect):
        mock_backend = MagicMock()
        mock_backend.execute.side_effect = [
            [{"status": "ok", "worlds": [{"name": "demo"}]}],
            [{"status": "ok"}],
            [{"status": "ok"}],
        ]
        mock_connect.return_value = mock_backend

        with tempfile.TemporaryDirectory() as tmp:
            lore = LoreStore.open_rpc("demo", "127.0.0.1", 8080, project_dir=tmp)
            self.assertFalse(lore.tryb_lokalny())
            self.assertEqual(lore.katalog_projektu(), Path(tmp).resolve())
            lore.close()


if __name__ == "__main__":
    unittest.main()