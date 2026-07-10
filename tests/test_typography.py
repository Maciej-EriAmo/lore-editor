"""Testy presetów typografii (bez GUI)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lore.typography import (
    PRESETS,
    TypographySettings,
    get_preset,
    list_presets_by_category,
    load_typography_settings,
    resolve_font_family,
    save_typography_settings,
    settings_summary,
    spacing2_pixels,
)


class TestTypography(unittest.TestCase):
    def test_all_presets_have_defaults(self):
        for p in PRESETS:
            self.assertIn(p.size, (11, 12))
            self.assertIn(p.line_spacing, (1.0, 1.5))

    def test_resolve_font_fallback(self):
        preset = get_preset("drafting_courier")
        self.assertEqual(
            resolve_font_family(preset, families=["Arial", "Courier New"]),
            "Courier New",
        )
        self.assertEqual(
            resolve_font_family(preset, families=["Arial", "Segoe UI"]),
            "TkFixedFont",
        )

    def test_spacing2_zero_for_print(self):
        self.assertEqual(spacing2_pixels(12, 1.0), 0)
        self.assertGreater(spacing2_pixels(12, 1.5), 0)

    def test_categories_cover_all_presets(self):
        listed = [p for _c, _l, items in list_presets_by_category() for p in items]
        self.assertEqual(len(listed), len(PRESETS))

    def test_save_and_load_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "typography.json"
            with mock.patch("lore.typography.SETTINGS_FILE", path):
                save_typography_settings(
                    TypographySettings(preset_id="print_garamond", size=12, line_spacing=1.0)
                )
                loaded = load_typography_settings()
            self.assertEqual(loaded.preset_id, "print_garamond")
            self.assertEqual(loaded.size, 12)
            self.assertEqual(loaded.line_spacing, 1.0)

    def test_settings_summary(self):
        s = TypographySettings(preset_id="drafting_sans")
        text = settings_summary(s, family="Calibri")
        self.assertIn("Calibri", text)
        self.assertIn("11", text)


if __name__ == "__main__":
    unittest.main()