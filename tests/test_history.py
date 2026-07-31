"""Testy historii zmian projektu."""

import os
import tempfile
import unittest
from pathlib import Path

from lore.backend import LocalLoreBackend
from lore.history import LoreHistoria
from lore.paths import ProjectPaths
from lore.store import LoreStore


class TestLoreHistoria(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._project = f"hist_{os.getpid()}"
        self._paths = ProjectPaths.resolve(self._project, self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _store(self) -> LoreStore:
        backend = LocalLoreBackend(self._paths)
        store = LoreStore(backend, self._paths)
        store._ensure_project()
        return store

    def test_snapshot_i_przywrocenie(self):
        root = self._paths.root
        ch1 = root / "rozdzial_01.txt"
        ch1.write_text("Wersja pierwsza", encoding="utf-8")

        lore = self._store()
        anna = lore.dodaj_postac("Anna", notatka="żywa")
        lore.otworz_dokument(str(ch1))
        lore.zapisz()
        snap = lore.utworz_snapshot("przed katastrofą")
        self.assertIsNotNone(snap)

        lore.ustaw(anna, "Notatka", "skasowana treść")
        ch1.write_text("Zniszczony tekst", encoding="utf-8")
        lore.zapisz(historia_auto=False)
        lore.close()

        lore = self._store()
        self.assertEqual(lore.podglad(anna).get("Notatka"), "skasowana treść")
        self.assertEqual(ch1.read_text(encoding="utf-8"), "Zniszczony tekst")

        lore.przywroc_historie(snap.id)  # type: ignore[union-attr]
        self.assertEqual(lore.podglad(anna).get("Notatka"), "żywa")
        self.assertEqual(ch1.read_text(encoding="utf-8"), "Wersja pierwsza")
        lore.close()

    def test_inicjalizacja_przy_otwarciu(self):
        lore = self._store()
        hist = self._paths.root / ".lore-history"
        self.assertTrue(hist.is_dir())
        self.assertTrue((hist / "README.txt").is_file())
        lore.close()

    def test_bootstrap_istniejacego_projektu(self):
        (self._paths.root / "rozdzial.txt").write_text("Stary tekst", encoding="utf-8")
        lore = self._store()
        snaps = lore.lista_historii()
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0].reason, "bootstrap")
        lore.close()

    def test_auto_przed_usunieciem(self):
        lore = self._store()
        lore.dodaj_postac("DoUsuniecia")
        lore.zapisz(historia_auto=False)
        before = len(lore.lista_historii())
        lore.usun_encje("DoUsuniecia")
        after = len(lore.lista_historii())
        self.assertGreater(after, before)
        lore.close()

    def test_rotacja_manifestu(self):
        import lore.history as history_mod

        old_max = history_mod.MAX_SNAPSHOTS
        history_mod.MAX_SNAPSHOTS = 3
        try:
            hist = LoreHistoria(self._paths.root, self._paths.name)
            for i in range(5):
                (self._paths.root / f"rozdzial_{i}.txt").write_text(f"tekst {i}", encoding="utf-8")
                hist.utworz(label=f"s{i}", reason="manual", force=True)
            listed = hist.lista()
            self.assertLessEqual(len(listed), 3)
            self.assertEqual(listed[0].label, "s4")
        finally:
            history_mod.MAX_SNAPSHOTS = old_max

    def test_strict_restore_usuwa_sieroty(self):
        """Pełny restore usuwa rozdziały spoza snapshota."""
        root = self._paths.root
        a = root / "a.txt"
        a.write_text("A", encoding="utf-8")
        (root / f"{self._project}.kafd").write_bytes(b"kafd-v1")
        hist = LoreHistoria(root, self._project)
        hist.inicjalizuj()
        snap = hist.utworz(label="s1", force=True)
        self.assertIsNotNone(snap)
        b = root / "b.txt"
        b.write_text("NEW", encoding="utf-8")
        a.write_text("A-mod", encoding="utf-8")

        hist.przywroc(snap.id, strict=True)
        self.assertEqual(a.read_text(encoding="utf-8"), "A")
        self.assertFalse(b.exists())

    def test_merge_restore_zostawia_nowe_pliki(self):
        root = self._paths.root
        a = root / "a.txt"
        a.write_text("A", encoding="utf-8")
        (root / f"{self._project}.kafd").write_bytes(b"kafd-v1")
        hist = LoreHistoria(root, self._project)
        hist.inicjalizuj()
        snap = hist.utworz(label="s1", force=True)
        self.assertIsNotNone(snap)
        b = root / "b.txt"
        b.write_text("NEW", encoding="utf-8")

        hist.przywroc(snap.id, strict=False)
        self.assertEqual(a.read_text(encoding="utf-8"), "A")
        self.assertTrue(b.exists())


if __name__ == "__main__":
    unittest.main()