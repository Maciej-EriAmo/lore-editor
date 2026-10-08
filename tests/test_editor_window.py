"""Testy logiki edytora (bez mainloop)."""

import unittest

from lore.editor_window import _word_count, karty_bez_pliku


class TestEditorWindow(unittest.TestCase):
    def test_word_count_basic(self):
        self.assertEqual(_word_count("jeden dwa trzy"), 3)

    def test_word_count_empty(self):
        self.assertEqual(_word_count(""), 0)
        self.assertEqual(_word_count("   \n\t  "), 0)

    def test_word_count_polish(self):
        self.assertEqual(_word_count("Zażółć gęślą jaźń."), 3)

    def test_karta_bez_pliku_po_restore(self):
        class Tab:
            def __init__(self, path):
                self.path = path

        missing = Tab("C:/nie-ma-takiego-rozdzialu-lore.txt")
        kept = Tab("")
        self.assertEqual(
            karty_bez_pliku({"gone": missing, "new": kept}),
            ["gone"],
        )


if __name__ == "__main__":
    unittest.main()