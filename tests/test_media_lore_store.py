# -*- coding: utf-8 -*-
"""Roundtrip mediów przez LoreStore (lokalnie) — weryfikacja „Dołącz plik” → .kafd."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from lore.store import LoreStore

_MIN_PNG = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D,
        0xB0, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ]
)


class TestLoreStoreMediaLocal(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "MediaProj"
        self.root.mkdir()
        (self.root / ".lore-project").write_text("name=MediaProj\n", encoding="utf-8")
        # domyślnie lazy ON w cynober — test ma przeżyć zwijanie
        os.environ.setdefault("CYNOBER_LAZY_LOAD", "1")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_attach_file_save_reopen_list_read(self) -> None:
        png = self.root / "hero.png"
        png.write_bytes(_MIN_PNG)

        st = LoreStore.open_local(project_dir=self.root)
        st.dodaj_postac("Bohater")
        info = st.dodaj_media("Bohater", "portret", png)
        self.assertEqual(info.get("binding"), "portret")
        self.assertGreater(int(info.get("size") or 0), 0)
        st.zapisz()
        st._backend.close(flush=False)

        st2 = LoreStore.open_local(project_dir=self.root)
        listed = st2.lista_mediow("Bohater")
        self.assertTrue(listed, "lista_mediow pusta po reopen — media nie w .kafd / bubble")
        roles = {m.get("binding") for m in listed}
        self.assertIn("portret", roles)
        data, mime = st2.odczyt_media("Bohater", "portret")
        self.assertEqual(data[:8], _MIN_PNG[:8])
        self.assertIn("image", (mime or "").lower())

    def test_attach_bytes_and_jpeg_mime_guess(self) -> None:
        st = LoreStore.open_local(project_dir=self.root)
        st.dodaj_postac("Anna")
        info = st.dodaj_media(
            "Anna", "portret", _MIN_PNG, mime="image/png"
        )
        st.zapisz()
        self.assertEqual(info.get("mime"), "image/png")
        listed = st.lista_mediow("Anna")
        self.assertEqual(len(listed), 1)

    def test_stream_force_roundtrip(self) -> None:
        """Większy plik / force_stream — head A_STREAM + segmenty."""
        big = self.root / "big.bin"
        payload = _MIN_PNG + (b"Q" * (512 * 1024))
        big.write_bytes(payload)
        st = LoreStore.open_local(project_dir=self.root)
        st.dodaj_postac("Hero")
        info = st.dodaj_media("Hero", "duzy", big, force_stream=True)
        self.assertTrue(info.get("stream") or info.get("size", 0) > 0)
        st.zapisz()
        st._backend.close(flush=False)

        st2 = LoreStore.open_local(project_dir=self.root)
        listed = st2.lista_mediow("Hero")
        self.assertTrue(any(m.get("binding") == "duzy" for m in listed), listed)
        data, _mime = st2.odczyt_media("Hero", "duzy")
        self.assertEqual(len(data), len(payload))
        self.assertEqual(data[:8], payload[:8])


if __name__ == "__main__":
    unittest.main()
