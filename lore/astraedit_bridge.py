"""
Most do AstraEdit — dołącza panel Lore bez znajomości bazy danych.
Nie przenosi paned_window — edytor + karty + konsola zostają nienaruszone.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lore.store import LoreStore

LORE_PANEL_WIDTH = 300


def _editor_shell(gui_app):
    if hasattr(gui_app, "paned_window"):
        return gui_app.paned_window
    if hasattr(gui_app, "paned"):
        return gui_app.paned
    raise AttributeError(
        "Nieznany układ AstraEdit (brak paned_window / paned). "
        "Zaktualizuj vendor/Astraedit lub ASTRAEDIT_PATH."
    )


def _restyle_astraedit_tabs(gui_app) -> None:
    """Upewnij się, że karty notebooka są widoczne po zmianie układu."""
    import tkinter as tk
    from tkinter import ttk

    root = gui_app.root
    bg = getattr(gui_app, "bg_color", "#1e1e1e")
    fg = getattr(gui_app, "fg_color", "#d4d4d4")
    style = ttk.Style(root)
    try:
        style.theme_use("default")
    except tk.TclError:
        pass
    style.configure("TNotebook", background=bg, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background="#2d2d2d",
        foreground=fg,
        padding=[10, 5],
        borderwidth=0,
    )
    style.map("TNotebook.Tab", background=[("selected", "#007acc")])


def _fix_vertical_panes(editor_shell) -> None:
    """Edytor (góra) musi mieć min. wysokość — inaczej znikają karty."""
    try:
        panes = editor_shell.panes()
        if panes:
            editor_shell.paneconfigure(panes[0], minsize=280)
        h = editor_shell.winfo_height()
        if h > 320 and hasattr(editor_shell, "sash_place"):
            editor_shell.sash_place(0, 0, int(h * 0.72))
    except Exception:
        pass


def attach_lore_to_astraedit(gui_app, lore: "LoreStore") -> None:
    """
    Dodaje panel lore po prawej stronie istniejącego AstraEditGUI.
    Wywołaj przed gui.run(), po utworzeniu okna.
    """
    import tkinter as tk
    from tkinter import filedialog

    from lore.document_hooks import on_file_opened, on_file_saved
    from lore.panel import LorePanel

    root = gui_app.root
    editor_shell = _editor_shell(gui_app)
    status_bar = getattr(gui_app, "status_bar", None)
    bg = getattr(gui_app, "bg_color", "#1e1e1e")

    def _active_tab():
        if hasattr(gui_app, "get_current_tab"):
            return gui_app.get_current_tab()
        if hasattr(gui_app, "_get_current_tab"):
            return gui_app._get_current_tab()
        return None

    def current_file() -> str:
        tab = _active_tab()
        if tab is not None:
            return getattr(tab, "file_path", "")
        tabs = getattr(gui_app, "_tabs", [])
        if tabs:
            return getattr(tabs[0], "file_path", "")
        return ""

    editor_shell.pack_forget()
    if status_bar is not None:
        status_bar.pack_forget()

    body = tk.Frame(root, bg=bg)
    body.pack(fill="both", expand=True)

    editor_shell.pack(in_=body, side="left", fill="both", expand=True)

    right_host = tk.Frame(body, bg=bg, width=LORE_PANEL_WIDTH)
    right_host.pack(side="right", fill="both")
    right_host.pack_propagate(False)

    right = LorePanel(right_host, lore, get_current_file=current_file)
    right.pack(fill="both", expand=True)

    if status_bar is not None:
        status_bar.pack(side="bottom", fill="x")

    _restyle_astraedit_tabs(gui_app)
    _fix_vertical_panes(editor_shell)
    root.update_idletasks()
    root.after(50, lambda: _fix_vertical_panes(editor_shell))
    root.after(200, lambda: (_restyle_astraedit_tabs(gui_app), _fix_vertical_panes(editor_shell)))

    orig_open = gui_app.open_file

    def open_with_lore(file_path, *args, **kwargs):
        result = orig_open(file_path, *args, **kwargs)
        path = str(Path(file_path).resolve())
        if os.path.isfile(path):
            on_file_opened(lore, path, right)
        return result

    gui_app.open_file = open_with_lore

    def open_dialog_with_lore():
        paths = filedialog.askopenfilenames(
            parent=root,
            title="Otwórz pliki",
            initialdir=str(lore.katalog_projektu()),
            filetypes=[("Tekst", "*.txt *.md"), ("Wszystkie", "*.*")],
        )
        for path in paths:
            if path:
                open_with_lore(path)

    gui_app.open_file_dialog = open_dialog_with_lore

    orig_save = gui_app.save_current

    def save_with_lore(*args, **kwargs):
        result = orig_save(*args, **kwargs)
        path = current_file()
        if path:
            on_file_saved(lore, path, right)
        return result

    gui_app.save_current = save_with_lore

    if hasattr(gui_app, "save_as"):
        orig_save_as = gui_app.save_as

        def save_as_with_lore(*args, **kwargs):
            result = orig_save_as(*args, **kwargs)
            path = current_file()
            if path:
                on_file_saved(lore, path, right)
            return result

        gui_app.save_as = save_as_with_lore

    if hasattr(gui_app, "on_tab_changed"):
        orig_tab = gui_app.on_tab_changed

        def tab_with_lore(event=None):
            orig_tab(event)
            path = current_file()
            if path and os.path.isfile(path):
                on_file_opened(lore, path, right)

        gui_app.on_tab_changed = tab_with_lore

    try:
        mb = root.nametowidget(root.cget("menu"))
        lm = tk.Menu(mb, tearoff=0)
        lm.add_command(label="Otwórz z folderu projektu…", command=open_dialog_with_lore)
        lm.add_command(label="Odśwież panel lore", command=right.odswiez)
        lm.add_command(label="Zapisz projekt lore", command=lore.zapisz)
        mb.add_cascade(label="Lore", menu=lm)
    except Exception:
        pass

    path = current_file()
    if path and os.path.isfile(path):
        on_file_opened(lore, path, right)