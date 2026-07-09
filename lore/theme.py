"""Wspólny motyw UI — standalone i panel lore."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

BG = "#1e1e1e"
BG_PANEL = "#252526"
BG_INPUT = "#2d2d2d"
FG = "#d4d4d4"
FG_DIM = "#9d9d9d"
ACCENT = "#4a9eff"
BORDER = "#3c3c3c"
FONT_UI = ("Segoe UI", 9)
FONT_HEAD = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 11)
FONT_SMALL = ("Segoe UI", 8)


def apply_theme(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=BG)

    style.configure(".", background=BG_PANEL, foreground=FG, font=FONT_UI, borderwidth=0)
    style.configure("TFrame", background=BG_PANEL)
    style.configure("TLabelframe", background=BG_PANEL, foreground=FG_DIM, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG_PANEL, foreground=FG_DIM, font=FONT_UI)
    style.configure("TLabel", background=BG_PANEL, foreground=FG)
    style.configure("Dim.TLabel", background=BG_PANEL, foreground=FG_DIM, font=FONT_SMALL)
    style.configure("Head.TLabel", background=BG_PANEL, foreground=FG, font=FONT_HEAD)
    style.configure("TButton", padding=(8, 4), background=BG_INPUT, foreground=FG)
    style.map("TButton", background=[("active", BORDER)])
    style.configure("Accent.TButton", padding=(8, 4))
    style.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG, insertcolor=FG)
    style.configure("TNotebook", background=BG_PANEL, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_INPUT, foreground=FG_DIM, padding=(10, 4))
    style.map("TNotebook.Tab", background=[("selected", BG_PANEL)], foreground=[("selected", FG)])
    style.configure("TPanedwindow", background=BORDER)
    style.configure("Vertical.TScrollbar", background=BG_INPUT, troughcolor=BG_PANEL)

    return style


def style_listbox(lb: tk.Listbox) -> None:
    lb.configure(
        bg=BG_INPUT,
        fg=FG,
        selectbackground=ACCENT,
        selectforeground="#111",
        highlightthickness=0,
        borderwidth=0,
        activestyle="none",
    )


def style_text(widget: tk.Text, *, height: int = 6, mono: bool = False) -> None:
    widget.configure(
        height=height,
        font=FONT_MONO if mono else FONT_UI,
        wrap="word",
        bg=BG_INPUT,
        fg=FG,
        insertbackground=FG,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        borderwidth=0,
    )