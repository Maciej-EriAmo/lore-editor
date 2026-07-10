"""Termodynamika wpisów lore — gorący / zimny / grobowiec."""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from lore.temporal import ostatni_rozdzial_wystapienia

SEK_DZIEŃ = 86_400


class Temperatura(str, Enum):
    GORĄCY = "gorący"
    CIEPŁY = "ciepły"
    ZIMNY = "zimny"
    GROBOWIEC = "grobowiec"


KOLEJNOŚĆ_TEMP: Dict[Temperatura, int] = {
    Temperatura.GORĄCY: 0,
    Temperatura.CIEPŁY: 1,
    Temperatura.ZIMNY: 2,
    Temperatura.GROBOWIEC: 3,
}


def _parse_dotyk(raw: Any) -> Optional[float]:
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def oblicz_temperature(
    *,
    ostatni_dotyk: Any,
    ostatni_rozdzial: Optional[int],
    max_indeks_rozdzialu: int,
    biezacy_indeks: Optional[int] = None,
    teraz: Optional[float] = None,
) -> Temperatura:
    now = teraz if teraz is not None else time.time()
    dotyk = _parse_dotyk(ostatni_dotyk)
    dni = (now - dotyk) / SEK_DZIEŃ if dotyk else 9999.0

    if biezacy_indeks is not None and ostatni_rozdzial == biezacy_indeks:
        return Temperatura.GORĄCY
    if dni <= 7:
        return Temperatura.GORĄCY
    if ostatni_rozdzial is not None and max_indeks_rozdzialu > 0:
        odleglosc = max_indeks_rozdzialu - ostatni_rozdzial
        if odleglosc <= 2:
            return Temperatura.GORĄCY
        if odleglosc <= 5:
            return Temperatura.CIEPŁY
    if dni <= 30:
        return Temperatura.CIEPŁY
    if dni <= 180:
        return Temperatura.ZIMNY
    return Temperatura.GROBOWIEC


def sortuj_po_temperaturze(
    wpisy: List[Dict[str, Any]],
    *,
    ukryj_grobowiec: bool = True,
) -> List[Dict[str, Any]]:
    filtered = [
        w for w in wpisy
        if not ukryj_grobowiec or w.get("temperatura") != Temperatura.GROBOWIEC.value
    ]
    return sorted(
        filtered,
        key=lambda w: (
            KOLEJNOŚĆ_TEMP.get(Temperatura(w.get("temperatura", Temperatura.ZIMNY.value)), 9),
            -(w.get("ostatni_rozdzial") or 0),
            str(w.get("nazwa", "")).lower(),
        ),
    )


def metadane_zycia(
    nazwa: str,
    data: Dict[str, Any],
    kolejnosc: List[Tuple[int, str, str]],
    *,
    biezacy_doc: Optional[str] = None,
    teraz: Optional[float] = None,
) -> Dict[str, Any]:
    relacje = list(data.get("_relations") or [])
    ostatni = ostatni_rozdzial_wystapienia(nazwa, relacje, kolejnosc)
    max_idx = kolejnosc[-1][0] if kolejnosc else 0
    biezacy_idx = None
    if biezacy_doc:
        for idx, doc_id, _ in kolejnosc:
            if doc_id == biezacy_doc:
                biezacy_idx = idx
                break
    temp = oblicz_temperature(
        ostatni_dotyk=data.get("OstatniDotyk"),
        ostatni_rozdzial=ostatni,
        max_indeks_rozdzialu=max_idx,
        biezacy_indeks=biezacy_idx,
        teraz=teraz,
    )
    return {
        "temperatura": temp.value,
        "ostatni_rozdzial": ostatni,
        "ostatni_dotyk": data.get("OstatniDotyk"),
    }