"""
LoreStore — API lore dla pisarza. Zero KarminQL w interfejsie.
Narzędzie pisarskie — bez Lua, bez silnika gry.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from cynober_worlds import validate_world_name

from lore.backend import (
    EngineBackend,
    LocalLoreBackend,
    LoreBackendError,
    RpcLoreBackend,
    _esc,
    _last,
    connect_local,
    connect_rpc,
)
from lore.history import LoreHistoria, SnapshotInfo
from lore.lifecycle import metadane_zycia, sortuj_po_temperaturze
from lore.paths import LORE_PROJECT_FILE, ProjectPaths
from lore.query import parsuj_zapytanie, wykonaj_zapytanie
from lore.team_sync import ZespolLore
from lore.temporal import (
    dokumenty_uporzadkowane,
    parse_stany,
    pole_temporalne,
    scal_stan,
    ustaw_stan_rozdzialu,
)
from lore.types import (
    POLE_DOTYK,
    POLE_NOTATKA,
    POLE_OPIS,
    POLE_PLIK,
    POLE_STANY,
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

    def __init__(
        self,
        backend: EngineBackend,
        paths: ProjectPaths,
    ):
        self._backend = backend
        self._paths = paths
        self._project = paths.name
        self._opened_doc: Optional[str] = None
        self._dirty = False
        self._historia = LoreHistoria(paths.root, paths.name)

    @classmethod
    def open_local(
        cls,
        project: str | None = None,
        *,
        project_dir: str | Path | None = None,
    ) -> "LoreStore":
        paths = ProjectPaths.discover(project, project_dir)
        store = cls(connect_local(paths), paths)
        store._ensure_project()
        if not (paths.root / LORE_PROJECT_FILE).is_file():
            paths.write_marker()
        return store

    @classmethod
    def open_rpc(
        cls,
        project: str | None = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        *,
        profile: Optional[str] = None,
        project_dir: str | Path | None = None,
        user: Optional[str] = None,
        token: Optional[str] = None,
    ) -> "LoreStore":
        paths = ProjectPaths.discover(project, project_dir)
        store = cls(
            connect_rpc(
                host, port, profile=profile, user=user, token=token, login=True
            ),
            paths,
        )
        store._ensure_project()
        return store

    def close(self, *, zapisz_lore: bool = True) -> None:
        """
        Zamyka backend.
        zapisz_lore=True  → zapisz() potem release bez drugiego flush.
        zapisz_lore=False → porzuć dirty w RAM (bez zapisu na dysk).
        Błędy zapisu/close nie są połykane.
        """
        save_err: Exception | None = None
        if zapisz_lore:
            try:
                # zawsze ZAPISZ gdy proszono — indeksy + spójność .kafd
                self.zapisz()
            except Exception as e:
                save_err = e
        close_err: Exception | None = None
        try:
            # NIGDY auto-flush tu: przy zapisz_lore=False to byłby wyciek zapisu
            close_fn = getattr(self._backend, "close")
            try:
                close_fn(flush=False)
            except TypeError:
                close_fn()
        except Exception as e:
            close_err = e
        if save_err is not None:
            raise LoreBackendError(f"Zapis lore przy zamykaniu nieudany: {save_err}") from save_err
        if close_err is not None:
            raise LoreBackendError(f"Błąd zamykania backendu: {close_err}") from close_err

    # ── Projekt ───────────────────────────────────────────────────────────

    def _ensure_project(self) -> None:
        worlds = self._run_line("LISTA ŚWIATÓW", strict=False)
        if worlds.get("status") == "error":
            raise LoreBackendError(
                worlds.get("message")
                or "LISTA ŚWIATÓW nieudana — sprawdź auth RPC (LORE_RPC_USER/TOKEN)."
            )
        names = {w.get("name") for w in worlds.get("worlds", [])}
        if self._project not in names:
            self._run_line(f'UTWÓRZ ŚWIAT "{_esc(self._project)}"')
        attach = self._run_line(f'WYBIERZ ŚWIAT "{_esc(self._project)}"')
        if attach.get("status") == "error":
            raise LoreBackendError(
                attach.get("message")
                or f"Nie dołączono świata '{self._project}' (ACL / logowanie RPC)."
            )
        if self.tryb_lokalny():
            self._historia.inicjalizuj()
            self._historia.utworz_bazowy_jesli_pusty()

    def zapisz(self, *, historia_auto: bool = True, historia_label: str = "") -> None:
        """Zapis lore na dysk (pisarz: „Zapisz projekt”)."""
        self._odswiez_indeksy()
        self._run_line("ZAPISZ ŚWIAT")
        self._dirty = False
        if historia_auto and self.tryb_lokalny():
            if historia_label:
                self._historia.utworz(label=historia_label, reason="save")
            else:
                self._historia.moze_auto_snapshot()

    def historia(self) -> LoreHistoria:
        return self._historia

    def utworz_snapshot(self, opis: str = "") -> Optional[SnapshotInfo]:
        """Ręczny punkt przywracania (lore + rozdziały)."""
        if not self.tryb_lokalny():
            raise LoreBackendError("Historia wymaga trybu lokalnego.")
        return self._historia.utworz(label=opis, reason="manual", force=True)

    def lista_historii(self) -> List[SnapshotInfo]:
        return self._historia.lista()

    def przywroc_historie(
        self,
        snap_id: str,
        *,
        strict: bool = True,
    ) -> SnapshotInfo:
        """
        Przywraca snapshot; bieżący stan zapisywany jest automatycznie.

        strict=True (domyślnie): usuwa rozdziały .txt/.md spoza snapshota
        (pełny powrót w czasie). strict=False: tylko nadpisuje pliki ze snapshota.
        """
        if not self.tryb_lokalny():
            raise LoreBackendError("Historia wymaga trybu lokalnego.")
        info = self._historia.przywroc(snap_id, strict=strict)
        backend = self._backend
        if hasattr(backend, "reload"):
            backend.reload()  # type: ignore[attr-defined]
        self._opened_doc = None
        self._dirty = False
        self._run_line(f'WYBIERZ ŚWIAT "{_esc(self._project)}"')
        return info

    def lore_niezapisane(self) -> bool:
        """Czy graf lore ma zmiany niezsynchronizowane z .kafd."""
        if self._dirty:
            return True
        # desync: mutacja tylko na world.dirty (np. ROZWIŃ / inject poza API)
        backend = self._backend
        world = getattr(backend, "_world", None)
        if world is not None and getattr(world, "dirty", False):
            return True
        return False

    def nazwa_projektu(self) -> str:
        return self._project

    def katalog_projektu(self) -> Path:
        """Folder z rozdziałami i plikami .kafd."""
        return self._paths.root

    def tryb_lokalny(self) -> bool:
        return isinstance(self._backend, LocalLoreBackend)

    def zespol(self) -> ZespolLore:
        if not self.tryb_lokalny():
            raise LoreBackendError("Sync plików wymaga trybu lokalnego (bez --rpc).")
        return ZespolLore(self._paths)

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
        name = self._sanitize_entity(nazwa)
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
        self._dotknij(name)
        self._oznacz_brudne()
        return name

    def dodaj_postac(self, nazwa: str, *, notatka: str = "", opis: str = "") -> str:
        return self.dodaj(nazwa, TypLore.POSTAĆ, notatka=notatka, opis=opis)

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

    def ustaw(
        self,
        encja: str,
        pole: str,
        wartosc: Any,
        *,
        as_of: Optional[str] = None,
    ) -> None:
        """Uzupełnij cechę — w kontekście rozdziału zapisuje mutację czasową."""
        name = self._sanitize_entity(encja)
        doc = as_of or self._opened_doc
        data = self.podglad(name, as_of=doc, surowe=True)
        typ = str(data.get("Typ") or TypLore.INNE.value)

        if doc and pole_temporalne(pole, typ):
            stany = parse_stany(data.get(POLE_STANY))
            stany = ustaw_stan_rozdzialu(stany, doc, pole, wartosc)
            self._inject(name, POLE_STANY, stany)
        else:
            self._inject(name, pole, wartosc)

        self._dotknij(name)
        self._oznacz_brudne()

    def podglad(
        self,
        encja: str,
        *,
        as_of: Optional[str] = None,
        surowe: bool = False,
    ) -> Dict[str, Any]:
        """Szczegóły encji; as_of = bąbel dokumentu dla widoku „w tym rozdziale”."""
        name = self._sanitize_entity(encja)
        row = self._run_line(f'POKAŻ "{_esc(name)}"')
        raw = row.get("data") or row.get("bubble") or {}
        if isinstance(raw, dict) and "properties" in raw:
            out = dict(raw.get("properties") or {})
            out["_relations"] = list(raw.get("relations") or [])
            out["BĄBEL"] = name
        else:
            out = dict(raw) if isinstance(raw, dict) else {}

        if surowe:
            return out

        ctx = as_of or self._opened_doc
        stany = parse_stany(out.get(POLE_STANY))
        kolejnosc = self._kolejnosc_dokumentow()
        resolved = scal_stan(out, stany, as_of=ctx, kolejnosc=kolejnosc)
        resolved["_relations"] = out.get("_relations", [])
        resolved["BĄBEL"] = name
        if ctx:
            resolved["_as_of"] = ctx
        meta = metadane_zycia(name, out, kolejnosc, biezacy_doc=ctx)
        resolved["_temperatura"] = meta["temperatura"]
        resolved["_ostatni_rozdzial"] = meta["ostatni_rozdzial"]
        return resolved

    # ── Relacje (koligacje, wpływy) ───────────────────────────────────────

    def polacz(
        self,
        skad: str,
        dokad: str,
        relacja: str,
    ) -> None:
        rel_key = REL_TO_GRAPH.get(relacja, self._slug_rel(relacja))
        a = self._sanitize_entity(skad)
        b = self._sanitize_entity(dokad)
        if not self.encja_istnieje(a):
            raise LoreBackendError(f"Nie ma wpisu „{skad}”.")
        if not self.encja_istnieje(b):
            raise LoreBackendError(f"Nie ma wpisu „{dokad}”.")
        self._run_line(f'POŁĄCZ "{_esc(a)}" Z "{_esc(b)}" JAKO "{_esc(rel_key)}"')
        self._dotknij(a)
        self._dotknij(b)
        self._oznacz_brudne()

    def rozlacz(self, skad: str, dokad: str, relacja: str) -> None:
        rel_key = REL_TO_GRAPH.get(relacja, self._slug_rel(relacja))
        a = self._sanitize_entity(skad)
        b = self._sanitize_entity(dokad)
        self._run_line(f'ROZŁĄCZ "{_esc(a)}" Z "{_esc(b)}" JAKO "{_esc(rel_key)}"')
        self._dotknij(a)
        self._dotknij(b)
        self._oznacz_brudne()

    def usun_encje(self, encja: str) -> None:
        """Trwale usuwa wpis lore (postać, pomysł, wpływ…)."""
        name = self._sanitize_entity(encja)
        if not self.encja_istnieje(name):
            raise LoreBackendError(f"Nie ma wpisu „{encja}”.")
        if self.tryb_lokalny():
            self._historia.utworz(label=f"przed usunięciem {name}", reason="pre_delete", force=True)
        self._rozlacz_wszystkie_relacje(name)
        self._run_line(f'USUŃ BĄBEL "{_esc(name)}"')
        if self._opened_doc == name:
            self._opened_doc = None
        self._odswiez_indeksy()
        self._oznacz_brudne()

    def odlacz_od_dokumentu(
        self,
        encja: str,
        sciezka_pliku: Optional[str] = None,
    ) -> None:
        """Usuwa powiązanie z rozdziałem — wpis lore zostaje w projekcie."""
        doc = self._opened_doc
        if sciezka_pliku:
            doc = self._dokument_z_pliku(sciezka_pliku)
        if not doc:
            raise LoreBackendError("Brak otwartego dokumentu — otwórz plik w edytorze.")
        a = self._sanitize_entity(encja)
        removed = self._rozlacz_jesli_polaczone(a, doc)
        if not removed:
            removed = self._rozlacz_jesli_polaczone(doc, a)
        if not removed:
            raise LoreBackendError(f"„{encja}” nie jest powiązane z tym rozdziałem.")
        self._dotknij(a)
        self._odswiez_indeksy()
        self._oznacz_brudne()

    def _rozlacz_wszystkie_relacje(self, encja: str) -> None:
        """Usuwa relacje przychodzące i wychodzące przed skasowaniem bąbla."""
        name = self._sanitize_entity(encja)
        for other in list(self.wszystkie_wpisy()):
            if other == name:
                continue
            self._rozlacz_jesli_polaczone(other, name)
            self._rozlacz_jesli_polaczone(name, other)
        if self.encja_istnieje(name):
            try:
                data = self.podglad(name)
                for rel in list(data.get("_relations") or []):
                    if not isinstance(rel, dict):
                        continue
                    target = rel.get("target")
                    rel_key = rel.get("relation", "")
                    if target and rel_key:
                        self._run_line(
                            f'ROZŁĄCZ "{_esc(name)}" Z "{_esc(target)}" JAKO "{_esc(rel_key)}"'
                        )
            except LoreBackendError:
                pass

    def _rozlacz_jesli_polaczone(self, skad: str, dokad: str) -> bool:
        try:
            data = self.podglad(skad)
        except LoreBackendError:
            return False
        removed = False
        for rel in data.get("_relations") or []:
            if not isinstance(rel, dict):
                continue
            if rel.get("target") != dokad:
                continue
            rel_key = rel.get("relation", "")
            if not rel_key:
                continue
            self._run_line(f'ROZŁĄCZ "{_esc(skad)}" Z "{_esc(dokad)}" JAKO "{_esc(rel_key)}"')
            removed = True
        return removed

    def graf_powiazan(
        self,
        seed: Optional[str] = None,
        promien: int = 2,
    ) -> Dict[str, Any]:
        raw_seed = seed or self._opened_doc
        if not raw_seed:
            return {"seed": "", "nodes": [], "edges": []}
        seed_name = self._sanitize_entity(raw_seed)
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
        name = self._sanitize_entity(encja)
        self._run_line(f'ROZWIŃ "{_esc(name)}" PROMIEŃ {int(promien)}', strict=False)
        out: set[str] = set()
        for rel in REL_TO_GRAPH.values():
            row = self._run_line(
                f'ZNAJDŹ POŁĄCZONE JAKO "{_esc(rel)}" Z "{_esc(name)}"',
                strict=False,
            )
            out.update(row.get("matches") or [])
        try:
            data = self.podglad(name)
            for rel in data.get("_relations") or []:
                if isinstance(rel, dict):
                    target = rel.get("target")
                    if target:
                        out.add(str(target))
        except LoreBackendError:
            pass
        out.discard(name)
        return sorted(out)

    def encja_istnieje(self, encja: str) -> bool:
        name = self._sanitize_entity(encja)
        row = self._run_line(f'ZNAJDŹ GDZIE "BĄBEL" = "{_esc(name)}"', strict=False)
        return name in (row.get("matches") or [])

    def wszystkie_wpisy(self) -> List[str]:
        out: set[str] = set()
        for typ in TYPY_LORE:
            out.update(self.lista_po_typie(typ))
        return sorted(out)

    # ── Dokument ↔ lore (edytor) ──────────────────────────────────────────

    def otworz_dokument(self, sciezka_pliku: str) -> str:
        path = str(Path(sciezka_pliku).resolve())
        doc = self._dokument_z_pliku(path)
        plik = self._paths.plik_wzgledny(path)
        worlds = {w.get("name") for w in self._run_line("LISTA ŚWIATÓW").get("worlds", [])}
        if self._project in worlds:
            self._run_line(f'WYBIERZ ŚWIAT "{_esc(self._project)}"')
        row = self._run_line(f'ZNAJDŹ GDZIE "BĄBEL" = "{_esc(doc)}"', strict=False)
        if doc not in (row.get("matches") or []):
            self.dodaj(doc, TypLore.DOKUMENT, Plik=plik, Opis=Path(path).name)
        else:
            try:
                cur = self.podglad(doc, surowe=True)
            except LoreBackendError:
                cur = {}
            if cur.get(POLE_PLIK) != plik:
                self.ustaw(doc, POLE_PLIK, plik)
        self._opened_doc = doc
        self._run_line(f'ROZWIŃ "{_esc(doc)}" PROMIEŃ 1', strict=False)
        return doc

    def powiaz_z_dokumentem(
        self,
        encja: str,
        sciezka_pliku: Optional[str] = None,
        relacja: str = "występuje w",
    ) -> None:
        enc = self._sanitize_entity(encja)
        if not self.encja_istnieje(enc):
            raise LoreBackendError(
                f"Nie ma wpisu „{encja}”. Dodaj go (+ Postać / + Pomysł / + Wpływ) lub użyj Szukaj."
            )
        doc = self._opened_doc
        if sciezka_pliku:
            self.otworz_dokument(sciezka_pliku)
            doc = self._dokument_z_pliku(sciezka_pliku)
        if not doc:
            raise LoreBackendError("Brak otwartego dokumentu — otwórz i zapisz plik rozdziału w edytorze.")
        self.polacz(enc, doc, relacja)
        self._dotknij(enc)

    def lore_przy_dokumencie(
        self,
        sciezka_pliku: Optional[str] = None,
        *,
        ukryj_grobowiec: bool = True,
    ) -> List[Dict[str, Any]]:
        doc = self._opened_doc
        if sciezka_pliku:
            doc = self._dokument_z_pliku(sciezka_pliku)
        if not doc:
            return []
        items: List[Dict[str, Any]] = []
        for name in self.sasiedzi(doc, promien=1):
            try:
                data = self.podglad(name, as_of=doc)
                items.append({
                    "nazwa": name,
                    "typ": data.get("Typ", data.get("v", "Inne")),
                    "opis": self._skrot(
                        data.get(POLE_OPIS) or data.get(POLE_TEKST) or data.get(POLE_NOTATKA) or ""
                    ),
                    "temperatura": data.get("_temperatura"),
                    "ostatni_rozdzial": data.get("_ostatni_rozdzial"),
                })
            except LoreBackendError:
                items.append({"nazwa": name, "typ": "?", "opis": ""})
        return sortuj_po_temperaturze(items, ukryj_grobowiec=ukryj_grobowiec)

    def wklej_pomysl_do_dokumentu(
        self,
        tekst: str,
        *,
        zrodlo: str = "edytor",
        sciezka_pliku: Optional[str] = None,
    ) -> str:
        name = self.dodaj_pomysl(tekst, zrodlo=zrodlo)
        if sciezka_pliku:
            self.powiaz_z_dokumentem(name, sciezka_pliku, relacja="koliguje z")
        elif self._opened_doc:
            self.polacz(name, self._opened_doc, "koliguje z")
        return name

    # ── Multimedia (Faza 1 — lokalnie; RPC przez put_media) ────────────────

    def _phi_store(self) -> Any:
        """Surowy Store Karmazyna (tylko LocalLoreBackend)."""
        if not self.tryb_lokalny():
            raise LoreBackendError(
                "Bezpośredni Store wymaga trybu lokalnego. "
                "W --rpc użyj dodaj_media (KAFS) lub pracuj lokalnie."
            )
        backend = self._backend
        world = backend._attach()  # type: ignore[attr-defined]
        rt = world.runtime
        if hasattr(rt, "engine") and hasattr(rt.engine, "api"):
            return rt.engine.api.store
        return rt.store

    def dodaj_media(
        self,
        encja: str,
        rola: str,
        sciezka_lub_bajty: Union[str, Path, bytes, bytearray],
        *,
        mime: Optional[str] = None,
        force_stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Dołącz plik/bajty do encji lore (binding w bąblu).

        Lokalnie: karmazyn_media.attach_* + dirty.
        RPC: CynoberClient.put_media (wymaga kafs-stream).
        """
        name = self._sanitize_entity(encja)
        role = (rola or "").strip() or "portret"
        if not self.encja_istnieje(name) and self.tryb_lokalny():
            # auto-utwórz postać gdy brak
            self.dodaj_postac(name)

        if isinstance(self._backend, RpcLoreBackend):
            client = getattr(self._backend, "_client", None)
            if client is None or not callable(getattr(client, "put_media", None)):
                raise LoreBackendError("Klient RPC bez put_media — zaktualizuj cynober-db.")
            if isinstance(sciezka_lub_bajty, (bytes, bytearray)):
                data = bytes(sciezka_lub_bajty)
                use_mime = mime or "application/octet-stream"
            else:
                p = Path(sciezka_lub_bajty).expanduser()
                if not p.is_file():
                    raise LoreBackendError(f"Brak pliku: {p}")
                data = p.read_bytes()
                if mime:
                    use_mime = mime
                else:
                    import mimetypes

                    use_mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
            atom_id = f"m_{name}_{role}".replace(" ", "_")[:48]
            end = client.put_media(
                atom_id,
                data,
                mime=use_mime,
                bubble=name,
                binding=role,
            )
            if end.get("status") != "ok":
                raise LoreBackendError(end.get("message") or "put_media nieudane")
            self._oznacz_brudne()
            return {
                "atom_id": atom_id,
                "binding": role,
                "mime": use_mime,
                "size": len(data),
                "bubble": name,
                "rpc": True,
            }

        import karmazyn_media as km

        store = self._phi_store()
        if isinstance(sciezka_lub_bajty, (bytes, bytearray)):
            ref = km.attach_bytes(
                store,
                name,
                role,
                bytes(sciezka_lub_bajty),
                mime=mime or "application/octet-stream",
                as_root=True,
                force_stream=force_stream,
            )
        else:
            ref = km.attach_file(
                store,
                name,
                role,
                sciezka_lub_bajty,
                mime=mime,
                as_root=True,
                force_stream=force_stream,
            )
        self._oznacz_brudne()
        return {
            "atom_id": ref.atom_id,
            "binding": ref.binding,
            "mime": ref.mime,
            "size": ref.size,
            "bubble": ref.bubble_label,
            "cas12": ref.cas12,
            "rpc": False,
            "stream": km.is_stream_atom(store.get_atom(ref.atom_id)),
        }

    def lista_mediow(self, encja: str) -> List[Dict[str, Any]]:
        """Lista bindingów mediów przy encji (lokalnie)."""
        name = self._sanitize_entity(encja)
        if isinstance(self._backend, RpcLoreBackend):
            # RPC: brak pełnej listy bez KarminQL — zwróć puste + komunikat w polu
            return []
        import karmazyn_media as km

        store = self._phi_store()
        out: List[Dict[str, Any]] = []
        for ref in km.list_bindings(store, name):
            out.append({
                "atom_id": ref.atom_id,
                "binding": ref.binding,
                "mime": ref.mime,
                "size": ref.size,
                "cas12": ref.cas12,
            })
        return out

    def eksport_media(
        self,
        encja: str,
        rola: str,
        sciezka: str | Path,
    ) -> int:
        """Zapisz medium bindingu do pliku. Zwraca bajty."""
        name = self._sanitize_entity(encja)
        role = (rola or "").strip()
        if isinstance(self._backend, RpcLoreBackend):
            client = getattr(self._backend, "_client", None)
            if client is None or not callable(getattr(client, "get_media", None)):
                raise LoreBackendError("Klient RPC bez get_media.")
            # szukaj id po konwencji put
            atom_id = f"m_{name}_{role}".replace(" ", "_")[:48]
            data, _mime, _meta = client.get_media(atom_id)
            p = Path(sciezka).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return len(data)

        import karmazyn_media as km

        store = self._phi_store()
        for ref in km.list_bindings(store, name):
            if ref.binding == role:
                return km.export_to_path(store, ref.atom_id, sciezka)
        raise LoreBackendError(f"Brak media „{role}” przy „{name}”.")

    def odczyt_media(self, encja: str, rola: str) -> Tuple[bytes, str]:
        """(bytes, mime) dla bindingu."""
        name = self._sanitize_entity(encja)
        role = (rola or "").strip()
        if isinstance(self._backend, RpcLoreBackend):
            client = getattr(self._backend, "_client", None)
            atom_id = f"m_{name}_{role}".replace(" ", "_")[:48]
            data, mime, _ = client.get_media(atom_id)
            return data, mime
        import karmazyn_media as km

        store = self._phi_store()
        for ref in km.list_bindings(store, name):
            if ref.binding == role:
                return km.get_bytes(store, ref.atom_id)
        raise LoreBackendError(f"Brak media „{role}” przy „{name}”.")

    # ── Wyszukiwanie ──────────────────────────────────────────────────────

    def zapytaj(self, tekst: str) -> List[Dict[str, Any]]:
        """Zapytanie semantyczne po grafie (np. postacie przy X nie od 5)."""
        zap = parsuj_zapytanie(tekst)
        ctx = self._opened_doc
        return wykonaj_zapytanie(
            zap,
            wszystkie=self.wszystkie_wpisy,
            sasiedzi=lambda n: self.sasiedzi(n, promien=1),
            podglad=lambda n: self.podglad(n, as_of=ctx),
            szukaj_tekst=lambda f: self.szukaj(f),
            kolejnosc=self._kolejnosc_dokumentow(),
            sanitize=self._sanitize_entity,
        )

    def kolejnosc_rozdzialow(self) -> List[Tuple[int, str, str]]:
        """Uporządkowana oś narracji: (nr rozdziału, bąbel, ścieżka pliku)."""
        return self._kolejnosc_dokumentow()

    def dokument_biezacy(self, sciezka_pliku: Optional[str] = None) -> Optional[str]:
        """Bąbel dokumentu dla kontekstu as_of (bez zapisu)."""
        if sciezka_pliku:
            return self._dokument_z_pliku(sciezka_pliku)
        return self._opened_doc

    def szukaj(self, fraza: str, *, typ: Optional[str] = None) -> List[str]:
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

    # ── Wewnętrzne ────────────────────────────────────────────────────────

    def _kolejnosc_dokumentow(self) -> List[Tuple[int, str, str]]:
        docs: List[Tuple[str, Dict[str, Any]]] = []
        for name in self.lista_po_typie(TypLore.DOKUMENT):
            try:
                docs.append((name, self.podglad(name, surowe=True)))
            except LoreBackendError:
                continue
        return dokumenty_uporzadkowane(docs)

    def _dotknij(self, encja: str) -> None:
        self._inject(self._sanitize_entity(encja), POLE_DOTYK, time.time())

    def _oznacz_brudne(self) -> None:
        self._dirty = True

    def _odswiez_indeksy(self) -> None:
        """Przebuduj inv_index/atom_index z aktualnych bąbli — usuwa martwe wpisy."""
        if not self.tryb_lokalny():
            return
        from cynober_worlds import rebuild_all_indexes

        world = self._backend._attach()  # type: ignore[attr-defined]
        with world.runtime.lock:
            rebuild_all_indexes(world.runtime.engine.api)
        self._backend._registry.mark_dirty(world.name)  # type: ignore[attr-defined]

    def _run(self, script: str, *, strict: bool = True) -> List[dict]:
        return self._backend.execute(script.strip(), strict=strict)

    def _run_line(self, line: str, *, strict: bool = True) -> dict:
        row = _last(self._run(line, strict=strict))
        # RPC + strict=False: nadal wykryj status error w odpowiedzi
        if strict and row.get("status") == "error":
            raise LoreBackendError(row.get("message") or "Błąd zapytania lore")
        return row

    def _inject(self, bubble: str, key: str, value: Any) -> None:
        verb = "WSTRZYKNIJ"
        if self.encja_istnieje(bubble):
            props = self.podglad(bubble, surowe=True)
            if key in props:
                verb = "ZAKTUALIZUJ"
        target = f'"{_esc(bubble)}"'
        if isinstance(value, (dict, list)):
            payload = json.dumps(value, ensure_ascii=False)
            self._run_line(f'{verb} "{_esc(key)}" = {payload} DO {target}')
        elif isinstance(value, bool):
            self._run_line(
                f'{verb} "{_esc(key)}" = {"true" if value else "false"} DO {target}'
            )
        elif isinstance(value, (int, float)):
            self._run_line(f'{verb} "{_esc(key)}" = {value} DO {target}')
        else:
            self._run_line(f'{verb} "{_esc(key)}" = "{_esc(str(value))}" DO {target}')

    @staticmethod
    def _sanitize_entity(name: str) -> str:
        name = name.strip()
        if not name:
            raise LoreBackendError("Podaj nazwę.")
        clean = re.sub(r"[^\w\-]", "_", name, flags=re.UNICODE)
        clean = re.sub(r"_+", "_", clean).strip("_")
        if not clean:
            raise LoreBackendError("Nieprawidłowa nazwa.")
        return clean[:64]

    @staticmethod
    def _sanitize_project(name: str) -> str:
        return validate_world_name(name)

    @staticmethod
    def _slug_rel(label: str) -> str:
        s = re.sub(r"[^\w]", "_", label.lower(), flags=re.UNICODE)
        return re.sub(r"_+", "_", s).strip("_")[:32] or "powiazanie"

    def _dokument_z_pliku(self, path: str) -> str:
        p = Path(path).resolve()
        try:
            rel = p.relative_to(self._paths.root)
            slug_base = str(rel.with_suffix("")).replace("\\", "/").replace("/", "_")
        except ValueError:
            slug_base = p.stem
        slug = re.sub(r"[^\w\-]", "_", slug_base, flags=re.UNICODE)[:48]
        return f"Dok_{slug or 'bez_nazwy'}"

    @staticmethod
    def _pomysl_z_tekstu(tekst: str) -> str:
        words = re.findall(r"\w+", tekst, flags=re.UNICODE)[:4]
        base = "_".join(words) if words else "pomysl"
        return LoreStore._sanitize_entity(f"Pomysl_{base}")[:48]

    @staticmethod
    def _skrot(text: str, n: int = 80) -> str:
        t = str(text).replace("\n", " ").strip()
        return t if len(t) <= n else t[: n - 1] + "…"