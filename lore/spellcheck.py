"""
Sprawdzanie pisowni (PL) + słownik projektu i nazw lore.

Kolejność źródeł (offline):
1. Nazwy z grafu lore + słownik projektu (.lore-spelling.json) + sesja „ignoruj”
2. Słownik ortograficzny SJP.PL (hunspell pl_PL) przez spylls — gdy dostępny
3. Zapas: wbudowana lista częstych słów PL (pl_common.txt.gz)

SJP.PL: Apache 2.0 (oraz GPL/LGPL/MPL/CC BY — wybór). Atrybucja: lore/data/sjp/NOTICE.txt
"""

from __future__ import annotations

import gzip
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional, Sequence

# Słowa: litery PL + apostrof/myślnik wewnętrzny (np. d'Artagnan, Sienkiewicz-Górski)
_WORD_RE = re.compile(
    r"[A-Za-zÀ-ÖØ-öø-ÿĄĆĘŁŃÓŚŹŻąćęłńóśźż]+(?:['\u2019-][A-Za-zÀ-ÖØ-öø-ÿĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)*"
)

SPELLING_FILE = ".lore-spelling.json"
_DATA_DIR = Path(__file__).resolve().parent / "data"
_DATA_GZ = _DATA_DIR / "pl_common.txt.gz"
_SJP_BASE = _DATA_DIR / "sjp" / "pl_PL"  # bez rozszerzenia (.aff / .dic)

# Minimalny zestaw zawsze znany (gdy brak pliku data/)
_BOOTSTRAP: frozenset[str] = frozenset(
    """
    a i o u w z że się nie to na do od po za co jak tak jest są był była było
    bym byś byśmy byście przez przy bez dla lub albo oraz więc bo gdy jeśli
    może już jeszcze tylko też teże mam masz ma mamy macie mają będzie będą
    ten ta to ci cię mu jej ich nas was mnie mój moja moje twój twoja twoje
    swój swoja swoje jego jej ich ten ta te tych tym tymi tej temu
    który która które którzy której którego którym których
    pan pani państwo panowie panie panu pana panią
    raz dwa trzy cztery pięć sześć siedem osiem dziewięć dziesięć
    dzień nocy roku roku lat wieku miejsca domu miasta drogi czasu
    bardzo bardzo dobrze źle bardziej mniej więcej
    """.split()
)


@dataclass(frozen=True)
class WordSpan:
    """Wystąpienie słowa w tekście (indeksy znaków, 0-based)."""

    start: int
    end: int
    word: str

    @property
    def lower(self) -> str:
        return self.word.casefold()


def tokenize(text: str) -> Iterator[WordSpan]:
    """Zwraca wszystkie „słowa” w tekście (kolejność wystąpień)."""
    for m in _WORD_RE.finditer(text):
        yield WordSpan(m.start(), m.end(), m.group(0))


@lru_cache(maxsize=1)
def load_common_polish() -> frozenset[str]:
    """Wczytaj zapasową listę częstych słów PL (gzip)."""
    words: set[str] = set(_BOOTSTRAP)
    if not _DATA_GZ.is_file():
        return frozenset(words)
    try:
        with gzip.open(_DATA_GZ, "rt", encoding="utf-8") as f:
            for line in f:
                w = line.strip().casefold()
                if w:
                    words.add(w)
    except OSError:
        pass
    return frozenset(words)


@lru_cache(maxsize=1)
def load_sjp_dictionary() -> Any | None:
    """
    Załaduj słownik SJP.PL (hunspell) przez spylls.
    Zwraca Dictionary albo None, gdy brak plików / pakietu.
    """
    aff = Path(str(_SJP_BASE) + ".aff")
    dic = Path(str(_SJP_BASE) + ".dic")
    if not aff.is_file() or not dic.is_file():
        return None
    try:
        from spylls.hunspell import Dictionary  # type: ignore
    except ImportError:
        return None
    try:
        return Dictionary.from_files(str(_SJP_BASE))
    except Exception:
        return None


def sjp_available() -> bool:
    """Czy SJP + spylls są gotowe do użycia."""
    return load_sjp_dictionary() is not None


def backend_label() -> str:
    """Krótki opis aktywnego silnika (status / UI)."""
    if sjp_available():
        return "SJP.PL (hunspell) + lore"
    return "lista częstych PL + lore"


def _edits1(word: str) -> set[str]:
    letters = "aąbcćdeęfghijklłmnńoóprsśtuwyzźż"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = {L + R[1:] for L, R in splits if R}
    transposes = {L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1}
    replaces = {L + c + R[1:] for L, R in splits if R for c in letters}
    inserts = {L + c + R for L, R in splits for c in letters}
    return deletes | transposes | replaces | inserts


def suggest_from_known(
    word: str,
    known: set[str] | frozenset[str],
    *,
    limit: int = 8,
) -> list[str]:
    """Proste sugestie odległości edycyjnej (1–2) spośród zbioru known."""
    w = word.casefold()
    if not w or w in known:
        return []
    if len(w) > 24:
        return []

    candidates: list[str] = []
    e1 = _edits1(w)
    for cand in e1:
        if cand in known:
            candidates.append(cand)
    if len(candidates) < limit:
        for e in list(e1):
            if len(e) > 20:
                continue
            for cand in _edits1(e):
                if cand in known and cand not in candidates and cand != w:
                    candidates.append(cand)
                if len(candidates) >= limit * 3:
                    break
            if len(candidates) >= limit * 3:
                break

    has_pl = any(c in "ąćęłńóśźż" for c in w)
    candidates.sort(
        key=lambda c: (
            abs(len(c) - len(w)),
            0 if (any(ch in "ąćęłńóśźż" for ch in c) == has_pl) else 1,
            c,
        )
    )
    out: list[str] = []
    seen: set[str] = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        if word[:1].isupper():
            out.append(c[:1].upper() + c[1:])
        else:
            out.append(c)
        if len(out) >= limit:
            break
    return out


