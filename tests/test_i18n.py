"""Locale packs + i18n API."""

from __future__ import annotations

import unittest

from lore.i18n import discover_and_load, get_locale, list_locales, set_locale, t
from lore.i18n.core import load_locale_dir
from pathlib import Path


class TestI18n(unittest.TestCase):
    def setUp(self) -> None:
        discover_and_load(force=True)
        set_locale("pl", persist=False)

    def test_pl_default_menu(self) -> None:
        set_locale("pl", persist=False)
        self.assertEqual(t("menu.file"), "Plik")

    def test_english_pack(self) -> None:
        set_locale("en", persist=False)
        self.assertEqual(get_locale(), "en")
        self.assertEqual(t("menu.file"), "File")
        self.assertEqual(t("file.save"), "Save")

    def test_klingon_plugin_discovered(self) -> None:
        codes = {p.code for p in list_locales()}
        self.assertIn("tlh", codes)
        set_locale("tlh", persist=False)
        self.assertEqual(t("menu.file"), "teywI'")

    def test_fallback_unknown_key(self) -> None:
        set_locale("en", persist=False)
        # klucz tylko w PL wbudowanym
        self.assertTrue(len(t("app.ready")) > 0)

    def test_load_locale_dir_roundtrip(self) -> None:
        root = Path(__file__).resolve().parents[1] / "lore" / "locales" / "en"
        pack = load_locale_dir(root, source="test")
        self.assertIsNotNone(pack)
        assert pack is not None
        self.assertEqual(pack.code, "en")


class TestDirtyOnRead(unittest.TestCase):
    def test_find_does_not_mark_dirty(self) -> None:
        import tempfile

        from lore.store import LoreStore

        with tempfile.TemporaryDirectory() as tmp:
            s = LoreStore.open_local(project="dirty_probe", project_dir=tmp)
            s._dirty = False
            w = s._backend._world
            if w is not None:
                w.dirty = False
            s._run_line('ZNAJDŹ GDZIE "Typ" = "Postać"', strict=False)
            w = s._backend._world
            self.assertFalse(getattr(w, "dirty", True))
            s.close(zapisz_lore=False)

    def test_discard_close_does_not_persist(self) -> None:
        """Regresja: close(zapisz_lore=False) NIE może flushować dirty świata."""
        import tempfile

        from lore.store import LoreStore

        with tempfile.TemporaryDirectory() as tmp:
            s = LoreStore.open_local(project="discard_probe", project_dir=tmp)
            s.dodaj_postac("Ala")
            s.zapisz()
            s.dodaj_postac("Bob")
            self.assertTrue(s.lore_niezapisane())
            s.close(zapisz_lore=False)

            s2 = LoreStore.open_local(project="discard_probe", project_dir=tmp)
            names = s2.lista_po_typie("Postać")
            self.assertIn("Ala", names)
            self.assertNotIn("Bob", names)
            s2.close(zapisz_lore=False)

    def test_two_projects_no_env_collision(self) -> None:
        """Dwa lokalne backendy nie powinny polegać na globalnym CYNOBER_WORLDS_DIR."""
        import os
        import tempfile

        from lore.store import LoreStore

        prev = os.environ.pop("CYNOBER_WORLDS_DIR", None)
        try:
            with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
                sa = LoreStore.open_local(project="projA", project_dir=a)
                sb = LoreStore.open_local(project="projB", project_dir=b)
                sa.dodaj_postac("OnlyA")
                sa.zapisz()
                sb.dodaj_postac("OnlyB")
                sb.zapisz()
                self.assertIn("OnlyA", sa.lista_po_typie("Postać"))
                self.assertNotIn("OnlyA", sb.lista_po_typie("Postać"))
                self.assertIn("OnlyB", sb.lista_po_typie("Postać"))
                self.assertNotIn("OnlyB", sa.lista_po_typie("Postać"))
                # nie ustawiamy env przy starcie
                self.assertNotEqual(os.environ.get("CYNOBER_WORLDS_DIR"), str(sa.katalog_projektu()))
                sa.close(zapisz_lore=False)
                sb.close(zapisz_lore=False)
        finally:
            if prev is not None:
                os.environ["CYNOBER_WORLDS_DIR"] = prev


if __name__ == "__main__":
    unittest.main()
