"""
UI: słownik nazw własnych (lore) oraz sprawdzanie pisowni.

Otwierane z menu Edycja — bez zależności sieciowych.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from lore.spellcheck import SpellChecker, WordSpan, backend_label
from lore.store import LoreStore
from lore.theme import style_listbox, style_text
from lore.types import (
    POLE_NOTATKA,
    POLE_OPIS,
    POLE_TEKST,
    POLE_ŹRÓDŁO,
    TYPY_LORE,
)

# Tk Text tag for misspellings
TAG_SPELL = "spell_err"


def _selection_or_word(text: tk.Text) -> str:
    try:
        return text.get("sel.first", "sel.last").strip()
    except tk.TclError:
        pass
    # Słowo pod kursorem
    try:
        start = text.index("insert wordstart")
        end = text.index("insert wordend")
        return text.get(start, end).strip()
    except tk.TclError:
        return ""


def _index_from_offset(text: tk.Text, offset: int) -> str:
    """Zamień offset znakowy (0-based w treści bez końcowego \\n Tk) na indeks Tk."""
    return f"1.0+{offset}c"


class NameDictionaryDialog(tk.Toplevel):
    """Przeglądarka nazw z lore (postacie, miejsca, …)."""

    def __init__(
        self,
        parent: tk.Misc,
        lore: LoreStore,
        *,
        initial_query: str = "",
        on_insert: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.title("Słownik nazw (lore)")
        self.transient(parent.winfo_toplevel())
        self.minsize(420, 380)
        self.geometry("520x480")
        self._lore = lore
        self._on_insert = on_insert
        self._all_names: list[str] = []
        self._by_name: dict[str, dict] = {}

        hdr = ttk.Frame(self, padding=8)
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Szukaj nazwy z lore:", style="Head.TLabel").pack(anchor="w")
        row = ttk.Frame(hdr)
        row.pack(fill="x", pady=(6, 0))
        self._query = ttk.Entry(row)
        self._query.pack(side="left", fill="x", expand=True)
        if initial_query:
            self._query.insert(0, initial_query)
        ttk.Button(row, text="Szukaj", command=self._refresh_list).pack(side="left", padx=(6, 0))

        filt = ttk.Frame(self, padding=(8, 0))
        filt.pack(fill="x")
        ttk.Label(filt, text="Typ:", style="Dim.TLabel").pack(side="left")
        self._typ_var = tk.StringVar(value="(wszystkie)")
        types = ["(wszystkie)"] + list(TYPY_LORE)
        self._typ = ttk.Combobox(filt, textvariable=self._typ_var, values=types, state="readonly", width=16)
        self._typ.pack(side="left", padx=(6, 0))
        self._typ.bind("<<ComboboxSelected>>", lambda _e: self._refresh_list())

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=2)

        self._list = tk.Listbox(left, height=16, exportselection=False)
        style_listbox(self._list)
        sb = ttk.Scrollbar(left, orient="vertical", command=self._list.yview)
        self._list.configure(yscrollcommand=sb.set)
        self._list.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._list.bind("<<ListboxSelect>>", lambda _e: self._show_detail())
        self._list.bind("<Double-Button-1>", lambda _e: self._insert_selected())

        ttk.Label(right, text="Szczegóły", style="Dim.TLabel").pack(anchor="w")
        self._detail = tk.Text(right, height=16, wrap="word", state="disabled")
        style_text(self._detail, height=16)
        self._detail.pack(fill="both", expand=True, pady=(4, 0))

        btns = ttk.Frame(self, padding=8)
        btns.pack(fill="x")
        ttk.Button(btns, text="Wstaw do tekstu", command=self._insert_selected).pack(side="right", padx=(4, 0))
        ttk.Button(btns, text="Zamknij", command=self.destroy).pack(side="right")

        self._query.bind("<Return>", lambda _e: self._refresh_list())
        self._query.bind("<KeyRelease>", lambda _e: self._refresh_list())
        self.bind("<Escape>", lambda _e: self.destroy())

        self._load_index()
        self._refresh_list()
        self._query.focus_set()
        if initial_query:
            self._select_first()

    def _load_index(self) -> None:
        self._all_names = []
        self._by_name = {}
        try:
            names = self._lore.wszystkie_wpisy()
        except Exception:
            names = []
        for name in names:
            try:
                data = self._lore.podglad(name)
            except Exception:
                data = {"Typ": "?"}
            typ = str(data.get("Typ") or "?")
            # Pomiń czyste „Dokument” w słowniku nazw własnych (opcjonalnie zostaw)
            self._all_names.append(name)
            self._by_name[name] = data

    def _refresh_list(self) -> None:
        q = self._query.get().strip().casefold()
        typ_f = self._typ_var.get()
        self._list.delete(0, tk.END)
        for name in self._all_names:
            data = self._by_name.get(name) or {}
            typ = str(data.get("Typ") or "")
            if typ_f != "(wszystkie)" and typ != typ_f:
                continue
            if q and q not in name.casefold():
                # też w notatce/opisie
                blob = " ".join(
                    str(data.get(k) or "")
                    for k in (POLE_NOTATKA, POLE_OPIS, POLE_TEKST, POLE_ŹRÓDŁO)
                ).casefold()
                if q not in blob:
                    continue
            label = f"{name}  ·  {typ}" if typ else name
            self._list.insert(tk.END, label)
        if self._list.size():
            self._list.selection_set(0)
            self._show_detail()
        else:
            self._set_detail("Brak pasujących nazw w lore.\nDodaj postać / miejsce w panelu Lore.")

    def _selected_name(self) -> Optional[str]:
        sel = self._list.curselection()
        if not sel:
            return None
        label = self._list.get(sel[0])
        # "Name  ·  Typ"
        name = label.split("  ·  ", 1)[0].strip()
        return name or None

    def _show_detail(self) -> None:
        name = self._selected_name()
        if not name:
            return
        data = self._by_name.get(name) or {}
        lines = [
            name,
            f"Typ: {data.get('Typ', '?')}",
            "",
        ]
        for label, key in (
            ("Notatka", POLE_NOTATKA),
            ("Opis", POLE_OPIS),
            ("Tekst", POLE_TEKST),
            ("Źródło", POLE_ŹRÓDŁO),
        ):
            val = data.get(key)
            if val:
                lines.append(f"{label}:")
                lines.append(str(val))
                lines.append("")
        self._set_detail("\n".join(lines).rstrip())

    def _set_detail(self, text: str) -> None:
        self._detail.configure(state="normal")
        self._detail.delete("1.0", tk.END)
        self._detail.insert("1.0", text)
        self._detail.configure(state="disabled")

    def _select_first(self) -> None:
        if self._list.size():
            self._list.selection_clear(0, tk.END)
            self._list.selection_set(0)
            self._list.see(0)
            self._show_detail()

    def _insert_selected(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if self._on_insert:
            self._on_insert(name)
        else:
            self.clipboard_clear()
            self.clipboard_append(name)
            messagebox.showinfo("Słownik nazw", f"Skopiowano: {name}", parent=self)


class SpellcheckDialog(tk.Toplevel):
    """Nawigacja po błędach pisowni z sugestiami."""

    def __init__(
        self,
        parent: tk.Misc,
        text_widget: tk.Text,
        checker: SpellChecker,
        *,
        on_lore_lookup: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.title("Sprawdź pisownię")
        self.transient(parent.winfo_toplevel())
        self.resizable(True, False)
        self.minsize(400, 220)
        self.geometry("460x280")

        self._text = text_widget
        self._checker = checker
        self._on_lore_lookup = on_lore_lookup
        self._errors: list[WordSpan] = []
        self._idx = 0

        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Słowo:", style="Dim.TLabel").grid(row=0, column=0, sticky="w")
        self._word_var = tk.StringVar()
        ttk.Label(top, textvariable=self._word_var, style="Head.TLabel").grid(row=0, column=1, sticky="w", padx=8)
        ttk.Label(top, text=f"Silnik: {backend_label()}", style="Dim.TLabel").grid(
            row=0, column=2, sticky="e", padx=4
        )
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Sugestie:", style="Dim.TLabel").grid(row=1, column=0, sticky="nw", pady=(8, 0))
        self._sugs = tk.Listbox(top, height=6, exportselection=False)
        style_listbox(self._sugs)
        self._sugs.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=8, pady=(8, 0))
        self._sugs.bind("<Double-Button-1>", lambda _e: self._replace())

        btns = ttk.Frame(self, padding=8)
        btns.pack(fill="x")
        ttk.Button(btns, text="Zamień", command=self._replace).pack(side="left")
        ttk.Button(btns, text="Ignoruj", command=self._ignore).pack(side="left", padx=(4, 0))
        ttk.Button(btns, text="Dodaj do słownika", command=self._add_dict).pack(side="left", padx=(4, 0))
        ttk.Button(btns, text="Dalej", command=self._next).pack(side="left", padx=(4, 0))
        if on_lore_lookup:
            ttk.Button(btns, text="Szukaj w lore…", command=self._lore).pack(side="left", padx=(4, 0))
        ttk.Button(btns, text="Zamknij", command=self._close).pack(side="right")

        self.bind("<Escape>", lambda _e: self._close())
        self.protocol("WM_DELETE_WINDOW", self._close)

        apply_spell_tags(self._text, self._checker)
        self._errors = list(self._checker.unknown_spans(self._text.get("1.0", "end-1c")))
        if not self._errors:
            self._word_var.set("(brak nieznanych słów)")
            self._sugs.insert(tk.END, "—")
            messagebox.showinfo(
                "Pisownia",
                "Nie znaleziono nieznanych słów.\n"
                f"Silnik: {backend_label()}\n"
                "(+ .lore-spelling.json w projekcie)",
                parent=self,
            )
        else:
            self._show_current()

    def _show_current(self) -> None:
        if not self._errors:
            self._word_var.set("(koniec)")
            self._sugs.delete(0, tk.END)
            return
        if self._idx >= len(self._errors):
            self._idx = 0
        span = self._errors[self._idx]
        self._word_var.set(f"{span.word}  ({self._idx + 1}/{len(self._errors)})")
        # Zaznacz w tekście
        a = _index_from_offset(self._text, span.start)
        b = _index_from_offset(self._text, span.end)
        self._text.tag_remove("sel", "1.0", tk.END)
        self._text.tag_add("sel", a, b)
        self._text.mark_set("insert", b)
        self._text.see(a)

        self._sugs.delete(0, tk.END)
        for s in self._checker.suggestions(span.word):
            self._sugs.insert(tk.END, s)
        if self._sugs.size():
            self._sugs.selection_set(0)

    def _current_span(self) -> Optional[WordSpan]:
        if not self._errors or self._idx >= len(self._errors):
            return None
        return self._errors[self._idx]

    def _replace(self) -> None:
        span = self._current_span()
        if not span:
            return
        sel = self._sugs.curselection()
        if not sel:
            return
        repl = self._sugs.get(sel[0])
        a = _index_from_offset(self._text, span.start)
        b = _index_from_offset(self._text, span.end)
        self._text.delete(a, b)
        self._text.insert(a, repl)
        self._recompute_from_here()

    def _ignore(self) -> None:
        span = self._current_span()
        if span:
            self._checker.ignore_session(span.word)
        self._next()

    def _add_dict(self) -> None:
        span = self._current_span()
        if not span:
            return
        self._checker.add_to_project(span.word)
        self._recompute_from_here()

    def _lore(self) -> None:
        span = self._current_span()
        if span and self._on_lore_lookup:
            self._on_lore_lookup(span.word)

    def _next(self) -> None:
        if not self._errors:
            return
        self._idx += 1
        if self._idx >= len(self._errors):
            apply_spell_tags(self._text, self._checker)
            self._errors = list(self._checker.unknown_spans(self._text.get("1.0", "end-1c")))
            self._idx = 0
            if not self._errors:
                self._word_var.set("(koniec — brak dalszych)")
                self._sugs.delete(0, tk.END)
                apply_spell_tags(self._text, self._checker)
                return
        self._show_current()

    def _recompute_from_here(self) -> None:
        apply_spell_tags(self._text, self._checker)
        content = self._text.get("1.0", "end-1c")
        self._errors = list(self._checker.unknown_spans(content))
        if self._idx >= len(self._errors):
            self._idx = max(0, len(self._errors) - 1)
        if not self._errors:
            self._word_var.set("(koniec — brak dalszych)")
            self._sugs.delete(0, tk.END)
            return
        self._show_current()

    def _close(self) -> None:
        apply_spell_tags(self._text, self._checker)
        self.destroy()


def apply_spell_tags(text: tk.Text, checker: SpellChecker) -> None:
    """Podkreśl nieznane słowa w widgetcie Text."""
    text.tag_configure(TAG_SPELL, underline=True, foreground="#f48771")
    text.tag_remove(TAG_SPELL, "1.0", tk.END)
    content = text.get("1.0", "end-1c")
    for span in checker.unknown_spans(content):
        a = _index_from_offset(text, span.start)
        b = _index_from_offset(text, span.end)
        text.tag_add(TAG_SPELL, a, b)


def clear_spell_tags(text: tk.Text) -> None:
    try:
        text.tag_remove(TAG_SPELL, "1.0", tk.END)
    except tk.TclError:
        pass


def open_name_dictionary(
    parent: tk.Misc,
    lore: LoreStore,
    text_widget: Optional[tk.Text] = None,
) -> NameDictionaryDialog:
    initial = ""
    if text_widget is not None:
        initial = _selection_or_word(text_widget)

    on_insert = None
    if text_widget is not None:
        on_insert = lambda name: _insert_at_cursor(text_widget, name)

    return NameDictionaryDialog(
        parent,
        lore,
        initial_query=initial,
        on_insert=on_insert,
    )


def open_spellcheck(
    parent: tk.Misc,
    text_widget: tk.Text,
    lore: LoreStore,
    *,
    project_root,
) -> SpellcheckDialog:
    try:
        names = lore.wszystkie_wpisy()
    except Exception:
        names = []
    checker = SpellChecker(project_root=project_root, lore_names=names)

    def _lore_lookup(word: str) -> None:
        NameDictionaryDialog(
            parent,
            lore,
            initial_query=word,
            on_insert=lambda name: _insert_at_cursor(text_widget, name),
        )

    return SpellcheckDialog(
        parent,
        text_widget,
        checker,
        on_lore_lookup=_lore_lookup,
    )


def _insert_at_cursor(text_widget: tk.Text, name: str) -> None:
    try:
        text_widget.delete("sel.first", "sel.last")
    except tk.TclError:
        pass
    text_widget.insert("insert", name)
    text_widget.focus_set()
