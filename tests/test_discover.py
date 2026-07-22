"""Testy auto-wykrywania projektu (.lore-project, domyślny katalog pracy)."""

import os
import tempfile
import unittest
from pathlib import Path

from lore.paths import (
    ENV_DEFAULT_WORK_DIR,
    ENV_PROJECT_DIR,
    LORE_PROJECT_FILE,
    ProjectPaths,
    default_work_dir,
    is_app_source_root,
    load_last_file,
    load_last_work_dir,
    save_last_file,
    save_last_work_dir,
)


class TestDiscover(unittest.TestCase):
    def test_default_work_dir_when_no_marker(self):
        """Bez .lore-project i bez last_work_dir → ../dokumenty/lore."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "losowy-cwd"
            work.mkdir()
            with mock_last_work_file(Path(tmp) / "brak.json"):
                expected = default_work_dir(cwd=work)
                p = ProjectPaths.discover(cwd=work)
                self.assertEqual(p.root, expected)
                self.assertEqual(p.name, expected.name)

    def test_default_work_dir_path_shape(self):
        d = default_work_dir()
        self.assertTrue(str(d).replace("\\", "/").endswith("dokumenty/lore") or d.name == "lore")
        self.assertEqual(d.name, "lore")
        self.assertEqual(d.parent.name, "dokumenty")

    def test_lore_default_work_dir_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "moja-praca"
            os.environ[ENV_DEFAULT_WORK_DIR] = str(custom)
            try:
                # bez markera i bez LORE_PROJECT_DIR / last GUI
                os.environ.pop(ENV_PROJECT_DIR, None)
                work = Path(tmp) / "cwd"
                work.mkdir()
                with mock_last_work_file(Path(tmp) / "brak.json"):
                    p = ProjectPaths.discover(cwd=work)
                    self.assertEqual(p.root, custom.resolve())
            finally:
                os.environ.pop(ENV_DEFAULT_WORK_DIR, None)

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
                hist = work / ".lore-history"
                self.assertTrue(hist.is_dir())
                self.assertTrue((hist / "README.txt").is_file())
                self.assertTrue((hist / "manifest.json").is_file())
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
            os.environ[ENV_PROJECT_DIR] = tmp
            try:
                p = ProjectPaths.discover("EnvProj")
                self.assertEqual(p.root, Path(tmp).resolve())
                self.assertEqual(p.name, "EnvProj")
            finally:
                os.environ.pop(ENV_PROJECT_DIR, None)

    def test_explicit_beats_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            chosen = Path(tmp) / "wskazany"
            chosen.mkdir()
            p = ProjectPaths.discover(project_dir=chosen)
            self.assertEqual(p.root, chosen.resolve())
            self.assertNotEqual(p.root, default_work_dir())

    def test_last_work_dir_from_gui(self):
        with tempfile.TemporaryDirectory() as tmp:
            gui_dir = Path(tmp) / "z-gui"
            gui_dir.mkdir()
            # izoluj plik last_work_dir
            with mock_last_work_file(Path(tmp) / "last.json"):
                saved = save_last_work_dir(gui_dir)
                self.assertEqual(saved, gui_dir.resolve())
                self.assertEqual(load_last_work_dir(), gui_dir.resolve())
                work = Path(tmp) / "inny-cwd"
                work.mkdir()
                p = ProjectPaths.discover(cwd=work)
                self.assertEqual(p.root, gui_dir.resolve())

    def test_last_file_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "powiesc"
            root.mkdir()
            chapter = root / "rozdzial_01.txt"
            chapter.write_text("Ala ma kota\n", encoding="utf-8")
            with mock_last_work_file(Path(tmp) / "last.json"):
                save_last_work_dir(root)
                self.assertIsNone(load_last_file())
                save_last_file(chapter, project_dir=root)
                self.assertEqual(load_last_work_dir(), root.resolve())
                self.assertEqual(load_last_file(), chapter.resolve())
                # nieistniejący plik → None
                import json

                gone = root / "brak.txt"
                data_path = Path(tmp) / "last.json"
                data_path.write_text(
                    json.dumps(
                        {"path": str(root), "last_file": str(gone), "version": 2},
                        ensure_ascii=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                self.assertIsNone(load_last_file())

    def test_skip_app_source_marker(self):
        """Marker w katalogu kodu lore-editor nie blokuje dokumenty/lore."""
        # is_app_source_root na prawdziwym repo
        repo = Path(__file__).resolve().parents[1]
        if is_app_source_root(repo):
            self.assertTrue(is_app_source_root(repo))
        with tempfile.TemporaryDirectory() as tmp:
            # symulacja: cwd z markerem „aplikacji” nie da się łatwo — test helpera
            fake_app = Path(tmp) / "lore-editor"
            fake_app.mkdir()
            (fake_app / "run_lore_editor.py").write_text("#\n", encoding="utf-8")
            (fake_app / "lore").mkdir()
            (fake_app / "lore" / "__init__.py").write_text("", encoding="utf-8")
            (fake_app / LORE_PROJECT_FILE).write_text("name=lore-editor\n", encoding="utf-8")
            self.assertTrue(is_app_source_root(fake_app))
            with mock_last_work_file(Path(tmp) / "last.json"):
                # bez last → default
                p = ProjectPaths.discover(cwd=fake_app)
                self.assertNotEqual(p.root, fake_app.resolve())
                self.assertEqual(p.root, default_work_dir(cwd=fake_app))

    def test_standalone_dist_is_app_root(self):
        """Folder Nuitka (exe + python*.dll) nie jest folderem powieści."""
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "run_lore_editor.dist"
            dist.mkdir()
            (dist / "run_lore_editor.exe").write_bytes(b"MZ")
            (dist / "python314.dll").write_bytes(b"")
            (dist / LORE_PROJECT_FILE).write_text("name=oops\n", encoding="utf-8")
            self.assertTrue(is_app_source_root(dist))
            with mock_last_work_file(Path(tmp) / "last.json"):
                p = ProjectPaths.discover(cwd=dist)
                self.assertNotEqual(p.root, dist.resolve())


class _LastWorkCtx:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._old = None

    def __enter__(self):
        import lore.paths as paths_mod

        self._old = paths_mod.LAST_WORK_DIR_FILE
        paths_mod.LAST_WORK_DIR_FILE = self.path
        return self

    def __exit__(self, *args):
        import lore.paths as paths_mod

        paths_mod.LAST_WORK_DIR_FILE = self._old


def mock_last_work_file(path: Path) -> _LastWorkCtx:
    return _LastWorkCtx(path)


if __name__ == "__main__":
    unittest.main()
