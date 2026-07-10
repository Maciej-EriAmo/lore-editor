"""Wspólne hooki otwarcia/zapisu pliku — edytor standalone."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from lore.panel import LorePanel
    from lore.store import LoreStore


def on_file_opened(lore: "LoreStore", path: str, panel: Optional["LorePanel"] = None) -> None:
    if not path:
        return
    lore.otworz_dokument(path)
    if panel is not None:
        panel.odswiez()


def on_file_saved(
    lore: "LoreStore",
    path: str,
    panel: Optional["LorePanel"] = None,
    *,
    content: Optional[str] = None,
    encoding: str = "utf-8",
) -> None:
    """Transakcyjny zapis: tekst (atomowo) + flush lore w jednym kroku."""
    from lore.transaction import zapisz_rozdzial_i_lore

    if content is not None and path:
        zapisz_rozdzial_i_lore(lore, path, content, encoding, panel)
        return
    if path:
        lore.otworz_dokument(path)
    lore.zapisz()
    if panel is not None:
        panel.odswiez()