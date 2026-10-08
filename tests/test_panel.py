"""Testy logiki panelu lore (bez mainloop Tk)."""

import tkinter as tk
import unittest

from lore.panel import miniatura_z_bajtow, pola_do_edycji, rekord_mediow
from lore.types import POLE_NOTATKA, POLE_OPIS, POLE_TEKST, POLE_ŹRÓDŁO, TypLore

_MIN_PNG = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D,
        0xB0, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ]
)


class TestPanelEditFields(unittest.TestCase):
    def test_postac(self):
        self.assertEqual(pola_do_edycji("Postać"), (POLE_NOTATKA, POLE_OPIS))

    def test_pomysl(self):
        self.assertEqual(pola_do_edycji("Pomysł"), (POLE_TEKST, POLE_ŹRÓDŁO))

    def test_dokument(self):
        self.assertEqual(pola_do_edycji("Dokument"), (POLE_OPIS,))

    def test_nieznany_typ(self):
        self.assertIn(POLE_NOTATKA, pola_do_edycji("CosInnego"))

    def test_rekord_mediow_nie_jest_tekstem_postaci(self):
        self.assertTrue(rekord_mediow({"kind": "media", "mime": "image/png"}))
        self.assertFalse(rekord_mediow("bohaterka"))
        self.assertFalse(rekord_mediow({"kind": "notatka"}))

    def test_miniatura_png(self):
        root = tk.Tk()
        root.withdraw()
        try:
            photo = miniatura_z_bajtow(_MIN_PNG, "image/png")
            self.assertIsNotNone(photo)
            self.assertGreater(photo.width(), 0)
            self.assertIsNone(miniatura_z_bajtow(b"nie-obraz", "audio/mpeg"))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()