"""Test mostu AstraEdit — bez uruchamiania mainloop."""

import os
import tempfile
import unittest
from pathlib import Path

from lore.astraedit_bridge import _editor_shell, attach_lore_to_astraedit
from lore.astraedit_loader import load_astraedit_gui
from lore.store import LoreStore


class TestAstraeditBridge(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["LORE_PROJECT_DIR"] = self._tmp.name

    def tearDown(self):
        os.environ.pop("LORE_PROJECT_DIR", None)
        self._tmp.cleanup()

    def test_attach_vendor_astraedit(self):
        try:
            AstraEditGUI = load_astraedit_gui()
        except ImportError as e:
            self.skipTest(str(e))

        lore = LoreStore.open_local(project_dir=self._tmp.name)
        gui = AstraEditGUI()
        try:
            self.assertIsNotNone(_editor_shell(gui))
            attach_lore_to_astraedit(gui, lore)
            gui.root.update_idletasks()
        finally:
            gui.root.destroy()
            lore.close()

    def test_open_file_after_attach(self):
        try:
            AstraEditGUI = load_astraedit_gui()
        except ImportError as e:
            self.skipTest(str(e))

        chapter = Path(self._tmp.name) / "rozdzial.txt"
        chapter.write_text("Tekst rozdziału.", encoding="utf-8")

        lore = LoreStore.open_local(project_dir=self._tmp.name)
        gui = AstraEditGUI()
        try:
            attach_lore_to_astraedit(gui, lore)
            gui.open_file(str(chapter))
            gui.root.update_idletasks()
            tab = gui.get_current_tab()
            self.assertIsNotNone(tab)
            content = tab.text_area.get("1.0", "end").strip()
            self.assertIn("Tekst rozdziału", content)
        finally:
            gui.root.destroy()
            lore.close()


if __name__ == "__main__":
    unittest.main()