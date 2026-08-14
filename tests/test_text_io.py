"""Testy odczytu plików z różnymi kodowaniami."""

import tempfile
import unittest
from pathlib import Path

from lore.text_io import is_binary_file, read_text_smart, write_text, write_text_atomic


class TestTextIo(unittest.TestCase):
    def test_cp1250_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rozdzial.txt"
            original = "Żółć i ósemka"
            path.write_bytes(original.encode("cp1250"))
            content, enc = read_text_smart(path)
            self.assertEqual(content, original)
            self.assertEqual(enc, "cp1250")
            write_text(path, content + "!", enc)
            self.assertEqual(path.read_bytes(), (original + "!").encode("cp1250"))

    def test_utf8_sig(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "utf8.txt"
            path.write_bytes(b"\xef\xbb\xbf" + "Cześć".encode("utf-8"))
            content, enc = read_text_smart(path)
            self.assertEqual(content, "Cześć")
            self.assertIn("utf-8", enc)

    def test_zapis_strict_nie_podmienia_znakow(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.txt"
            with self.assertRaises(UnicodeEncodeError):
                write_text(path, "ę", encoding="latin-1")
            dest = Path(tmp) / "atom.txt"
            with self.assertRaises(UnicodeEncodeError):
                write_text_atomic(dest, "ę", encoding="latin-1")
            self.assertFalse(dest.is_file())

    def test_brak_pliku_to_oserror_nie_binarny(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nie_ma.txt"
            with self.assertRaises(OSError):
                is_binary_file(missing)
            with self.assertRaises(OSError):
                read_text_smart(missing)


if __name__ == "__main__":
    unittest.main()