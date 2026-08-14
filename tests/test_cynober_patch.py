"""Uczciwość odczytu .kafd / licznika atomów — bez pustych meta przy błędzie."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lore.cynober_patch import (
    LORE_PACK_KEY,
    LORE_PACK_VERSION,
    read_kafd_vfs_meta,
    sync_atom_id_counter,
    world_meta_from_disk,
)


class TestReadKafdMeta(unittest.TestCase):
    def test_brak_pliku_to_pusta_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_kafd_vfs_meta(Path(tmp) / "brak.kafd"), {})

    def test_smieci_w_kafd_rzucaja(self):
        with tempfile.TemporaryDirectory() as tmp:
            kafd = Path(tmp) / "zly.kafd"
            kafd.write_bytes(b"to nie jest kafd")
            with self.assertRaises(RuntimeError) as ctx:
                read_kafd_vfs_meta(kafd)
            self.assertIn("uszkodzony", str(ctx.exception).lower())

    def test_sidecar_gdy_kafd_nieczytelne(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "Swiat.kafd").write_bytes(b"smiec")
            (base / "Swiat.meta.json").write_text(
                '{"version": 1, "name": "Swiat", "created_at": 1}',
                encoding="utf-8",
            )
            meta = world_meta_from_disk(base, "Swiat")
            self.assertEqual(meta.get("name"), "Swiat")

    def test_brak_sidecar_i_zly_kafd_rzuca(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "Swiat.kafd").write_bytes(b"smiec")
            with self.assertRaises(RuntimeError):
                world_meta_from_disk(base, "Swiat")


class TestSyncAtomId(unittest.TestCase):
    def test_fallback_z_atoms(self):
        store = SimpleNamespace(
            _n=0,
            atoms=lambda: [SimpleNamespace(id="a7"), SimpleNamespace(id="a2")],
        )
        sync_atom_id_counter(store)
        self.assertEqual(store._n, 8)

    def test_api_padnie_bez_fallbacku_rzuca(self):
        class _Store:
            def sync_id_counter(self):
                raise RuntimeError("native down")

        with self.assertRaises(RuntimeError) as ctx:
            sync_atom_id_counter(_Store())
        self.assertIn("licznika", str(ctx.exception))


class TestLorePackConst(unittest.TestCase):
    def test_pack_key(self):
        self.assertEqual(LORE_PACK_KEY, "lore_pack")
        self.assertEqual(LORE_PACK_VERSION, 1)


if __name__ == "__main__":
    unittest.main()
