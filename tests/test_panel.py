"""Testy logiki panelu lore (bez mainloop Tk)."""

import unittest

from lore.panel import pola_do_edycji
from lore.types import POLE_NOTATKA, POLE_OPIS, POLE_TEKST, POLE_ŹRÓDŁO, TypLore


class TestPanelEditFields(unittest.TestCase):
    def test_postac(self):
        self.assertEqual(pola_do_edycji("Postać"), (POLE_NOTATKA, POLE_OPIS))

    def test_pomysl(self):
        self.assertEqual(pola_do_edycji("Pomysł"), (POLE_TEKST, POLE_ŹRÓDŁO))

    def test_dokument(self):
        self.assertEqual(pola_do_edycji("Dokument"), (POLE_OPIS,))

    def test_nieznany_typ(self):
        self.assertIn(POLE_NOTATKA, pola_do_edycji("CosInnego"))


if __name__ == "__main__":
    unittest.main()