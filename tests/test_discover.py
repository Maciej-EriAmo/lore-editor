"""Testy auto-wykrywania projektu (.lore-project, cwd)."""

import os
import tempfile
import unittest
from pathlib import Path

from lore.paths import LORE_PROJECT_FILE, ProjectPaths


class TestDiscover(unittest.TestCase):
    def test_cwd_as_default_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "MojaPowiesc"
            work.mkdir()
            p = ProjectPaths.discover(cwd=work)
            self.assertEqual(p.root, work.resolve())
            self.assertEqual(p.name, "MojaPowiesc")

    def test_lore_project_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "novel"
            root.mkdir()
            (root / LORE_PROJECT_FILE).write_text("name=EpickaSaga\n", encoding="utf-8")
            sub = root / "rozdzialy"
            sub.mkdir()
            p = ProjectPaths.discover(cwd=sub)
            self.assertEqual(p.root, root.resolve())
            self.assertEqual(p.name, "EpickaSaga")

    def test_cli_project_overrides_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / LORE_PROJECT_FILE).write_text("name=ZPliku\n", encoding="utf-8")
            p = ProjectPaths.discover("ZCLI", cwd=root)
            self.assertEqual(p.name, "ZCLI")

    def test_explicit_project_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            explicit = Path(tmp) / "custom"
            explicit.mkdir()
            p = ProjectPaths.discover("Foo", project_dir=explicit)
            self.assertEqual(p.root, explicit.resolve())
            self.assertEqual(p.name, "Foo")

    def test_open_local_creates_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "Nowela"
            work.mkdir()
            from lore.store import LoreStore

            lore = LoreStore.open_local(project_dir=work)
            try:
                self.assertTrue((work / LORE_PROJECT_FILE).is_file())
            finally:
                lore.close()

    def test_write_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = ProjectPaths.resolve("Test", tmp)
            path = p.write_marker()
            self.assertTrue(path.is_file())
            p2 = ProjectPaths.discover(cwd=Path(tmp))
            self.assertEqual(p2.name, "Test")

    def test_env_lore_project_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["LORE_PROJECT_DIR"] = tmp
            try:
                p = ProjectPaths.discover("EnvProj")
                self.assertEqual(p.root, Path(tmp).resolve())
                self.assertEqual(p.name, "EnvProj")
            finally:
                os.environ.pop("LORE_PROJECT_DIR", None)


if __name__ == "__main__":
    unittest.main()