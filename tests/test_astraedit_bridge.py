"""Most AstraEdit — kiedy flushować lore po zapisie."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from lore.astraedit_bridge import should_flush_lore_after_save


class TestShouldFlushLore(unittest.TestCase):
    def test_brak_karty(self):
        self.assertFalse(should_flush_lore_after_save(None))

    def test_zapis_anulowany_lub_nieudany(self):
        self.assertFalse(should_flush_lore_after_save(SimpleNamespace(is_modified=True)))

    def test_zapis_ok(self):
        self.assertTrue(should_flush_lore_after_save(SimpleNamespace(is_modified=False)))


if __name__ == "__main__":
    unittest.main()
