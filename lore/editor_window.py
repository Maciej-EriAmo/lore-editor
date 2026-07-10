"""Okno edytora tekstu — karty, menu, skróty klawiszowe."""

from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from lore.document_hooks import on_file_opened, on_file_saved
from lore.panel import LorePanel
from lore.store import LoreStore
from lore.text_io import read_text_smart, write_text
from lore.theme import apply_theme, style_text
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
            self._status_var.set(f"{path_lbl} · {words} słów · {chars} znaków · {enc}{dirty}")
        else:
            self._status_var.set(f"Bez tytułu · {words} słów · {chars} znaków{(' · niezapisane' if tab.dirty else '')}")

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=(8, 6))
        top.pack(fill="x")
        ttk.Label(top, text="Lore Editor", style="Head.TLabel").pack(side="left")
        ttk.Label(top, text=f"  ·  {self._proj}", style="Dim.TLabel").pack(side="left")

        toolbar = ttk.Frame(top)
        toolbar.pack(side="right")
        ttk.Button(toolbar, text="Nowy", command=self._new_tab).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Otwórz…", command=self._open_dialog).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Zapisz", command=self._save).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Zapisz jako…", command=self._save_as).pack(side="left", padx=2)
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
        ttk.Label(status, text=str(self._proj_root), style="Dim.TLabel").pack(side="right")

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
        edit_m.add_command(label="Zawijaj wiersze", command=self._toggle_wrap)

        lore_m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Lore", menu=lore_m)
        lore_m.add_command(label="Odśwież panel", command=self._panel.odswiez)
        lore_m.add_command(label="Zapisz projekt lore", command=self._save_lore)

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

    def _bind_shortcuts(self) -> None:
        self.root.bind_all("<Control-n>", lambda e: self._new_tab())
        self.root.bind_all("<Control-o>", lambda e: self._open_dialog())
        self.root.bind_all("<Control-s>", lambda e: self._save())
        self.root.bind_all("<Control-Shift-S>", lambda e: self._save_as())
        self.root.bind_all("<Control-w>", lambda e: self._close_current_tab())
        self.root.bind_all("<Control-f>", lambda e: self._show_find())

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

        try:
            write_text(tab.path, tab.text.get("1.0", tk.END), tab.encoding)
        except OSError as e:
            messagebox.showerror("Błąd zapisu", str(e), parent=self.root)
            return False

        tab.dirty = False
        tab_id = self._tab_id_for(tab)
        if tab_id:
            self._update_tab_title(tab_id)
        self._update_window_title()
        self._update_status()
        on_file_saved(self._lore, tab.path, self._panel)
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
            self._lore.zapisz()
            self._panel.odswiez()
            self._status_var.set("Projekt lore zapisany")
        except Exception as e:
            messagebox.showerror("Błąd", str(e), parent=self.root)

    def _schedule_autosave(self) -> None:
        def _tick():
            for tab_id, tab in list(self._tabs.items()):
                if tab.dirty and tab.path:
                    try:
                        write_text(tab.path, tab.text.get("1.0", tk.END), tab.encoding)
                        tab.dirty = False
                        self._update_tab_title(tab_id)
                        on_file_saved(self._lore, tab.path, self._panel)
                    except OSError:
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
        try:
            self._lore.zapisz()
            self._lore.close()
        except Exception:
            pass
        self.root.destroy()


def run_editor_window(
    lore: LoreStore,
    *,
    initial_files: Optional[list[str]] = None,
) -> None:
    EditorWindow(lore, initial_files=initial_files).run()