"""Okno edytora tekstu — karty, menu, skróty klawiszowe."""

from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from lore.dictionary_view import open_name_dictionary, open_spellcheck
from lore.document_hooks import on_file_opened, on_file_saved
from lore.panel import LorePanel
from lore.paths import default_work_dir, save_last_work_dir
from lore.store import LoreStore
from lore.text_io import read_text_smart, write_text_atomic
from lore.theme import apply_theme, style_text
from lore.export_docx import DocxExportError, export_available, export_manuscript_docx
from lore.help_view import open_help
from lore.history_view import open_history_window
from lore.manuscript import paginate, profile_for_preset
from lore.print_preview import open_print_preview
from lore.typography import (
    apply_typography,
    load_typography_settings,
    list_presets_by_category,
    refresh_body_tag,
    save_typography_settings,
    settings_summary,
    TypographySettings,
)

_AUTOSAVE_MS = 60_000


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


@dataclass
class _TabState:
    text: scrolledtext.ScrolledText = field(repr=False)
    frame: ttk.Frame = field(repr=False)
    path: str = ""
    encoding: str = "utf-8"
    dirty: bool = False


class EditorWindow:
    """Standalone edytor rozdziałów z panelem lore."""

    def __init__(
        self,
        lore: LoreStore,
        *,
        initial_files: Optional[list[str]] = None,
    ) -> None:
        self._lore = lore
        self._proj = lore.nazwa_projektu()
        self._proj_root = lore.katalog_projektu()
        self._tabs: dict[str, _TabState] = {}
        self._find_dialog: Optional[tk.Toplevel] = None
        self._typography = load_typography_settings()

        self.root = tk.Tk()
        preset, size, spacing = self._typography.resolved()
        self._font_family_var = tk.StringVar(master=self.root, value=self._typography.preset_id)
        self._font_size_var = tk.IntVar(master=self.root, value=size)
        self._line_spacing_var = tk.DoubleVar(master=self.root, value=spacing)
        self.root.title(f"Lore Editor — {self._proj}")
        self.root.geometry("1150x720")
        self.root.minsize(900, 560)
        apply_theme(self.root)

        self._status_var = tk.StringVar(value="Gotowy")
        self._proj_label_var = tk.StringVar(value=f"  ·  {self._proj}")
        self._path_status_var = tk.StringVar(value=str(self._proj_root))
        self._build_ui()
        self._build_menu()
        self._bind_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_autosave()

        files = [f for f in (initial_files or []) if f and Path(f).is_file()]
        if files:
            for path in files:
                self._open_path(path)
        else:
            self._new_tab()

    def run(self) -> None:
        self.root.mainloop()

    def _current_tab(self) -> Optional[_TabState]:
        try:
            tab_id = self._notebook.select()
            if not tab_id:
                return None
            return self._tabs.get(tab_id)
        except tk.TclError:
            return None

    def _current_file(self) -> str:
        tab = self._current_tab()
        return tab.path if tab else ""

    def _tab_display_name(self, tab: _TabState) -> str:
        if tab.path:
            try:
                name = Path(tab.path).resolve().relative_to(self._proj_root)
                label = str(name)
            except ValueError:
                label = Path(tab.path).name
        else:
            label = "Bez tytułu"
        return f"{label}*" if tab.dirty else label

    def _tab_label(self, tab: _TabState) -> str:
        return f"{self._tab_display_name(tab)}  ×"

    def _update_tab_title(self, tab_id: str) -> None:
        tab = self._tabs.get(tab_id)
        if tab is None:
            return
        self._notebook.tab(tab_id, text=self._tab_label(tab))

    def _update_window_title(self) -> None:
        tab = self._current_tab()
        base = f"Lore Editor — {self._proj}"
        if tab and tab.path:
            name = Path(tab.path).name
            base += f" — {name}"
            if tab.dirty:
                base += " *"
        elif tab and tab.dirty:
            base += " — *"
        self.root.title(base)

    def _update_status(self) -> None:
        tab = self._current_tab()
        if tab is None:
            self._status_var.set("Gotowy")
            return
        content = tab.text.get("1.0", "end-1c")
        words = _word_count(content)
        chars = len(content)
        enc = tab.encoding
        if tab.path:
            try:
                rel = Path(tab.path).resolve().relative_to(self._proj_root)
                path_lbl = str(rel)
            except ValueError:
                path_lbl = Path(tab.path).name
            dirty = " · niezapisane" if tab.dirty else ""
            ms = paginate(content, profile_for_preset(self._typography.preset_id))
            self._status_var.set(
                f"{path_lbl} · {words} słów · {ms.summary()} · {enc}{dirty}"
            )
        else:
            ms = paginate(content, profile_for_preset(self._typography.preset_id))
            self._status_var.set(
                f"Bez tytułu · {words} słów · {ms.summary()}"
                f"{(' · niezapisane' if tab.dirty else '')}"
            )

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=(8, 6))
        top.pack(fill="x")
        ttk.Label(top, text="Lore Editor", style="Head.TLabel").pack(side="left")
        ttk.Label(top, textvariable=self._proj_label_var, style="Dim.TLabel").pack(side="left")

        toolbar = ttk.Frame(top)
        toolbar.pack(side="right")
        ttk.Button(toolbar, text="Nowy", command=self._new_tab).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Otwórz…", command=self._open_dialog).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Zapisz", command=self._save).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Zapisz jako…", command=self._save_as).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Katalog…", command=self._choose_project_dir).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Zamknij kartę", command=self._close_current_tab).pack(side="left", padx=2)

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        left = ttk.Frame(paned)
        paned.add(left, weight=3)

        self._notebook = ttk.Notebook(left)
        self._notebook.pack(fill="both", expand=True)
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._notebook.bind("<Button-1>", self._on_tab_click, add="+")
        self._notebook.bind("<Button-2>", self._on_tab_middle_click, add="+")

        self._panel = LorePanel(paned, self._lore, get_current_file=self._current_file)
        paned.add(self._panel, weight=1)

        status = ttk.Frame(self.root, padding=(8, 4))
        status.pack(fill="x", side="bottom")
        ttk.Label(status, textvariable=self._status_var, style="Dim.TLabel").pack(side="left")
        path_lbl = ttk.Label(status, textvariable=self._path_status_var, style="Dim.TLabel", cursor="hand2")
        path_lbl.pack(side="right")
        path_lbl.bind("<Button-1>", lambda _e: self._choose_project_dir())

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)

        file_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plik", menu=file_m)
        file_m.add_command(label="Nowy", accelerator="Ctrl+N", command=self._new_tab)
        file_m.add_command(label="Otwórz…", accelerator="Ctrl+O", command=self._open_dialog)
        file_m.add_separator()
        file_m.add_command(label="Zapisz", accelerator="Ctrl+S", command=self._save)
        file_m.add_command(label="Zapisz jako…", accelerator="Ctrl+Shift+S", command=self._save_as)
        file_m.add_separator()
        file_m.add_command(
            label="Katalog projektu…",
            accelerator="Ctrl+Shift+O",
            command=self._choose_project_dir,
        )
        file_m.add_command(
            label="Domyślny katalog (dokumenty/lore)",
            command=self._use_default_project_dir,
        )
        file_m.add_separator()
        file_m.add_command(label="Zamknij kartę", accelerator="Ctrl+W", command=self._close_current_tab)
        file_m.add_command(label="Zapisz projekt lore", command=self._save_lore)
        file_m.add_separator()
        file_m.add_command(label="Zakończ", command=self._on_close)

        edit_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edycja", menu=edit_m)
        edit_m.add_command(label="Cofnij", accelerator="Ctrl+Z", command=self._undo)
        edit_m.add_command(label="Ponów", accelerator="Ctrl+Y", command=self._redo)
        edit_m.add_separator()
        edit_m.add_command(label="Znajdź…", accelerator="Ctrl+F", command=self._show_find)
        edit_m.add_command(
            label="Słownik nazw…",
            accelerator="Ctrl+Shift+D",
            command=self._show_name_dictionary,
        )
        edit_m.add_command(
            label="Sprawdź pisownię…",
            accelerator="F7",
            command=self._show_spellcheck,
        )
        edit_m.add_separator()
        edit_m.add_command(label="Zawijaj wiersze", command=self._toggle_wrap)

        lore_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Lore", menu=lore_m)
        lore_m.add_command(label="Odśwież panel", command=self._panel.odswiez)
        lore_m.add_command(label="Zapisz projekt lore", command=self._save_lore)
        lore_m.add_separator()
        lore_m.add_command(label="Utwórz punkt przywracania…", command=self._create_snapshot)
        lore_m.add_command(label="Historia zmian…", command=self._show_history)

        view_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Wygląd", menu=view_m)
        for _cat_id, cat_label, items in list_presets_by_category():
            sub = tk.Menu(view_m, tearoff=0)
            view_m.add_cascade(label=cat_label, menu=sub)
            for preset in items:
                sub.add_radiobutton(
                    label=preset.menu_label(),
                    variable=self._font_family_var,
                    value=preset.id,
                    command=self._on_typography_preset,
                )
        view_m.add_separator()
        size_m = tk.Menu(view_m, tearoff=0)
        view_m.add_cascade(label="Rozmiar czcionki", menu=size_m)
        for pt in (11, 12):
            size_m.add_radiobutton(
                label=f"{pt} pt",
                variable=self._font_size_var,
                value=pt,
                command=self._on_typography_size,
            )
        spacing_m = tk.Menu(view_m, tearoff=0)
        view_m.add_cascade(label="Interlinia", menu=spacing_m)
        for sp, label in ((1.0, "1,0 — druk / gotowy tekst"), (1.5, "1,5 — szkic roboczy")):
            spacing_m.add_radiobutton(
                label=label,
                variable=self._line_spacing_var,
                value=sp,
                command=self._on_typography_spacing,
            )

        print_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Wydruk", menu=print_m)
        prev_m = tk.Menu(print_m, tearoff=0)
        print_m.add_cascade(label="Podgląd stron", menu=prev_m)
        prev_m.add_command(
            label="Scenariusz (Courier, 1 str. ≈ 1 min)",
            command=lambda: self._show_print_preview("screenplay"),
        )
        prev_m.add_command(
            label="Rękopis do wysyłki (TNR, interlinia 2,0)",
            command=lambda: self._show_print_preview("submission"),
        )
        prev_m.add_command(
            label="Gotowy do druku (TNR, interlinia 1,0)",
            command=lambda: self._show_print_preview("print_ready"),
        )
        print_m.add_separator()
        exp_m = tk.Menu(print_m, tearoff=0)
        print_m.add_cascade(label="Eksportuj DOCX…", menu=exp_m)
        exp_m.add_command(
            label="Rękopis do wydawnictwa (TNR 12, margines 2,5 cm)",
            command=lambda: self._export_docx("submission"),
        )
        exp_m.add_command(
            label="Scenariusz (Courier 12)",
            command=lambda: self._export_docx("screenplay"),
        )
        exp_m.add_command(
            label="Gotowy do druku (TNR 12, interlinia 1,0)",
            command=lambda: self._export_docx("print_ready"),
        )

        help_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pomoc", menu=help_m)
        help_m.add_command(
            label="Przewodnik pisarza",
            accelerator="F1",
            command=lambda: open_help(self.root, "Przewodnik pisarza"),
        )
        help_m.add_command(
            label="Skróty klawiszowe",
            command=lambda: open_help(self.root, "Skróty klawiszowe"),
        )
        help_m.add_command(
            label="Czcionki i wygląd",
            command=lambda: open_help(self.root, "Czcionki i wygląd"),
        )
        help_m.add_command(
            label="Wydruk i eksport",
            command=lambda: open_help(self.root, "Wydruk i eksport"),
        )
        help_m.add_command(
            label="Panel Lore",
            command=lambda: open_help(self.root, "Panel Lore"),
        )
        help_m.add_command(
            label="Słownik i pisownia",
            command=lambda: open_help(self.root, "Słownik i pisownia"),
        )
        help_m.add_command(
            label="Kontekst czasowy",
            command=lambda: open_help(self.root, "Kontekst czasowy"),
        )
        help_m.add_command(
            label="Zapytania semantyczne",
            command=lambda: open_help(self.root, "Zapytania semantyczne"),
        )
        help_m.add_command(
            label="Historia zmian",
            command=lambda: open_help(self.root, "Historia zmian"),
        )
        help_m.add_command(
            label="Pliki i Lore Pack",
            command=lambda: open_help(self.root, "Pliki i Lore Pack"),
        )
        help_m.add_command(
            label="Sieć: Karmazyn i Cynober DB",
            command=lambda: open_help(self.root, "Sieć: Karmazyn i Cynober DB"),
        )
        help_m.add_separator()
        help_m.add_command(
            label="O programie",
            command=lambda: open_help(self.root, "O programie"),
        )

    def _bind_shortcuts(self) -> None:
        self.root.bind_all("<Control-n>", lambda e: self._new_tab())
        self.root.bind_all("<Control-o>", lambda e: self._open_dialog())
        self.root.bind_all("<Control-s>", lambda e: self._save())
        self.root.bind_all("<Control-Shift-S>", lambda e: self._save_as())
        self.root.bind_all("<Control-w>", lambda e: self._close_current_tab())
        self.root.bind_all("<Control-f>", lambda e: self._show_find())
        self.root.bind_all("<Control-Shift-D>", lambda e: self._show_name_dictionary())
        self.root.bind_all("<Control-Shift-O>", lambda e: self._choose_project_dir())
        self.root.bind_all("<F7>", lambda e: self._show_spellcheck())
        self.root.bind_all("<F1>", lambda e: open_help(self.root, "Przewodnik pisarza"))

    def _create_tab(self, content: str = "", path: str = "", encoding: str = "utf-8") -> str:
        frame = ttk.Frame(self._notebook)
        text = scrolledtext.ScrolledText(frame, wrap="word", undo=True)
        style_text(text, height=24, mono=False)
        self._apply_typography_to_widget(text)
        text.pack(fill="both", expand=True)
        if content:
            text.insert("1.0", content)

        self._notebook.add(frame, text="Bez tytułu")
        tab_id = str(frame)
        state = _TabState(text=text, frame=frame, path=path, encoding=encoding)
        self._tabs[tab_id] = state

        def _on_modify(_event=None):
            if not text.edit_modified():
                return
            text.edit_modified(False)
            if not state.dirty:
                state.dirty = True
                self._update_tab_title(tab_id)
                self._update_window_title()
            refresh_body_tag(text)
            self._update_status()

        text.bind("<<Modified>>", _on_modify)
        self._notebook.select(tab_id)
        self._update_tab_title(tab_id)
        self._update_window_title()
        self._update_status()
        return tab_id

    def _new_tab(self) -> None:
        self._create_tab()

    def _on_tab_changed(self, _event=None) -> None:
        tab = self._current_tab()
        self._update_window_title()
        self._update_status()
        if tab and tab.path:
            on_file_opened(self._lore, tab.path, self._panel)

    def _open_dialog(self) -> None:
        paths = filedialog.askopenfilenames(
            parent=self.root,
            initialdir=str(self._proj_root),
            filetypes=[("Tekst", "*.txt *.md"), ("Markdown", "*.md"), ("Wszystkie", "*.*")],
        )
        for path in paths:
            if path:
                self._open_path(path)

    def _open_path(self, path: str) -> None:
        for tab_id, state in self._tabs.items():
            if state.path and Path(state.path).resolve() == Path(path).resolve():
                self._notebook.select(tab_id)
                return

        try:
            content, enc = read_text_smart(path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Błąd otwarcia", str(e), parent=self.root)
            return

        tab_id = self._create_tab(content, path=path, encoding=enc)
        on_file_opened(self._lore, path, self._panel)
        self._update_tab_title(tab_id)

    def _save_tab(self, tab: _TabState, *, save_as: bool = False) -> bool:
        path = tab.path
        if not path or save_as:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                initialdir=str(self._proj_root),
                initialfile=Path(path).name if path else "rozdzial.txt",
                defaultextension=".txt",
                filetypes=[("Tekst", "*.txt *.md"), ("Markdown", "*.md")],
            )
            if not path:
                return False
            tab.path = path

        content = tab.text.get("1.0", tk.END)
        try:
            on_file_saved(
                self._lore,
                tab.path,
                self._panel,
                content=content,
                encoding=tab.encoding,
            )
        except OSError as e:
            messagebox.showerror("Błąd zapisu", str(e), parent=self.root)
            return False
        except Exception as e:
            messagebox.showerror(
                "Zapis",
                f"Tekst zapisany, ale lore nie: {e}\nSpróbuj „Zapisz projekt lore”.",
                parent=self.root,
            )

        tab.dirty = False
        tab_id = self._tab_id_for(tab)
        if tab_id:
            self._update_tab_title(tab_id)
        self._update_window_title()
        self._update_status()
        return True

    def _tab_id_for(self, tab: _TabState) -> Optional[str]:
        for tab_id, state in self._tabs.items():
            if state is tab:
                return tab_id
        return None

    def _save(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        self._save_tab(tab)

    def _save_as(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        self._save_tab(tab, save_as=True)

    def _undo(self) -> None:
        tab = self._current_tab()
        if tab:
            try:
                tab.text.edit_undo()
            except tk.TclError:
                pass

    def _redo(self) -> None:
        tab = self._current_tab()
        if tab:
            try:
                tab.text.edit_redo()
            except tk.TclError:
                pass

    def _sync_typography_from_vars(self) -> TypographySettings:
        self._typography = TypographySettings(
            preset_id=self._font_family_var.get(),
            size=int(self._font_size_var.get()),
            line_spacing=float(self._line_spacing_var.get()),
        )
        return self._typography

    def _apply_typography_to_widget(self, text: scrolledtext.ScrolledText) -> str:
        return apply_typography(text, self._typography)

    def _apply_typography_all(self) -> str:
        family = ""
        for state in self._tabs.values():
            family = self._apply_typography_to_widget(state.text)
        return family

    def _persist_typography(self, family: str = "") -> None:
        save_typography_settings(self._typography)
        if not family:
            tab = self._current_tab()
            if tab:
                family = tab.text.cget("font").split()[0] if tab.text.cget("font") else ""
        self._status_var.set("Wygląd: " + settings_summary(self._typography, family=family))

    def _on_typography_preset(self) -> None:
        from lore.typography import get_preset

        preset = get_preset(self._font_family_var.get())
        if preset:
            self._font_size_var.set(preset.size)
            self._line_spacing_var.set(preset.line_spacing)
        self._sync_typography_from_vars()
        family = self._apply_typography_all()
        self._persist_typography(family)

    def _on_typography_size(self) -> None:
        self._sync_typography_from_vars()
        family = self._apply_typography_all()
        self._persist_typography(family)

    def _on_typography_spacing(self) -> None:
        self._sync_typography_from_vars()
        family = self._apply_typography_all()
        self._persist_typography(family)

    def _current_text_content(self) -> str:
        tab = self._current_tab()
        return tab.text.get("1.0", "end-1c") if tab else ""

    def _show_print_preview(self, profile_id: str) -> None:
        tab = self._current_tab()
        if tab is None:
            messagebox.showinfo("Wydruk", "Otwórz kartę z tekstem.", parent=self.root)
            return
        title = "Podgląd — scenariusz" if profile_id == "screenplay" else "Podgląd druku"
        open_print_preview(self.root, self._current_text_content(), profile_id=profile_id, title=title)

    def _export_docx(self, profile_id: str) -> None:
        tab = self._current_tab()
        if tab is None:
            messagebox.showinfo("Eksport", "Otwórz kartę z tekstem.", parent=self.root)
            return
        if not export_available():
            messagebox.showerror(
                "Eksport DOCX",
                "Zainstaluj pakiet: pip install python-docx",
                parent=self.root,
            )
            return
        default = Path(tab.path).stem if tab.path else "rozdzial"
        path = filedialog.asksaveasfilename(
            parent=self.root,
            initialdir=str(self._proj_root),
            initialfile=f"{default}_rekopis.docx",
            defaultextension=".docx",
            filetypes=[("Word", "*.docx")],
        )
        if not path:
            return
        try:
            export_manuscript_docx(
                self._current_text_content(),
                path,
                profile_id=profile_id,
                title=Path(tab.path).stem if tab.path else "",
            )
            messagebox.showinfo("Eksport DOCX", f"Zapisano:\n{path}", parent=self.root)
        except (DocxExportError, OSError) as e:
            messagebox.showerror("Eksport DOCX", str(e), parent=self.root)

    def _toggle_wrap(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return
        current = tab.text.cget("wrap")
        tab.text.configure(wrap="none" if current == "word" else "word")
        self._status_var.set("Zawijanie wierszy: " + ("włączone" if tab.text.cget("wrap") == "word" else "wyłączone"))

    def _show_find(self) -> None:
        tab = self._current_tab()
        if tab is None:
            return

        if self._find_dialog is not None and self._find_dialog.winfo_exists():
            self._find_dialog.lift()
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Znajdź")
        dlg.transient(self.root)
        dlg.resizable(False, False)
        self._find_dialog = dlg

        ttk.Label(dlg, text="Szukaj:", padding=8).grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(dlg, width=36)
        entry.grid(row=0, column=1, padx=8, pady=8)
        try:
            entry.insert(0, tab.text.get("sel.first", "sel.last"))
        except tk.TclError:
            pass
        entry.focus_set()

        def _find_next():
            query = entry.get()
            if not query:
                return
            start = tab.text.index("insert")
            pos = tab.text.search(query, start, stopindex=tk.END)
            if not pos:
                pos = tab.text.search(query, "1.0", stopindex=tk.END)
            if pos:
                end = f"{pos}+{len(query)}c"
                tab.text.tag_remove("find_hit", "1.0", tk.END)
                tab.text.tag_add("find_hit", pos, end)
                tab.text.tag_configure("find_hit", background="#264f78")
                tab.text.mark_set("insert", end)
                tab.text.see(pos)
            else:
                messagebox.showinfo("Znajdź", "Nie znaleziono.", parent=dlg)

        ttk.Button(dlg, text="Dalej", command=_find_next).grid(row=1, column=1, sticky="e", padx=8, pady=(0, 8))
        entry.bind("<Return>", lambda e: _find_next())
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

    def _show_name_dictionary(self) -> None:
        tab = self._current_tab()
        text = tab.text if tab else None
        open_name_dictionary(self.root, self._lore, text)

    def _show_spellcheck(self) -> None:
        tab = self._current_tab()
        if tab is None:
            messagebox.showinfo("Pisownia", "Otwórz kartę z tekstem.", parent=self.root)
            return
        open_spellcheck(
            self.root,
            tab.text,
            self._lore,
            project_root=self._proj_root,
        )

    def _confirm_save_tab(self, tab: _TabState) -> bool:
        answer = messagebox.askyesnocancel(
            "Niezapisane zmiany",
            f"Zapisać zmiany w „{self._tab_display_name(tab).rstrip('*')}”?",
            parent=self.root,
        )
        if answer is None:
            return False
        if answer and not self._save_tab(tab):
            return False
        return True

    def _tab_id_at(self, event: tk.Event) -> Optional[str]:
        try:
            clicked = self._notebook.tk.call(self._notebook._w, "identify", "tab", event.x, event.y)
        except tk.TclError:
            return None
        if clicked in ("", None):
            return None
        tabs = self._notebook.tabs()
        try:
            return tabs[int(clicked)]
        except (ValueError, IndexError, tk.TclError):
            return clicked if clicked in tabs else None

    def _on_tab_click(self, event: tk.Event) -> Optional[str]:
        tab_id = self._tab_id_at(event)
        if not tab_id:
            return None
        bbox = self._notebook.bbox(tab_id)
        if not bbox:
            return None
        x, _y, width, _h = bbox
        if event.x > x + width - 22:
            self._close_tab_by_id(tab_id)
            return "break"
        return None

    def _on_tab_middle_click(self, event: tk.Event) -> str:
        tab_id = self._tab_id_at(event)
        if tab_id:
            self._close_tab_by_id(tab_id)
        return "break"

    def _close_tab_by_id(self, tab_id: str) -> bool:
        tab = self._tabs.get(tab_id)
        if tab is None:
            return True
        if tab.dirty:
            self._notebook.select(tab_id)
            if not self._confirm_save_tab(tab):
                return False
        self._notebook.forget(tab_id)
        tab.frame.destroy()
        del self._tabs[tab_id]
        if not self._tabs:
            self._new_tab()
        else:
            self._update_window_title()
            self._update_status()
        return True

    def _close_current_tab(self) -> None:
        tab_id = self._notebook.select()
        if tab_id:
            self._close_tab_by_id(tab_id)

    def _save_lore(self) -> None:
        try:
            self._lore.zapisz(historia_auto=False)
            self._panel.odswiez()
            self._status_var.set("Projekt lore zapisany")
        except Exception as e:
            messagebox.showerror("Błąd", str(e), parent=self.root)

    def _choose_project_dir(self) -> None:
        """Plik → Katalog projektu… — wybór folderu powieści z GUI."""
        kwargs = dict(
            parent=self.root,
            title="Katalog projektu (powieść)",
            initialdir=str(self._proj_root),
        )
        try:
            chosen = filedialog.askdirectory(**kwargs, mustexist=False)
        except TypeError:
            chosen = filedialog.askdirectory(**kwargs)
        if not chosen:
            return
        self._switch_project_dir(Path(chosen))

    def _use_default_project_dir(self) -> None:
        """Przełącz na domyślny ../dokumenty/lore."""
        target = default_work_dir()
        if not messagebox.askyesno(
            "Domyślny katalog",
            f"Ustawić katalog projektu na:\n{target} ?",
            parent=self.root,
        ):
            return
        self._switch_project_dir(target)

    def _switch_project_dir(self, new_root: Path) -> None:
        """Zamknij bieżący projekt i otwórz inny katalog (tryb lokalny)."""
        new_root = Path(new_root).expanduser().resolve()
        if new_root == self._proj_root.resolve():
            self._status_var.set(f"Katalog bez zmian: {new_root}")
            return

        if not self._lore.tryb_lokalny():
            messagebox.showinfo(
                "Katalog projektu",
                "W trybie sieciowym (--rpc) zmień katalog przy starcie:\n"
                f"  lore-editor --rpc --project-dir \"{new_root}\"\n\n"
                "Albo zamknij edytor i uruchom lokalnie.",
                parent=self.root,
            )
            return

        # Zapisz karty
        for tab_id in list(self._tabs.keys()):
            tab = self._tabs[tab_id]
            if tab.dirty:
                self._notebook.select(tab_id)
                if not self._confirm_save_tab(tab):
                    return

        zapisz_lore = True
        if self._lore.lore_niezapisane():
            ans = messagebox.askyesnocancel(
                "Niezapisane lore",
                "Zapisać graf lore przed zmianą katalogu?",
                parent=self.root,
            )
            if ans is None:
                return
            zapisz_lore = bool(ans)

        old = self._lore
        try:
            old.close(zapisz_lore=zapisz_lore)
        except Exception as e:
            if not messagebox.askyesno(
                "Katalog projektu",
                f"Nie udało się domknąć poprzedniego projektu:\n{e}\n\nKontynuować?",
                parent=self.root,
            ):
                return

        try:
            new_root.mkdir(parents=True, exist_ok=True)
            new_lore = LoreStore.open_local(project_dir=new_root)
        except Exception as e:
            messagebox.showerror(
                "Katalog projektu",
                f"Nie otwarto „{new_root}”:\n{e}",
                parent=self.root,
            )
            # próba powrotu — najlepiej nie zostawiać bez store; otwórz stary root
            try:
                self._lore = LoreStore.open_local(project_dir=self._proj_root)
                self._panel.set_lore(self._lore)
            except Exception:
                pass
            return

        self._lore = new_lore
        self._proj = new_lore.nazwa_projektu()
        self._proj_root = new_lore.katalog_projektu()
        save_last_work_dir(self._proj_root)
        try:
            import os

            os.chdir(self._proj_root)
        except OSError:
            pass

        self._proj_label_var.set(f"  ·  {self._proj}")
        self._path_status_var.set(str(self._proj_root))
        self._panel.set_lore(self._lore)

        # Wyczyść karty (tekst starego projektu) — bez ponownego potwierdzenia (już zapisane)
        for tab_id in list(self._tabs.keys()):
            tab = self._tabs[tab_id]
            self._notebook.forget(tab_id)
            tab.frame.destroy()
            del self._tabs[tab_id]
        self._new_tab()
        self._update_window_title()
        self._update_status()
        self._status_var.set(f"Katalog projektu: {self._proj_root}")
        messagebox.showinfo(
            "Katalog projektu",
            f"Otwarto projekt „{self._proj}”\n{self._proj_root}",
            parent=self.root,
        )

    def _create_snapshot(self) -> None:
        from tkinter import simpledialog

        opis = simpledialog.askstring(
            "Punkt przywracania",
            "Opis (opcjonalnie):",
            parent=self.root,
        )
        if opis is None:
            return
        try:
            info = self._lore.utworz_snapshot(opis)
            if info:
                self._status_var.set(f"Snapshot: {info.label}")
            else:
                messagebox.showinfo("Historia", "Brak zmian od ostatniego snapshotu.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Historia", str(e), parent=self.root)

    def _show_history(self) -> None:
        open_history_window(self.root, self._lore, on_restored=self._odswiez_z_dysku)

    def _odswiez_z_dysku(self) -> None:
        """Po przywróceniu snapshotu — przeładuj otwarte karty z plików."""
        for tab_id, tab in list(self._tabs.items()):
            if not tab.path or not Path(tab.path).is_file():
                continue
            try:
                content, enc = read_text_smart(tab.path)
            except (OSError, ValueError):
                continue
            tab.text.delete("1.0", tk.END)
            tab.text.insert("1.0", content)
            tab.encoding = enc
            tab.dirty = False
            self._update_tab_title(tab_id)
        self._panel.odswiez()
        self._update_window_title()
        self._update_status()

    def _schedule_autosave(self) -> None:
        def _tick():
            for tab_id, tab in list(self._tabs.items()):
                if tab.dirty and tab.path:
                    try:
                        on_file_saved(
                            self._lore,
                            tab.path,
                            self._panel,
                            content=tab.text.get("1.0", tk.END),
                            encoding=tab.encoding,
                        )
                        tab.dirty = False
                        self._update_tab_title(tab_id)
                    except (OSError, Exception):
                        pass
            self._update_window_title()
            self._update_status()
            self.root.after(_AUTOSAVE_MS, _tick)

        self.root.after(_AUTOSAVE_MS, _tick)

    def _on_close(self) -> None:
        for tab_id in list(self._tabs.keys()):
            tab = self._tabs[tab_id]
            if tab.dirty:
                self._notebook.select(tab_id)
                if not self._confirm_save_tab(tab):
                    return
        zapisz_lore = True
        if self._lore.lore_niezapisane():
            zapisz_lore = messagebox.askyesno(
                "Niezapisane lore",
                "Graf lore ma niezapisane zmiany. Zapisać przed zamknięciem?",
                parent=self.root,
            )
            if not zapisz_lore and not messagebox.askokcancel(
                "Zamknij bez zapisu lore",
                "Zamknąć bez zapisu zmian w grafie lore?",
                parent=self.root,
            ):
                return
        try:
            self._lore.close(zapisz_lore=zapisz_lore)
        except Exception:
            pass
        self.root.destroy()


def run_editor_window(
    lore: LoreStore,
    *,
    initial_files: Optional[list[str]] = None,
) -> None:
    EditorWindow(lore, initial_files=initial_files).run()