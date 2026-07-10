"""Testy paginacji i eksportu rękopisu."""

import tempfile
import unittest
from pathlib import Path

from lore.export_docx import export_available, export_manuscript_docx
from lore.manuscript import (
    paginate,
    profile_for_preset,
    wrap_document,
    word_count,
)
from lore.typography import PRESETS


class TestManuscript(unittest.TestCase):
    def test_screenplay_pages_and_minutes(self):
        lines = ["LINIA"] * 110
        text = "\n".join(lines)
        stats = paginate(text, "screenplay")
        self.assertEqual(stats.pages, 2)
        self.assertAlmostEqual(stats.estimated_minutes, 2.0)
        self.assertEqual(len(stats.page_slices), 2)

    def test_submission_word_pages(self):
        words = " ".join(["słowo"] * 500)
        stats = paginate(words, "submission")
        self.assertGreaterEqual(stats.pages, 2)

    def test_profile_for_preset_courier(self):
        self.assertEqual(profile_for_preset("drafting_courier_prime"), "screenplay")
        self.assertEqual(profile_for_preset("print_times"), "print_ready")

    def test_wrap_long_line(self):
        prof = paginate("x", "print_ready").profile
        wrapped = wrap_document("a" * 200, prof)
        self.assertGreater(len(wrapped), 1)

    def test_empty_text_one_page(self):
        stats = paginate("", "print_ready")
        self.assertEqual(stats.pages, 1)

    def test_all_typography_presets_map(self):
        for p in PRESETS:
            pid = profile_for_preset(p.id)
            self.assertIn(pid, ("screenplay", "submission", "print_ready"))


@unittest.skipUnless(export_available(), "python-docx not installed")
class TestDocxExport(unittest.TestCase):
    def test_export_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "test.docx"
            export_manuscript_docx("Rozdział pierwszy.\n\nDrugi akapit.", out, profile_id="submission")
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()