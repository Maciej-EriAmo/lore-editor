"""Testy odczytu plików z różnymi kodowaniami."""

import tempfile
import unittest
from pathlib import Path

from lore.text_io import read_text_smart, write_text


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


if __name__ == "__main__":
    unittest.main()