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

    def test_lore_panel_has_full_height(self):
        try:
            AstraEditGUI = load_astraedit_gui()
        except ImportError as e:
            self.skipTest(str(e))

        lore = LoreStore.open_local(project_dir=self._tmp.name)
        gui = AstraEditGUI()
        try:
            attach_lore_to_astraedit(gui, lore)
            gui.root.geometry("1100x800")
            gui.root.update_idletasks()
            gui.root.update()

            body = None
            right_host = None
            for child in gui.root.winfo_children():
                if child.winfo_class() == "Frame" and child.winfo_width() > 500:
                    body = child
                    break
            self.assertIsNotNone(body, "brak ramki body")
            for child in body.winfo_children():
                if child.winfo_width() == 300:
                    right_host = child
                    break
            self.assertIsNotNone(right_host, "brak panelu lore")
            self.assertGreaterEqual(right_host.winfo_height(), 400)
            self.assertGreaterEqual(_editor_shell(gui).winfo_height(), 400)
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
            gui.root.geometry("1100x800")
            gui.root.update_idletasks()
            content = tab.text_area.get("1.0", "end").strip()
            self.assertIn("Tekst rozdziału", content)
            self.assertGreater(len(gui.notebook.tabs()), 0)
        finally:
            gui.root.destroy()
            lore.close()


if __name__ == "__main__":
    unittest.main()