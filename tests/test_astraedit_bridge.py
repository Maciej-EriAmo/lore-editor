"""Test mostu AstraEdit — bez uruchamiania mainloop."""

import os
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()