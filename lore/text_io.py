"""Odczyt/zapis rozdziałów — UTF-8, Windows-1250, Latin-1."""

from __future__ import annotations

from pathlib import Path

_ENCODINGS = ("utf-8-sig", "utf-8", "cp1250", "latin-1", "iso-8859-2")


def is_binary_file(path: str | Path, sample: int = 8192) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(sample)
        return b"\0" in chunk
    except OSError:
        return True


def read_text_smart(path: str | Path) -> tuple[str, str]:
    """Zwraca (treść, nazwa_kodowania)."""
    path = Path(path)
    if is_binary_file(path):
        raise ValueError(f"Plik binarny — nie można otworzyć jako tekst:\n{path}")

    for enc in _ENCODINGS:
        try:
            return path.read_text(encoding=enc), enc
        except (UnicodeDecodeError, LookupError):
            continue

    return path.read_text(encoding="utf-8", errors="replace"), "utf-8 (zastępstwa)"


def write_text(path: str | Path, content: str, encoding: str = "utf-8") -> None:
    enc = encoding.split()[0] if encoding else "utf-8"
    if enc not in _ENCODINGS and enc != "utf-8":
        enc = "utf-8"
    Path(path).write_text(content, encoding=enc, errors="replace")