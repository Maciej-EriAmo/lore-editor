"""
LoreStore — API lore dla pisarza. Zero KarminQL w interfejsie.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lore.backend import (
    LocalLoreBackend,
    LoreBackendError,
    RpcLoreBackend,
    _esc,
    _last,
    connect_local,
    connect_rpc,
    default_lore_worlds_dir,
)
from lore.types import (
    POLE_NOTATKA,
    POLE_OPIS,
    POLE_PLIK,
    POLE_TEKST,
    POLE_ŹRÓDŁO,
    REL_TO_GRAPH,
    RELACJE_LORE,
    TYPY_LORE,
    TypLore,
)


class LoreStore:
    """
    Warstwa dla pisarza: postacie, pomysły, wpływy, koligacje.
    Wszystkie operacje na grafie lore są ukryte pod prostymi metodami.
    """

    def __init__(self, backend: Union[LocalLoreBackend, RpcLoreBackend], project: str):
        self._backend = backend
        self._project = self._sanitize_name(project)
        self._opened_doc: Optional[str] = None

    @classmethod
    def open_local(cls, project: str) -> "LoreStore":
        default_lore_worlds_dir(project)
        store = cls(connect_local(project), project)
        store._ensure_project()
        return store

    @classmethod
    def open_rpc(
        cls,
        project: str,
        host: str = "127.0.0.1",
        port: int = 8080,
        *,
        profile: Optional[str] = None,
    ) -> "LoreStore":
        store = cls(connect_rpc(host, port, profile=profile), project)
        store._ensure_project()
        return store

    def close(self) -> None:
        try:
            self.zapisz()
        except LoreBackendError:
            pass
        self._backend.close()

    # ── Projekt ───────────────────────────────────────────────────────────

    def _ensure_project(self) -> None:
        worlds = self._run_line("LISTA ŚWIATÓW", strict=False)
        names = {w.get("name") for w in worlds.get("worlds", [])}
        if self._project not in names:
            self._run_line(f'UTWÓRZ ŚWIAT "{_esc(self._project)}"')
        self._run_line(f'WYBIERZ ŚWIAT "{_esc(self._project)}"')

    def zapisz(self) -> None:
        """Zapis lore na dysk (pisarz: „Zapisz projekt”)."""
        self._run_line("ZAPISZ ŚWIAT")

    def nazwa_projektu(self) -> str:
        return self._project

    # ── Encje lore ────────────────────────────────────────────────────────

    def dodaj(
        self,
        nazwa: str,
        typ: Union[TypLore, str],
        *,
        notatka: str = "",
        opis: str = "",
        tekst: str = "",
        zrodlo: str = "",
        **extra: Any,
    ) -> str:
        """Utwórz wpis lore (postać, pomysł, wpływ, …). Zwraca nazwę encji."""
        name = self._sanitize_name(nazwa)
        typ_val = typ.value if isinstance(typ, TypLore) else str(typ)
        self._run_line(f'UTRWAL "{_esc(name)}"')
        self._inject(name, "Typ", typ_val)
        if notatka:
            self._inject(name, POLE_NOTATKA, notatka)
        if opis:
            self._inject(name, POLE_OPIS, opis)
        if tekst:
            self._inject(name, POLE_TEKST, tekst)
        if zrodlo:
            self._inject(name, POLE_ŹRÓDŁO, zrodlo)
        for key, val in extra.items():
            if val is not None and val != "":
                self._inject(name, key, val)
        return name

    def dodaj_postac(self, nazwa: str, *, notatka: str = "", opis: str = "") -> str:
        return self.dodaj(nazwa, TypLore.POSTAĆ, notatka=notatka, opis=opis)

    def dodaj_miejsce(self, nazwa: str, *, opis: str = "") -> str:
        return self.dodaj(nazwa, TypLore.MIEJSCE, opis=opis)

    def dodaj_pomysl(self, tekst: str, *, nazwa: str = "", zrodlo: str = "") -> str:
        label = nazwa or self._pomysl_z_tekstu(tekst)
        return self.dodaj(label, TypLore.POMYSŁ, tekst=tekst, zrodlo=zrodlo)

    def dodaj_wplyw(
        self,
        nazwa: str,
        *,
        zrodlo: str = "",
        notatka: str = "",
    ) -> str:
        return self.dodaj(nazwa, TypLore.WPŁYW, zrodlo=zrodlo, notatka=notatka)

    def dodaj_scene(self, nazwa: str, *, opis: str = "", plik: str = "") -> str:
        return self.dodaj(nazwa, TypLore.SCENA, opis=opis, Plik=plik or "")

    def ustaw(self, encja: str, pole: str, wartosc: Any) -> None:
        """Uzupełnij notatkę, opis lub inną cechę."""
        self._inject(self._sanitize_name(encja), pole, wartosc)

    def podglad(self, encja: str) -> Dict[str, Any]:
        """Szczegóły encji do panelu bocznego."""
        row = self._run_line(f'POKAŻ "{_esc(self._sanitize_name(encja))}"')
        raw = row.get("data") or row.get("bubble") or {}
        if isinstance(raw, dict) and "properties" in raw:
            out = dict(raw.get("properties") or {})
            out["_relations"] = list(raw.get("relations") or [])
            out["BĄBEL"] = encja
            return out
        return dict(raw) if isinstance(raw, dict) else {}

    # ── Relacje (koligacje, wpływy) ───────────────────────────────────────

    def polacz(
        self,
        skad: str,
        dokad: str,
        relacja: str,
    ) -> None:
        """
        Połącz dwa elementy lore. relacja = etykieta z RELACJE_LORE
        (np. „wpływa na”, „koliguje z”).
        """
        rel_key = REL_TO_GRAPH.get(relacja, self._slug_rel(relacja))
        a = self._sanitize_name(skad)
        b = self._sanitize_name(dokad)
        self._run_line(f'POŁĄCZ "{_esc(a)}" Z "{_esc(b)}" JAKO "{_esc(rel_key)}"')

    def graf_powiazan(
        self,
        seed: Optional[str] = None,
        promien: int = 2,
    ) -> Dict[str, Any]:
        """Węzły i krawędzie do mapy wizualnej (panel „Mapa lore”)."""
        raw_seed = seed or self._opened_doc
        if not raw_seed:
            return {"seed": "", "nodes": [], "edges": []}
        seed_name = self._sanitize_name(raw_seed)
        visited: set[str] = {seed_name}
        frontier: set[str] = {seed_name}
        for _ in range(max(0, promien)):
            nxt: set[str] = set()
            for n in frontier:
                for s in self.sasiedzi(n, promien=1):
                    if s not in visited:
                        nxt.add(s)
            visited.update(nxt)
            frontier = nxt

        rel_labels = {v: k for k, v in REL_TO_GRAPH.items()}
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_edges: set[tuple] = set()

        for name in sorted(visited):
            data = self.podglad(name)
            nodes.append({"id": name, "typ": data.get("Typ", "Inne")})
            for rel in data.get("_relations") or []:
                if not isinstance(rel, dict):
                    continue
                rel_key = rel.get("relation", "")
                target = rel.get("target", "")
                if target not in visited:
                    continue
                edge_key = (name, target, rel_key)
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                edges.append({
                    "from": name,
                    "to": target,
                    "rel": rel_labels.get(rel_key, rel_key.replace("_", " ")),
                })

        return {"seed": seed_name, "nodes": nodes, "edges": edges}

    def sasiedzi(self, encja: str, promien: int = 2) -> List[str]:
        """Encje w pobliżu na grafie lore (do panelu „powiązane”)."""
        name = self._sanitize_name(encja)
        self._run_line(f'ROZWIJ "{_esc(name)}" PROMIEŃ {int(promien)}', strict=False)
        row = self._run_line(
            f'ZNAJDŹ POŁĄCZONE JAKO "wplywa_na" Z "{_esc(name)}"',
            strict=False,
        )
        out = set(row.get("matches") or [])
        for rel in REL_TO_GRAPH.values():
            row = self._run_line(
                f'ZNAJDŹ POŁĄCZONE JAKO "{_esc(rel)}" Z "{_esc(name)}"',
                strict=False,
            )
            out.update(row.get("matches") or [])
        rev = self._run_line(
            f'ZNAJDŹ GDZIE "BĄBEL" = "{_esc(name)}"',
            strict=False,
        )
        if name in (rev.get("matches") or []):
            out.discard(name)
        return sorted(x for x in out if x != name)

    # ── Dokument ↔ lore (edytor) ──────────────────────────────────────────

    def otworz_dokument(self, sciezka_pliku: str) -> str:
        """
        Rejestruje otwarty rozdział/plik w lore. Wywoływane przy otwarciu karty
        w edytorze — pisarz nie musi nic klikać.
        """
        path = str(Path(sciezka_pliku).resolve())
        doc = self._dokument_z_pliku(path)
        worlds = {w.get("name") for w in self._run_line("LISTA ŚWIATÓW").get("worlds", [])}
        if self._project in worlds:
            self._run_line(f'WYBIERZ ŚWIAT "{_esc(self._project)}"')
        row = self._run_line(f'ZNAJDŹ GDZIE "BĄBEL" = "{_esc(doc)}"', strict=False)
        if doc not in (row.get("matches") or []):
            self.dodaj(doc, TypLore.DOKUMENT, Plik=path, Opis=Path(path).name)
        else:
            self.ustaw(doc, POLE_PLIK, path)
        self._opened_doc = doc
        self._run_line(f'ROZWIJ "{_esc(doc)}" PROMIEŃ 1', strict=False)
        return doc

    def powiaz_z_dokumentem(
        self,
        encja: str,
        sciezka_pliku: Optional[str] = None,
        relacja: str = "występuje w",
    ) -> None:
        """Przypnij postać/pomysł do bieżącego rozdziału."""
        doc = self._opened_doc
        if sciezka_pliku:
            doc = self._dokument_z_pliku(sciezka_pliku)
            self.otworz_dokument(sciezka_pliku)
        if not doc:
            raise LoreBackendError("Brak otwartego dokumentu — otwórz plik w edytorze.")
        self.polacz(encja, doc, relacja)

    def lore_przy_dokumencie(self, sciezka_pliku: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista lore powiązanej z tym rozdziałem (panel boczny)."""
        doc = self._opened_doc
        if sciezka_pliku:
            doc = self._dokument_z_pliku(sciezka_pliku)
        if not doc:
            return []
        items: List[Dict[str, Any]] = []
        for name in self.sasiedzi(doc, promien=1):
            try:
                data = self.podglad(name)
                items.append({
                    "nazwa": name,
                    "typ": data.get("Typ", data.get("v", "Inne")),
                    "opis": self._skrot(
                        data.get(POLE_OPIS) or data.get(POLE_TEKST) or data.get(POLE_NOTATKA) or ""
                    ),
                })
            except LoreBackendError:
                items.append({"nazwa": name, "typ": "?", "opis": ""})
        return items

    def wklej_pomysl_do_dokumentu(self, tekst: str, *, zrodlo: str = "edytor") -> str:
        """Szybki capture: nowy pomysł + powiązanie z otwartym rozdziałem."""
        name = self.dodaj_pomysl(tekst, zrodlo=zrodlo)
        if self._opened_doc:
            self.polacz(name, self._opened_doc, "koliguje z")
        return name

    # ── Wyszukiwanie ──────────────────────────────────────────────────────

    def szukaj(self, fraza: str, *, typ: Optional[str] = None) -> List[str]:
        """Szukaj w notatkach, opisach i tekstach pomysłów."""
        pattern = _esc(fraza)
        clauses = [
            f'"{POLE_NOTATKA}" ILIKE "%{pattern}%"',
            f'"{POLE_OPIS}" ILIKE "%{pattern}%"',
            f'"{POLE_TEKST}" ILIKE "%{pattern}%"',
            f'"{POLE_ŹRÓDŁO}" ILIKE "%{pattern}%"',
        ]
        where = " LUB ".join(clauses)
        if typ:
            where = f'({where}) ORAZ "Typ" = "{_esc(typ)}"'
        row = self._run_line(f"ZNAJDŹ GDZIE {where}", strict=False)
        return list(row.get("matches") or [])

    def lista_po_typie(self, typ: Union[TypLore, str]) -> List[str]:
        t = typ.value if isinstance(typ, TypLore) else str(typ)
        row = self._run_line(f'ZNAJDŹ GDZIE "Typ" = "{_esc(t)}"', strict=False)
        return list(row.get("matches") or [])

    def wszystkie_typy(self) -> List[str]:
        return list(TYPY_LORE)

    def wszystkie_relacje(self) -> List[str]:
        return list(RELACJE_LORE)

    # ── Wewnętrzne ────────────────────────────────────────────────────────

    def _run(self, script: str, *, strict: bool = True) -> List[dict]:
        return self._backend.execute(script.strip(), strict=strict)

    def _run_line(self, line: str, *, strict: bool = True) -> dict:
        return _last(self._run(line, strict=strict))

    def _inject(self, bubble: str, key: str, value: Any) -> None:
        if isinstance(value, (dict, list)):
            payload = json.dumps(value, ensure_ascii=False)
            self._run_line(f'WSTRZYKNIJ "{_esc(key)}" = {payload} DO "{_esc(bubble)}"')
        elif isinstance(value, bool):
            self._run_line(
                f'WSTRZYKNIJ "{_esc(key)}" = {"true" if value else "false"} DO "{_esc(bubble)}"'
            )
        elif isinstance(value, (int, float)):
            self._run_line(f'WSTRZYKNIJ "{_esc(key)}" = {value} DO "{_esc(bubble)}"')
        else:
            self._run_line(f'WSTRZYKNIJ "{_esc(key)}" = "{_esc(str(value))}" DO "{_esc(bubble)}"')

    @staticmethod
    def _sanitize_name(name: str) -> str:
        name = name.strip()
        if not name:
            raise LoreBackendError("Podaj nazwę.")
        clean = re.sub(r"[^\w\-]", "_", name, flags=re.UNICODE)
        clean = re.sub(r"_+", "_", clean).strip("_")
        if not clean:
            raise LoreBackendError("Nieprawidłowa nazwa.")
        return clean[:64]

    @staticmethod
    def _slug_rel(label: str) -> str:
        s = re.sub(r"[^\w]", "_", label.lower(), flags=re.UNICODE)
        return re.sub(r"_+", "_", s).strip("_")[:32] or "powiazanie"

    @staticmethod
    def _dokument_z_pliku(path: str) -> str:
        stem = Path(path).stem
        slug = re.sub(r"[^\w\-]", "_", stem, flags=re.UNICODE)[:40]
        return f"Dok_{slug or 'bez_nazwy'}"

    @staticmethod
    def _pomysl_z_tekstu(tekst: str) -> str:
        words = re.findall(r"\w+", tekst, flags=re.UNICODE)[:4]
        base = "_".join(words) if words else "pomysl"
        return LoreStore._sanitize_name(f"Pomysl_{base}")[:48]

    @staticmethod
    def _skrot(text: str, n: int = 80) -> str:
        t = str(text).replace("\n", " ").strip()
        return t if len(t) <= n else t[: n - 1] + "…"