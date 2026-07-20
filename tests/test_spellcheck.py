"""Testy słownika / pisowni (bez UI)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lore.spellcheck import (
    ProjectSpellingDict,
    SpellChecker,
    SPELLING_FILE,
    backend_label,
    load_sjp_dictionary,
    sjp_available,
    suggest_from_known,
    tokenize,
)


class TestTokenize(unittest.TestCase):
    def test_polish_words(self):
        spans = list(tokenize("Zażółć gęślą jaźń — d'Artagnan."))
        words = [s.word for s in spans]
        self.assertIn("Zażółć", words)
        self.assertIn("gęślą", words)
        self.assertIn("jaźń", words)
        self.assertIn("d'Artagnan", words)

    def test_offsets(self):
        text = "Ala ma kota"
        spans = list(tokenize(text))
        self.assertEqual(len(spans), 3)
        self.assertEqual(text[spans[0].start : spans[0].end], "Ala")
        self.assertEqual(text[spans[2].start : spans[2].end], "kota")


class TestSuggestions(unittest.TestCase):
    def test_edit_distance(self):
        known = frozenset({"kot", "kotka", "pies", "dom"})
        sugs = suggest_from_known("kto", known, limit=5)
        self.assertIn("kot", [s.casefold() for s in sugs])


class TestSjpBackend(unittest.TestCase):
    def test_sjp_loads_when_present(self):
        # W repozytorium są pliki lore/data/sjp/pl_PL.* + spylls w zależnościach
        if not sjp_available():
            self.skipTest("SJP/spylls niedostępne w tym środowisku")
        d = load_sjp_dictionary()
        self.assertIsNotNone(d)
        self.assertTrue(d.lookup("nie"))
        self.assertTrue(d.lookup("poszedłem"))
        self.assertFalse(d.lookup("xyzzyqwerty"))
        self.assertIn("SJP", backend_label())

    def test_sjp_inflection_via_checker(self):
        if not sjp_available():
            self.skipTest("SJP/spylls niedostępne w tym środowisku")
        sc = SpellChecker()
        self.assertTrue(sc.uses_sjp)
        self.assertTrue(sc.is_known("nie"))
        self.assertTrue(sc.is_known("koty"))
        self.assertTrue(sc.is_known("poszedłem"))
        self.assertTrue(sc.is_known("zażółć"))
        self.assertFalse(sc.is_known("xyzzyqwerty"))
        sugs = sc.suggestions("kotyk")
        self.assertIsInstance(sugs, list)


class TestSpellChecker(unittest.TestCase):
    def test_common_polish(self):
        sc = SpellChecker()
        self.assertTrue(sc.is_known("nie"))
        self.assertTrue(sc.is_known("się"))
        self.assertTrue(sc.is_known("jest"))

    def test_lore_names(self):
        sc = SpellChecker(lore_names=["Anastazja Wrona", "Karmazyn"])
        self.assertTrue(sc.is_known("Anastazja"))
        self.assertTrue(sc.is_known("Wrona"))
        self.assertTrue(sc.is_known("Karmazyn"))
        self.assertFalse(sc.is_known("Xyzzyqwerty"))

    def test_project_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sc = SpellChecker(project_root=root)
            weird = "błyskotliwośććć"
            self.assertFalse(sc.is_known(weird))
            sc.add_to_project(weird)
            self.assertTrue(sc.is_known(weird))
            path = root / SPELLING_FILE
            self.assertTrue(path.is_file())
            # reload
            sc2 = SpellChecker(project_root=root)
            self.assertTrue(sc2.is_known(weird))

    def test_unknown_spans(self):
        sc = SpellChecker(lore_names=["Marek"])
        text = "Marek poszedł do xyzzyqwerty domu"
        bad = sc.unknown_spans(text)
        words = [s.word for s in bad]
        self.assertIn("xyzzyqwerty", words)
        self.assertNotIn("Marek", words)

    def test_session_ignore(self):
        sc = SpellChecker()
        sc.ignore_session("xyzzyqwerty")
        self.assertTrue(sc.is_known("xyzzyqwerty"))

    def test_acronym(self):
        sc = SpellChecker()
        self.assertTrue(sc.is_known("FBI"))
        self.assertTrue(sc.is_known("NASA"))

    def test_match_lore(self):
        sc = SpellChecker(lore_names=["Anastazja", "Anna", "Boruta"])
        hits = sc.match_lore("an")
        self.assertIn("Anastazja", hits)
        self.assertIn("Anna", hits)
        self.assertNotIn("Boruta", hits)
        self.assertEqual(sc.match_lore("boru"), ["Boruta"])


class TestProjectSpellingDict(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = ProjectSpellingDict(Path(tmp))
            d.add("foo")
            d.add("BAR")
            self.assertIn("foo", d.words)
            self.assertIn("bar", d.words)
            d2 = ProjectSpellingDict(Path(tmp))
            self.assertEqual(d.words, d2.words)


if __name__ == "__main__":
    unittest.main()