class ProjectSpellingDict:
    """Słownik użytkownika w katalogu projektu (trwały)."""

    def __init__(self, project_root: Path) -> None:
        self.path = Path(project_root) / SPELLING_FILE
        self.words: set[str] = set()
        self.load()

    def load(self) -> None:
        self.words = set()
        if not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for w in data.get("words") or []:
            s = str(w).strip().casefold()
            if s:
                self.words.add(s)

    def save(self) -> None:
        payload = {
            "version": 1,
            "words": sorted(self.words),
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def add(self, word: str) -> None:
        w = word.strip().casefold()
        if not w:
            return
        self.words.add(w)
        self.save()

    def discard(self, word: str) -> None:
        self.words.discard(word.strip().casefold())
        self.save()


class SpellChecker:
    """
    Korektor offline: SJP.PL (gdy dostępny) + lore + słownik projektu + sesja.
    """

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        lore_names: Optional[Sequence[str]] = None,
    ) -> None:
        self._sjp = load_sjp_dictionary()
        self._common = load_common_polish() if self._sjp is None else frozenset(_BOOTSTRAP)
        self._project = ProjectSpellingDict(project_root) if project_root else None
        self._session_ignore: set[str] = set()
        self._lore_tokens: set[str] = set()
        self._lore_full: dict[str, str] = {}  # casefold → oryginalna nazwa
        if lore_names:
            self.set_lore_names(lore_names)

    @property
    def uses_sjp(self) -> bool:
        return self._sjp is not None

    def set_lore_names(self, names: Iterable[str]) -> None:
        self._lore_tokens = set()
        self._lore_full = {}
        for name in names:
            n = (name or "").strip()
            if not n:
                continue
            self._lore_full[n.casefold()] = n
            for part in _WORD_RE.findall(n):
                self._lore_tokens.add(part.casefold())

    def reload_project_dict(self) -> None:
        if self._project:
            self._project.load()

    def known_pool(self) -> set[str]:
        """Zbiór do sugestii zapasowych (bez pełnego SJP — zbyt duży)."""
        pool: set[str] = set(self._common)
        pool |= self._lore_tokens
        pool |= set(self._lore_full.keys())
        if self._project:
            pool |= self._project.words
        pool |= self._session_ignore
        return pool

    def _sjp_lookup(self, word: str) -> bool:
        if self._sjp is None:
            return False
        try:
            if self._sjp.lookup(word):
                return True
            # warianty wielkości liter (początek zdania)
            if word[:1].isupper() and self._sjp.lookup(word[:1].lower() + word[1:]):
                return True
            if self._sjp.lookup(word.casefold()):
                return True
        except Exception:
            return False
        return False

    def is_known(self, word: str) -> bool:
        w = word.casefold()
        if not w:
            return True
        if w.isdigit():
            return True
        if len(w) == 1:
            return True
        if w in self._session_ignore:
            return True
        if w in self._lore_tokens or w in self._lore_full:
            return True
        if self._project and w in self._project.words:
            return True
        # Akronimy typu ABC / FBI
        if word.isupper() and 2 <= len(word) <= 6:
            return True
        if self._sjp is not None:
            return self._sjp_lookup(word)
        return w in self._common

    def unknown_spans(self, text: str) -> list[WordSpan]:
        return [span for span in tokenize(text) if not self.is_known(span.word)]

    def suggestions(self, word: str, *, limit: int = 8) -> list[str]:
        lore_hits = [
            orig
            for key, orig in self._lore_full.items()
            if key.startswith(word.casefold()[: max(2, len(word) // 2)])
            or word.casefold() in key
        ][:3]

        sjp_hits: list[str] = []
        if self._sjp is not None:
            try:
                sjp_hits = list(self._sjp.suggest(word))[:limit]
            except Exception:
                sjp_hits = []

        base = suggest_from_known(word, self.known_pool(), limit=limit)

        out: list[str] = []
        seen: set[str] = set()
        for item in lore_hits + sjp_hits + base:
            k = item.casefold()
            if k in seen or k == word.casefold():
                continue
            seen.add(k)
            out.append(item)
            if len(out) >= limit:
                break
        return out

    def add_to_project(self, word: str) -> None:
        if self._project is None:
            self._session_ignore.add(word.casefold())
            return
        self._project.add(word)

    def ignore_session(self, word: str) -> None:
        self._session_ignore.add(word.casefold())

    def match_lore(self, query: str) -> list[str]:
        """Nazwy lore pasujące do frazy (dla słownika nazw)."""
        q = query.strip().casefold()
        if not q:
            return sorted(self._lore_full.values(), key=str.casefold)
        hits = [
            name
            for key, name in self._lore_full.items()
            if q in key or key in q
        ]
        return sorted(hits, key=lambda n: (0 if n.casefold().startswith(q) else 1, n.casefold()))
