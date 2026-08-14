"""
Rdzeń i18n: katalogi stringów UI, ładowanie paczek, entry-points, katalogi plugins/.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# ── Domyślne PL (zawsze w pamięci — fallback) ───────────────────────────────

_PL_UI: Dict[str, str] = {
    "app.name": "Lore Editor",
    "app.ready": "Gotowy",
    "app.untitled": "Bez tytułu",
    "app.unsaved": "niezapisane",
    "app.words": "słów",
    "app.language": "Język",
    "app.language_restart": "Zmieniono język na {name}. Część okien użyje nowych etykiet po restarcie.",
    "menu.file": "Plik",
    "menu.edit": "Edycja",
    "menu.lore": "Lore",
    "menu.media": "Media",
    "menu.view": "Wygląd",
    "menu.print": "Wydruk",
    "menu.help": "Pomoc",
    "media.attach_image": "Dodaj zdjęcie / grafikę…",
    "media.attach_audio": "Dodaj muzykę / dźwięk…",
    "media.attach_video": "Dodaj film / klip…",
    "media.attach_any": "Dołącz dowolny plik…",
    "media.preview": "Podgląd / odtwórz…",
    "media.export": "Eksportuj media do pliku…",
    "media.list": "Pokaż listę mediów wpisu",
    "media.hint_select": "Najpierw wybierz postać / miejsce / wpis na panelu Lore (lista po prawej).",
    "media.role_image": "Rola grafiki (portret, mapa, rekwizyt…):",
    "media.role_audio": "Rola dźwięku (głos, motyw, ambience…):",
    "media.role_video": "Rola filmu (klip, cutscene, ref…):",
    "media.role_any": "Rola pliku (portret, głos, klip…):",
    "media.ft_images": "Obrazy",
    "media.ft_audio": "Audio",
    "media.ft_video": "Wideo",
    "media.ft_all": "Wszystkie",
    "media.none": "Brak mediów przy „{name}”.",
    "media.list_title": "Media — {name}",
    "media.export_title": "Zapisz medium jako…",
    "media.export_ok": "Zapisano {path} ({size} B).",
    "file.new": "Nowy",
    "file.open": "Otwórz…",
    "file.save": "Zapisz",
    "file.save_as": "Zapisz jako…",
    "file.project_dir": "Katalog projektu…",
    "file.default_dir": "Domyślny katalog (dokumenty/lore)",
    "file.close_tab": "Zamknij kartę",
    "file.save_lore": "Zapisz projekt lore",
    "file.quit": "Zakończ",
    "edit.undo": "Cofnij",
    "edit.redo": "Ponów",
    "edit.find": "Znajdź…",
    "edit.name_dict": "Słownik nazw…",
    "edit.spellcheck": "Sprawdź pisownię…",
    "edit.wrap": "Zawijaj wiersze",
    "lore.refresh": "Odśwież panel",
    "lore.snapshot": "Utwórz punkt przywracania…",
    "lore.history": "Historia zmian…",
    "view.font_size": "Rozmiar czcionki",
    "view.line_spacing": "Interlinia",
    "print.preview": "Podgląd stron",
    "print.export_docx": "Eksportuj DOCX…",
    "toolbar.catalog": "Katalog…",
    "help.topics": "Tematy",
    "help.close": "Zamknij",
    "help.title": "Pomoc — Lore Editor",
    "help.writer_guide": "Przewodnik pisarza",
    "help.shortcuts": "Skróty klawiszowe",
    "help.fonts": "Czcionki i wygląd",
    "help.print": "Wydruk i eksport",
    "help.panel": "Panel Lore",
    "help.media": "Media (zdjęcia, dźwięk, film)",
    "help.spell": "Słownik i pisownia",
    "help.temporal": "Kontekst czasowy",
    "help.query": "Zapytania semantyczne",
    "help.history": "Historia zmian",
    "help.network": "Sieć: Karmazyn i Cynober DB",
    "help.about": "O programie",
    "spell.lang": "Język korekty",
    "status.close_save_failed": "Nie zapisano lore przy zamykaniu: {error}",
    "status.autosave_failed": "Autosave nieudany: {error}",
    "dialog.cancel": "Anuluj",
    "dialog.save": "Zapisz",
    "dialog.edit": "Edytuj — {name}",
    "panel.add": "Dodaj",
    "panel.add_character": "+ Postać",
    "panel.add_idea": "+ Pomysł",
    "panel.add_influence": "+ Wpływ",
    "panel.tab_chapter": "Rozdział",
    "panel.tab_search": "Szukaj",
    "panel.tab_team": "Zespół",
    "panel.linked_to_file": "Powiązane z tym plikiem:",
    "panel.link_chapter": "Powiąż z rozdziałem",
    "panel.link_other": "Powiąż inny wpis…",
    "panel.connect": "Połącz z…",
    "panel.unlink": "Odłącz od rozdziału",
    "panel.edit_entry": "Edytuj wpis",
    "panel.media_box": "Media (zdjęcie / dźwięk / film)",
    "panel.attach_media": "Dołącz plik…",
    "panel.attach_image": "+ Zdjęcie",
    "panel.attach_audio": "+ Dźwięk",
    "panel.attach_video": "+ Film",
    "panel.preview_media": "Podgląd media…",
    "panel.media_role_prompt": "Rola pliku (portret, głos, klip…):",
    "panel.media_attached": "Dołączono „{role}” ({size} B, {mime}).",
    "panel.preview_failed": "Nie udało się otworzyć podglądu.",
    "panel.delete_entry": "Usuń wpis",
    "panel.map": "Mapa powiązań",
    "panel.refresh": "Odśwież",
    "panel.search_btn": "Szukaj",
    "panel.search_hint": "Zapytanie semantyczne lub fraza.\nNp.: postacie przy Anna nie od 5\ntyp:Postać \"sojusznik\"  ·  wyniki → Rozdział",
    "panel.team_hint": "Sync lore przez cynober-server.\nNajpierw zapisz projekt lokalnie.",
    "panel.push": "Wyślij na serwer",
    "panel.pull": "Pobierz z serwera",
    "panel.sync": "Synchronizuj",
    "panel.open_chapter_first": "Otwórz najpierw rozdział (plik tekstowy) w edytorze.",
    "panel.select_entry": "Wybierz wpis z listy.",
    "panel.select_to_edit": "Wybierz wpis do edycji.",
    "dialog.unsaved_lore": "Niezapisane lore",
    "dialog.unsaved_lore_ask": "Graf lore ma niezapisane zmiany. Zapisać przed zamknięciem?",
    "dialog.close_no_save": "Zamknij bez zapisu lore",
    "dialog.close_no_save_ask": "Zamknąć bez zapisu zmian w grafie lore?",
}

_BUILTIN_META = {
    "pl": {"code": "pl", "name": "Polski", "spell": "pl", "native_name": "Polski"},
    "en": {"code": "en", "name": "English", "spell": "en", "native_name": "English"},
}


@dataclass
class LocalePack:
    """Paczka językowa — UI (+ opcjonalnie help, spell, meta)."""

    code: str
    name: str
    ui: Dict[str, str] = field(default_factory=dict)
    help_topics: Dict[str, tuple[str, str]] = field(default_factory=dict)
    spell: str = "pl"
    native_name: str = ""
    source: str = "builtin"  # builtin | dir | entrypoint
    path: Optional[Path] = None

    def display_name(self) -> str:
        return self.native_name or self.name or self.code


_packs: Dict[str, LocalePack] = {}
_active: str = "pl"
_initialized: bool = False


def _locales_root() -> Path:
    return Path(__file__).resolve().parent.parent / "locales"


def _settings_path() -> Path:
    return Path.home() / ".lore_editor" / "settings.json"


def load_settings() -> dict:
    path = _settings_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        from lore.paths import quarantine_corrupt

        quarantine_corrupt(path)
        return {}


def save_settings(data: dict) -> None:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register_pack(pack: LocalePack) -> None:
    code = pack.code.strip().lower()
    pack.code = code
    _packs[code] = pack


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def load_locale_dir(directory: Path, *, source: str = "dir") -> Optional[LocalePack]:
    """
    Wczytaj paczkę z katalogu:
      meta.json  — code, name, spell, native_name
      ui.json    — klucz → string
      help.json  — opcjonalnie { "topic_id": { "title", "body" } }
    """
    import warnings

    directory = Path(directory)
    if not directory.is_dir():
        return None
    ui_path = directory / "ui.json"
    if not ui_path.is_file():
        return None
    try:
        ui_raw = json.loads(ui_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        warnings.warn(f"Paczka locale {directory}: uszkodzony ui.json ({e})", UserWarning)
        return None
    if not isinstance(ui_raw, dict) or not ui_raw:
        warnings.warn(f"Paczka locale {directory}: pusty ui.json — nie rejestruję.", UserWarning)
        return None
    meta = _load_json(directory / "meta.json")
    ui_map = ui_raw
    help_raw = _load_json(directory / "help.json")
    code = str(meta.get("code") or directory.name).strip().lower()
    if not code:
        return None
    help_topics: Dict[str, tuple[str, str]] = {}
    for tid, val in help_raw.items():
        if isinstance(val, dict):
            title = str(val.get("title") or tid)
            body = str(val.get("body") or "")
            help_topics[str(tid)] = (title, body)
        elif isinstance(val, (list, tuple)) and len(val) >= 2:
            help_topics[str(tid)] = (str(val[0]), str(val[1]))
    pack = LocalePack(
        code=code,
        name=str(meta.get("name") or code),
        native_name=str(meta.get("native_name") or meta.get("name") or code),
        ui={str(k): str(v) for k, v in ui_map.items()},
        help_topics=help_topics,
        spell=str(meta.get("spell") or code),
        source=source,
        path=directory,
    )
    register_pack(pack)
    return pack


def _register_builtin_pl() -> None:
    register_pack(
        LocalePack(
            code="pl",
            name="Polski",
            native_name="Polski",
            ui=dict(_PL_UI),
            spell="pl",
            source="builtin",
        )
    )


def _load_bundled_locales() -> None:
    root = _locales_root()
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "ui.json").is_file():
            load_locale_dir(child, source="builtin")


def _load_entry_points() -> None:
    try:
        from importlib.metadata import entry_points
    except ImportError:
        return
    try:
        eps = entry_points()
        # Python 3.10+ SelectableGroups / 3.12 dict-like
        if hasattr(eps, "select"):
            group = eps.select(group="lore_editor.locale")
        else:
            group = eps.get("lore_editor.locale", [])  # type: ignore[arg-type]
        for ep in group:
            try:
                obj = ep.load()
                if isinstance(obj, LocalePack):
                    obj.source = "entrypoint"
                    register_pack(obj)
                elif callable(obj):
                    pack = obj()
                    if isinstance(pack, LocalePack):
                        pack.source = "entrypoint"
                        register_pack(pack)
                elif isinstance(obj, (str, Path)):
                    load_locale_dir(Path(obj), source="entrypoint")
            except Exception as e:
                import warnings

                warnings.warn(f"Nie załadowano locale entry-point {ep}: {e}", UserWarning)
                continue
    except Exception as e:
        import warnings

        warnings.warn(f"Nie odczytano entry-points lore_editor.locale: {e}", UserWarning)
        return


def _load_plugin_dirs() -> None:
    """
    LORE_LOCALE_PATHS — lista katalogów rozdzielona os.pathsep.
    Każdy podkatalog z meta.json+ui.json = paczka.
    Domyślnie: <repo>/plugins/locales
    """
    candidates: List[Path] = []
    env = os.environ.get("LORE_LOCALE_PATHS", "").strip()
    if env:
        for part in env.split(os.pathsep):
            part = part.strip()
            if part:
                candidates.append(Path(part).expanduser())
    # bundled example plugins
    repo = Path(__file__).resolve().parent.parent.parent
    candidates.append(repo / "plugins" / "locales")
    for base in candidates:
        if not base.is_dir():
            continue
        # either base is a pack, or contains packs
        if (base / "ui.json").is_file():
            load_locale_dir(base, source="dir")
            continue
        for child in sorted(base.iterdir()):
            if child.is_dir() and (child / "ui.json").is_file():
                load_locale_dir(child, source="dir")


def discover_and_load(*, force: bool = False) -> None:
    """Zainicjalizuj rejestry paczek (idempotentne)."""
    global _initialized, _active
    if _initialized and not force:
        return
    _packs.clear()
    _register_builtin_pl()
    _load_bundled_locales()
    _load_entry_points()
    _load_plugin_dirs()
    # Preferencja użytkownika
    preferred = (
        os.environ.get("LORE_LOCALE", "").strip().lower()
        or str(load_settings().get("locale") or "").strip().lower()
    )
    if preferred and preferred in _packs:
        _active = preferred
    elif "pl" in _packs:
        _active = "pl"
    else:
        _active = next(iter(_packs), "pl")
    _initialized = True


def list_locales() -> List[LocalePack]:
    discover_and_load()
    return sorted(_packs.values(), key=lambda p: (p.code != "pl", p.code))


def get_locale() -> str:
    discover_and_load()
    return _active


def set_locale(code: str, *, persist: bool = True) -> LocalePack:
    discover_and_load()
    code = code.strip().lower()
    if code not in _packs:
        raise KeyError(f"Nieznana locale '{code}'. Dostępne: {', '.join(sorted(_packs))}")
    global _active
    _active = code
    if persist:
        data = load_settings()
        data["locale"] = code
        save_settings(data)
    return _packs[code]


def _active_pack() -> LocalePack:
    discover_and_load()
    return _packs.get(_active) or _packs["pl"]


def t(key: str, **kwargs: Any) -> str:
    """Przetłumacz klucz UI; fallback: PL wbudowany → sam klucz."""
    discover_and_load()
    pack = _active_pack()
    text = pack.ui.get(key)
    if text is None and pack.code != "pl":
        pl = _packs.get("pl")
        if pl:
            text = pl.ui.get(key)
    if text is None:
        text = _PL_UI.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def ui(key: str, **kwargs: Any) -> str:
    """Alias t() — czytelniejszy w kodzie UI."""
    return t(key, **kwargs)


def active_spell_code() -> str:
    return _active_pack().spell or get_locale()


def help_topic_map() -> Dict[str, tuple[str, str]]:
    """Tematy pomocy z aktywnej paczki (może być puste — wtedy help_topics.py)."""
    return dict(_active_pack().help_topics)
