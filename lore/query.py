"""Zapytania semantyczne po grafie lore (z osią rozdziałów)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

from lore.lifecycle import Temperatura
from lore.temporal import ostatni_rozdzial_wystapienia
from lore.types import TypLore

_TYP_ALIASES = {
    "postać": TypLore.POSTAĆ.value,
    "postacie": TypLore.POSTAĆ.value,
    "postac": TypLore.POSTAĆ.value,
    "miejsce": TypLore.MIEJSCE.value,
    "miejsca": TypLore.MIEJSCE.value,
    "scena": TypLore.SCENA.value,
    "sceny": TypLore.SCENA.value,
    "pomysł": TypLore.POMYSŁ.value,
    "pomysly": TypLore.POMYSŁ.value,
    "wpływ": TypLore.WPŁYW.value,
    "wplyw": TypLore.WPŁYW.value,
    "wpływy": TypLore.WPŁYW.value,
    "dokument": TypLore.DOKUMENT.value,
}


@dataclass
class ZapytanieSemantyczne:
    typ: Optional[str] = None
    przy: Optional[str] = None
    nie_od_rozdzialu: Optional[int] = None
    fraza: Optional[str] = None
    min_temperatura: Optional[Temperatura] = None


_RE_TYP = re.compile(r"\btyp[:\s]+([^\s]+)", re.IGNORECASE)
_RE_PRZY = re.compile(r"\b(?:przy|powiązane z|powiazane z|z)\s+([^\s]+(?:\s+[^\s]+)?)", re.IGNORECASE)
_RE_NIE_OD = re.compile(r"\bnie\s+od\s+(\d+)\b", re.IGNORECASE)
_RE_TEMP = re.compile(
    r"\b(gorące|gorace|ciepłe|cieple|zimne|grobowiec)\b",
    re.IGNORECASE,
)
_RE_CUDZYSLOW = re.compile(r'"([^"]+)"')


def _norm_entity(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name.strip(), flags=re.UNICODE)


def parsuj_zapytanie(text: str) -> ZapytanieSemantyczne:
    raw = text.strip()
    if not raw:
        return ZapytanieSemantyczne()

    q = ZapytanieSemantyczne()
    lowered = raw.lower()

    m = _RE_NIE_OD.search(raw)
    przy_source = raw
    if m:
        q.nie_od_rozdzialu = int(m.group(1))
        przy_source = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    m = _RE_TYP.search(raw)
    if m:
        alias = m.group(1).lower()
        q.typ = _TYP_ALIASES.get(alias, m.group(1))

    for keyword, typ_val in _TYP_ALIASES.items():
        if keyword in lowered and q.typ is None:
            if lowered.startswith(keyword) or f" {keyword}" in lowered:
                q.typ = typ_val
                break

    m = _RE_TEMP.search(raw)
    if m:
        word = m.group(1).lower()
        mapping = {
            "gorące": Temperatura.GORĄCY,
            "gorace": Temperatura.GORĄCY,
            "ciepłe": Temperatura.CIEPŁY,
            "cieple": Temperatura.CIEPŁY,
            "zimne": Temperatura.ZIMNY,
            "grobowiec": Temperatura.GROBOWIEC,
        }
        q.min_temperatura = mapping.get(word)

    m = _RE_CUDZYSLOW.search(raw)
    if m:
        q.fraza = m.group(1)

    m = _RE_PRZY.search(przy_source)
    if m:
        q.przy = _norm_entity(m.group(1).strip())

    if q.typ is None and q.przy is None and q.fraza is None and q.nie_od_rozdzialu is None:
        q.fraza = raw

    return q


def wykonaj_zapytanie(
    zapytanie: ZapytanieSemantyczne,
    *,
    wszystkie: Callable[[], List[str]],
    sasiedzi: Callable[[str], List[str]],
    podglad: Callable[[str], Dict[str, Any]],
    szukaj_tekst: Callable[[str], List[str]],
    kolejnosc: List[tuple],
    sanitize: Callable[[str], str],
) -> List[Dict[str, Any]]:
    kandydaci: Optional[Set[str]] = None

    if zapytanie.fraza and not zapytanie.przy and not zapytanie.typ:
        names = szukaj_tekst(zapytanie.fraza)
        kandydaci = set(names)
    else:
        kandydaci = set(wszystkie())

    if zapytanie.przy:
        anchor = sanitize(zapytanie.przy)
        connected = set(sasiedzi(anchor))
        connected.add(anchor)
        kandydaci &= connected

    if zapytanie.typ:
        typed = {
            n for n in kandydaci
            if podglad(n).get("Typ") == zapytanie.typ
        }
        kandydaci = typed

    if zapytanie.fraza and (zapytanie.przy or zapytanie.typ):
        text_hits = set(szukaj_tekst(zapytanie.fraza))
        kandydaci &= text_hits

    wyniki: List[Dict[str, Any]] = []
    for name in sorted(kandydaci):
        data = podglad(name)
        relacje = list(data.get("_relations") or [])
        ostatni = ostatni_rozdzial_wystapienia(name, relacje, kolejnosc)

        if zapytanie.nie_od_rozdzialu is not None:
            prog = zapytanie.nie_od_rozdzialu
            if ostatni is not None and ostatni >= prog:
                continue
            if ostatni is None and prog <= 1:
                continue

        temp = data.get("_temperatura")
        if zapytanie.min_temperatura and temp:
            from lore.lifecycle import KOLEJNOŚĆ_TEMP

            if KOLEJNOŚĆ_TEMP.get(Temperatura(temp), 9) > KOLEJNOŚĆ_TEMP[zapytanie.min_temperatura]:
                continue

        wyniki.append({
            "nazwa": name,
            "typ": data.get("Typ", "?"),
            "opis": data.get("Opis") or data.get("Notatka") or data.get("Tekst") or "",
            "ostatni_rozdzial": ostatni,
            "temperatura": temp,
        })

    return wyniki