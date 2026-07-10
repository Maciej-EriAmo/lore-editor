"""Okno pomocy wbudowanej."""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Optional

from lore.help_topics import DEFAULT_TOPIC, get_topic, topic_titles
from lore.theme import apply_theme, style_text


class HelpWindow:
    def __init__(self, parent: tk.Misc, *, initial_topic: str = DEFAULT_TOPIC) -> None:
        self._win: Optional[tk.Toplevel] = None
        self._parent = parent
        self._initial = initial_topic

    def show(self) -> None:
        if self._win is not None and self._win.winfo_exists():
            self._win.lift()
            self._win.focus_force()
            return

        win = tk.Toplevel(self._parent)
        self._win = win
        win.title("Pomoc — Lore Editor")
        win.geometry("780x560")
        win.minsize(520, 400)
        win.transient(self._parent)
        apply_theme(win)

        body = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
        body.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(body, padding=4)
        body.add(left, weight=1)
        ttk.Label(left, text="Tematy", style="Head.TLabel").pack(anchor="w", pady=(0, 6))

        self._list = tk.Listbox(left, exportselection=False)
        from lore.theme import style_listbox

        style_listbox(self._list)
        self._list.pack(fill="both", expand=True)
        for title in topic_titles():
            self._list.insert(tk.END, title)
        self._list.bind("<<ListboxSelect>>", self._on_select)

        right = ttk.Frame(body, padding=4)
        body.add(right, weight=3)

        self._title_var = tk.StringVar()
        ttk.Label(right, textvariable=self._title_var, style="Head.TLabel").pack(anchor="w")

        self._text = scrolledtext.ScrolledText(right, wrap="word", state="disabled")
        style_text(self._text, height=24, mono=False)
        self._text.pack(fill="both", expand=True, pady=(6, 0))

        foot = ttk.Frame(win, padding=(8, 4))
        foot.pack(fill="x")
        ttk.Button(foot, text="Zamknij", command=win.destroy).pack(side="right")

        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.bind("<Escape>", lambda _e: win.destroy())

        self._select_topic(self._initial)

    def _on_select(self, _event=None) -> None:
        sel = self._list.curselection()
        if not sel:
            return
        title = self._list.get(int(sel[0]))
        self._load_topic(title)

    def _select_topic(self, title: str) -> None:
        titles = topic_titles()
        if title not in titles:
            title = DEFAULT_TOPIC
        idx = titles.index(title)
        self._list.selection_clear(0, tk.END)
        self._list.selection_set(idx)
        self._list.see(idx)
        self._load_topic(title)

    def _load_topic(self, title: str) -> None:
        heading, body = get_topic(title)
        self._title_var.set(heading)
        self._text.configure(state="normal")
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", body)
        self._text.configure(state="disabled")


def open_help(parent: tk.Misc, topic: str = DEFAULT_TOPIC) -> None:
    HelpWindow(parent, initial_topic=topic).show()