"""Typy lore widoczne dla pisarza — bez warstwy bazy danych."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List

# Etykiety w UI (pisarz wybiera z listy, nie wpisuje rel:*)
REL_WPŁYWA = "wpływa na"
REL_KOLIGUJE = "koliguje z"
REL_NAWIĄZUJE = "nawiązuje do"
REL_KONFLIKTUJE = "konfliktuje z"
REL_ZAWIERA = "zawiera"
REL_INSPIRUJE = "inspiruje"
REL_WYSTĘPUJE = "występuje w"

RELACJE_LORE: List[str] = [
    REL_WPŁYWA,
    REL_KOLIGUJE,
    REL_NAWIĄZUJE,
    REL_KONFLIKTUJE,
    REL_ZAWIERA,
    REL_INSPIRUJE,
    REL_WYSTĘPUJE,
]

# Mapowanie etykiety UI → klucz grafu Cynober (POŁĄCZ JAKO)
REL_TO_GRAPH: Dict[str, str] = {
    REL_WPŁYWA: "wplywa_na",
    REL_KOLIGUJE: "koliguje_z",
    REL_NAWIĄZUJE: "nawiazuje_do",
    REL_KONFLIKTUJE: "konfliktuje_z",
    REL_ZAWIERA: "zawiera",
    REL_INSPIRUJE: "inspiruje",
    REL_WYSTĘPUJE: "wystepuje_w",
}


class TypLore(str, Enum):
    POSTAĆ = "Postać"
    MIEJSCE = "Miejsce"
    SCENA = "Scena"
    POMYSŁ = "Pomysł"
    WPŁYW = "Wpływ"
    DOKUMENT = "Dokument"
    INNE = "Inne"


TYPY_LORE: List[str] = [t.value for t in TypLore]

# Pola wyświetlane w panelu (cechy bąbla)
POLE_NOTATKA = "Notatka"
POLE_OPIS = "Opis"
POLE_TEKST = "Tekst"
POLE_ŹRÓDŁO = "Źródło"
POLE_PLIK = "Plik"
POLE_STANY = "Stany"
POLE_DOTYK = "OstatniDotyk"

# Pola, które mogą różnić się między rozdziałami (mutacja na osi czasu)
POLA_TEMPORALNE: tuple[str, ...] = (POLE_NOTATKA, POLE_OPIS)