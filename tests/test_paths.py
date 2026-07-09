"""Testy ścieżek projektu."""

import tempfile
import unittest
from pathlib import Path

from lore.paths import ProjectPaths


class TestPaths(unittest.TestCase):
    def test_world_kafd(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = ProjectPaths.resolve("MojaPowiesc", tmp)
            self.assertEqual(p.world_kafd(), Path(tmp) / "MojaPowiesc.kafd")


if __name__ == "__main__":
    unittest.main()