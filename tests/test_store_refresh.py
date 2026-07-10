"""Regresje LoreStore — odświeżanie bez fałszywego dirty."""

import os
import tempfile
import unittest
from pathlib import Path

from lore.backend import LocalLoreBackend
from lore.paths import ProjectPaths
from lore.store import LoreStore


class TestStoreRefresh(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._paths = ProjectPaths.resolve(f"refresh_{os.getpid()}", self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _store(self) -> LoreStore:
        backend = LocalLoreBackend(self._paths)
        store = LoreStore(backend, self._paths)
        store._ensure_project()
        return store

    def test_otworz_dokument_drugi_raz_nie_brudzi(self):
        lore = self._store()
        path = str(self._paths.root / "rozdzial.txt")
        Path(path).write_text("Tekst", encoding="utf-8")
        lore.otworz_dokument(path)
        lore.zapisz(historia_auto=False)
        self.assertFalse(lore.lore_niezapisane())
        lore.otworz_dokument(path)
        self.assertFalse(lore.lore_niezapisane())
        lore.close(zapisz_lore=False)


if __name__ == "__main__":
    unittest.main()