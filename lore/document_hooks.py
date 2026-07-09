"""Wspólne hooki otwarcia/zapisu pliku — edytor standalone."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from lore.panel import LorePanel
    from lore.store import LoreStore


def on_file_opened(lore: "LoreStore", path: str, panel: Optional["LorePanel"] = None) -> None:
    if not path:
        return
    try:
        lore.otworz_dokument(path)
        if panel is not None:
            panel.odswiez()
    except Exception:
        pass


def on_file_saved(lore: "LoreStore", path: str, panel: Optional["LorePanel"] = None) -> None:
    try:
        if path:
            lore.otworz_dokument(path)
        lore.zapisz()
        if panel is not None:
            panel.odswiez()
    except Exception:
        pass