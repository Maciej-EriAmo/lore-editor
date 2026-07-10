"""Transakcyjny zapis rozdziału + lore."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from lore.text_io import write_text_atomic

if TYPE_CHECKING:
    from lore.panel import LorePanel
    from lore.store import LoreStore


def zapisz_rozdzial_i_lore(
    lore: "LoreStore",
    path: str,
    content: str,
    encoding: str = "utf-8",
    panel: Optional["LorePanel"] = None,
) -> None:
    """
    Jedna operacja: atomowy zapis tekstu, potem flush grafu lore.
    Przy błędzie lore plik tekstu pozostaje zapisany (tekst ważniejszy w flow),
    ale wyjątek sygnalizuje niespójność do obsługi w UI.
    """
    label = Path(path).name if path else ""
    if path:
        write_text_atomic(path, content, encoding)
        lore.otworz_dokument(path)
    lore.zapisz(historia_label=label)
    if panel is not None:
        panel.odswiez()