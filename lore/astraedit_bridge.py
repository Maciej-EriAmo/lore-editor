"""
Most do AstraEdit — dołącza panel Lore bez znajomości bazy danych.

Użycie (po imporcie AstraEditGUI):

    from lore.store import LoreStore
    from lore.astraedit_bridge import attach_lore_to_astraedit

    lore = LoreStore.open_local("MojaPowiesc")
    gui = AstraEditGUI(files=[...])
    attach_lore_to_astraedit(gui, lore)
    gui.run()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lore.store import LoreStore


def attach_lore_to_astraedit(gui_app, lore: "LoreStore") -> None:
    """
    Dodaje panel lore po prawej stronie istniejącego AstraEditGUI.
    Wywołaj przed gui.run(), po utworzeniu okna.
    """
    import tkinter as tk
    from tkinter import ttk

    from lore.panel import LorePanel

    root = gui_app.root

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

    outer = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    outer.pack(fill="both", expand=True)

    # Przenieś istniejący układ edytora do lewej części
    gui_app.paned.pack_forget()
    if hasattr(gui_app, "status_bar"):
        gui_app.status_bar.pack_forget()

    left = ttk.Frame(outer)
    outer.add(left, weight=3)
    gui_app.paned.pack(in_=left, fill="both", expand=True)
    if hasattr(gui_app, "status_bar"):
        gui_app.status_bar.pack(in_=left, side="bottom", fill="x")

    right = LorePanel(
        outer,
        lore,
        get_current_file=current_file,
        width=280,
    )
    outer.add(right, weight=1)

    orig_open = gui_app.open_file

    def open_with_lore(path, *args, **kwargs):
        result = orig_open(path, *args, **kwargs)
        try:
            lore.otworz_dokument(path)
            right.odswiez()
        except Exception:
            pass
        return result

    gui_app.open_file = open_with_lore

    orig_save = gui_app.save_current

    def save_with_lore(*args, **kwargs):
        result = orig_save(*args, **kwargs)
        try:
            lore.zapisz()
        except Exception:
            pass
        return result

    gui_app.save_current = save_with_lore

    if hasattr(gui_app, "on_tab_changed"):
        orig_tab = gui_app.on_tab_changed

        def tab_with_lore(event=None):
            orig_tab(event)
            path = current_file()
            if path:
                try:
                    lore.otworz_dokument(path)
                    right.odswiez()
                except Exception:
                    pass

        gui_app.on_tab_changed = tab_with_lore

    # Menu Lore
    try:
        mb = root.nametowidget(root.cget("menu"))
        lm = tk.Menu(mb, tearoff=0)
        lm.add_command(label="Odśwież panel lore", command=right.odswiez)
        lm.add_command(label="Zapisz projekt lore", command=lore.zapisz)
        mb.add_cascade(label="Lore", menu=lm)
    except Exception:
        pass