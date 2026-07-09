"""
Most do AstraEdit — dołącza panel Lore bez znajomości bazy danych.
Obsługuje AstraEdit 4.5+ (paned_window) i starsze wersje (paned).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lore.store import LoreStore


def _editor_shell(gui_app):
    """Główny kontener edytora — różny w zależności od wersji AstraEdit."""
    if hasattr(gui_app, "paned_window"):
        return gui_app.paned_window
    if hasattr(gui_app, "paned"):
        return gui_app.paned
    raise AttributeError(
        "Nieznany układ AstraEdit (brak paned_window / paned). "
        "Zaktualizuj vendor/Astraedit lub ASTRAEDIT_PATH."
    )


def attach_lore_to_astraedit(gui_app, lore: "LoreStore") -> None:
    """
    Dodaje panel lore po prawej stronie istniejącego AstraEditGUI.
    Wywołaj przed gui.run(), po utworzeniu okna.
    """
    import tkinter as tk
    from tkinter import ttk

    from lore.document_hooks import on_file_opened, on_file_saved
    from lore.panel import LorePanel

    root = gui_app.root
    editor_shell = _editor_shell(gui_app)
    status_bar = getattr(gui_app, "status_bar", None)

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

    outer = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    outer.pack(fill="both", expand=True)

    left = ttk.Frame(outer)
    outer.add(left, weight=3)
    editor_shell.pack(in_=left, fill="both", expand=True)

    right = LorePanel(
        outer,
        lore,
        get_current_file=current_file,
        width=300,
    )
    outer.add(right, weight=1)

    if status_bar is not None:
        status_bar.pack(side="bottom", fill="x")

    orig_open = gui_app.open_file

    def open_with_lore(path, *args, **kwargs):
        result = orig_open(path, *args, **kwargs)
        on_file_opened(lore, path, right)
        return result

    gui_app.open_file = open_with_lore

    orig_save = gui_app.save_current

    def save_with_lore(*args, **kwargs):
        result = orig_save(*args, **kwargs)
        on_file_saved(lore, current_file(), right)
        return result

    gui_app.save_current = save_with_lore

    if hasattr(gui_app, "on_tab_changed"):
        orig_tab = gui_app.on_tab_changed

        def tab_with_lore(event=None):
            orig_tab(event)
            on_file_opened(lore, current_file(), right)

        gui_app.on_tab_changed = tab_with_lore

    try:
        mb = root.nametowidget(root.cget("menu"))
        lm = tk.Menu(mb, tearoff=0)
        lm.add_command(label="Odśwież panel lore", command=right.odswiez)
        lm.add_command(label="Zapisz projekt lore", command=lore.zapisz)
        mb.add_cascade(label="Lore", menu=lm)
    except Exception:
        pass