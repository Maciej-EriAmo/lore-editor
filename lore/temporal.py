"""Kontekst czasowy lore — stany encji per rozdział (as_of)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from lore.types import POLE_PLIK, POLA_TEMPORALNE, TypLore


def natural_sort_key(text: str) -> list:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def parse_stany(raw: Any) -> Dict[str, Dict[str, Any]]:
    if raw in (None, ""):
        return {}
    if isinstance(raw, dict):
        return {str(k): dict(v) if isinstance(v, dict) else {} for k, v in raw.items()}
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
        if isinstance(data, dict):
            return {str(k): dict(v) if isinstance(v, dict) else {} for k, v in data.items()}
    return {}


def serialize_stany(stany: Dict[str, Dict[str, Any]]) -> str:
    cleaned = {
        doc: {k: v for k, v in fields.items() if v not in (None, "")}
        for doc, fields in stany.items()
        if fields
    }
    return json.dumps(cleaned, ensure_ascii=False)


def pole_temporalne(pole: str, typ: str) -> bool:
    if pole in POLA_TEMPORALNE:
        return True
    if typ == TypLore.POMYSŁ.value and pole in ("Tekst",):
        return True
    return False


def dokumenty_uporzadkowane(
    dokumenty: List[Tuple[str, Dict[str, Any]]],
) -> List[Tuple[int, str, str]]:
    """[(indeks 1-based, id_bąbla, plik_względny), …] posortowane po ścieżce pliku."""
    rows: List[Tuple[str, str, list]] = []
    for doc_id, data in dokumenty:
        plik = str(data.get(POLE_PLIK) or data.get("Opis") or doc_id)
        rows.append((doc_id, plik, natural_sort_key(plik)))
    rows.sort(key=lambda row: row[2])
    return [(idx + 1, doc_id, plik) for idx, (doc_id, plik, _) in enumerate(rows)]


def indeks_dokumentu(doc_id: str, kolejnosc: List[Tuple[int, str, str]]) -> Optional[int]:
    for idx, bubble, _plik in kolejnosc:
        if bubble == doc_id:
            return idx
    return None


def scal_stan(
    wlasciwosci: Dict[str, Any],
    stany: Dict[str, Dict[str, Any]],
    *,
    as_of: Optional[str],
    kolejnosc: List[Tuple[int, str, str]],
) -> Dict[str, Any]:
    """Nałóż mutacje rozdziałowe do podanego momentu narracji."""
    out = dict(wlasciwosci)
    if not stany:
        return out

    doc_indices = {doc_id: idx for idx, doc_id, _ in kolejnosc}
    limit = doc_indices.get(as_of or "", 10**9) if as_of else 10**9

    ordered_docs = sorted(
        (doc_indices[doc], doc) for doc in stany if doc in doc_indices
    )
    for doc_idx, doc_id in ordered_docs:
        if doc_idx > limit:
            break
        for pole, wartosc in stany[doc_id].items():
            if wartosc not in (None, ""):
                out[pole] = wartosc
    return out


def ustaw_stan_rozdzialu(
    stany: Dict[str, Dict[str, Any]],
    doc_id: str,
    pole: str,
    wartosc: Any,
) -> Dict[str, Dict[str, Any]]:
    updated = {k: dict(v) for k, v in stany.items()}
    slot = dict(updated.get(doc_id) or {})
    slot[pole] = wartosc
    updated[doc_id] = slot
    return updated


def ostatni_rozdzial_wystapienia(
    encja: str,
    relacje: List[Dict[str, Any]],
    kolejnosc: List[Tuple[int, str, str]],
) -> Optional[int]:
    """Najwyższy indeks rozdziału (1-based), w którym encja ma relację wystepuje_w."""
    doc_indices = {doc_id: idx for idx, doc_id, _ in kolejnosc}
    best: Optional[int] = None
    for rel in relacje:
        if not isinstance(rel, dict):
            continue
        if rel.get("relation") != "wystepuje_w":
            continue
        target = rel.get("target")
        if not target:
            continue
        idx = doc_indices.get(str(target))
        if idx is not None:
            best = idx if best is None else max(best, idx)
    return best