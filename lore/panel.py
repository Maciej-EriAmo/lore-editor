"""
Panel lore dla edytora — Tkinter, bez KarminQL.
Pisarz: dodaj postać, pomysł, powiąż z rozdziałem, przeglądaj sąsiadów.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional

from lore.store import LoreStore
from lore.types import RELACJE_LORE, TypLore


class LorePanel(ttk.Frame):
    """Boczny panel do osadzenia w AstraEdit lub standalone."""

    def __init__(
        self,
        parent,
        lore: LoreStore,
        *,
        get_current_file: Optional[Callable[[], str]] = None,
        on_open_entity: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._lore = lore
        self._get_file = get_current_file or (lambda: "")
        self._on_open = on_open_entity

        self._build_ui()
        self.odswiez()

    def _build_ui(self) -> None:
        hdr = ttk.Label(self, text="Lore", font=("Segoe UI", 11, "bold"))
        hdr.pack(fill="x", padx=6, pady=(6, 2))

        sub = ttk.Label(
            self,
            text=f"Projekt: {self._lore.nazwa_projektu()}",
            font=("Segoe UI", 8),
        )
        sub.pack(fill="x", padx=6, pady=(0, 6))

        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", padx=4, pady=2)
        ttk.Button(btn_row, text="+ Postać", width=9, command=self._dlg_postac).pack(
            side="left", padx=2
        )
        ttk.Button(btn_row, text="+ Pomysł", width=9, command=self._dlg_pomysl).pack(
            side="left", padx=2
        )
        ttk.Button(btn_row, text="+ Wpływ", width=9, command=self._dlg_wplyw).pack(
            side="left", padx=2
        )

        ttk.Label(self, text="Przy tym rozdziale:", font=("Segoe UI", 9)).pack(
            anchor="w", padx=6, pady=(8, 2)
        )

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=4, pady=2)

        self._list = tk.Listbox(
            list_frame,
            font=("Segoe UI", 9),
            activestyle="none",
            selectmode=tk.SINGLE,
            height=12,
        )
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._list.yview)
        self._list.configure(yscrollcommand=scroll.set)
        self._list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._list.bind("<Double-Button-1>", self._on_double_click)

        act = ttk.Frame(self)
        act.pack(fill="x", padx=4, pady=4)
        ttk.Button(act, text="Powiąż z rozdziałem", command=self._powiaz).pack(
            fill="x", pady=2
        )
        ttk.Button(act, text="Połącz z…", command=self._dlg_polacz).pack(fill="x", pady=2)
        ttk.Button(act, text="Odśwież", command=self.odswiez).pack(fill="x", pady=2)

        ttk.Label(self, text="Szukaj w lore:", font=("Segoe UI", 9)).pack(
            anchor="w", padx=6, pady=(4, 0)
        )
        sf = ttk.Frame(self)
        sf.pack(fill="x", padx=4, pady=2)
        self._search_var = tk.StringVar()
        ttk.Entry(sf, textvariable=self._search_var).pack(side="left", fill="x", expand=True)
        ttk.Button(sf, text="Szukaj", command=self._szukaj).pack(side="left", padx=2)

        self._detail = tk.Text(self, height=6, font=("Segoe UI", 9), wrap="word")
        self._detail.pack(fill="x", padx=4, pady=(4, 6))
        self._detail.configure(state="disabled")

        self._list.bind("<<ListboxSelect>>", self._on_select)

    def odswiez(self) -> None:
        path = self._get_file()
        if path:
            try:
                self._lore.otworz_dokument(path)
            except Exception:
                pass
        self._list.delete(0, tk.END)
        try:
            items = self._lore.lore_przy_dokumencie(path or None)
        except Exception as e:
            items = []
            self._set_detail(f"Błąd: {e}")
        for it in items:
            self._list.insert(tk.END, f"{it.get('typ', '?')}: {it['nazwa']}")
        self._items = items

    def _selected_name(self) -> Optional[str]:
        sel = self._list.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if idx < len(getattr(self, "_items", [])):
            return self._items[idx]["nazwa"]
        return None

    def _on_select(self, _event=None) -> None:
        name = self._selected_name()
        if not name:
            return
        try:
            data = self._lore.podglad(name)
            lines = [f"【{name}】"]
            for k, v in sorted(data.items()):
                if k in ("BĄBEL",) or v in (None, ""):
                    continue
                lines.append(f"{k}: {v}")
            self._set_detail("\n".join(lines))
        except Exception as e:
            self._set_detail(str(e))

    def _on_double_click(self, _event=None) -> None:
        name = self._selected_name()
        if name and self._on_open:
            self._on_open(name)

    def _set_detail(self, text: str) -> None:
        self._detail.configure(state="normal")
        self._detail.delete("1.0", tk.END)
        self._detail.insert("1.0", text)
        self._detail.configure(state="disabled")

    def _dlg_postac(self) -> None:
        nazwa = simpledialog.askstring("Postać", "Imię / nazwa postaci:", parent=self)
        if not nazwa:
            return
        notatka = simpledialog.askstring("Postać", "Krótka notatka (opcjonalnie):", parent=self) or ""
        try:
            self._lore.dodaj_postac(nazwa, notatka=notatka)
            path = self._get_file()
            if path:
                self._lore.powiaz_z_dokumentem(nazwa, path)
            self._lore.zapisz()
            self.odswiez()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _dlg_pomysl(self) -> None:
        tekst = simpledialog.askstring("Pomysł", "Zapisz myśl / pomysł:", parent=self)
        if not tekst:
            return
        try:
            self._lore.wklej_pomysl_do_dokumentu(tekst)
            self._lore.zapisz()
            self.odswiez()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _dlg_wplyw(self) -> None:
        nazwa = simpledialog.askstring("Wpływ", "Np. Tolkien, Mit grecki…:", parent=self)
        if not nazwa:
            return
        notatka = simpledialog.askstring("Wpływ", "Co Cię inspirowało?", parent=self) or ""
        try:
            self._lore.dodaj_wplyw(nazwa, notatka=notatka)
            path = self._get_file()
            if path:
                self._lore.powiaz_z_dokumentem(nazwa, path, relacja="inspiruje")
            self._lore.zapisz()
            self.odswiez()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _powiaz(self) -> None:
        name = self._selected_name()
        if not name:
            messagebox.showinfo("Lore", "Wybierz element z listy.", parent=self)
            return
        path = self._get_file()
        if not path:
            messagebox.showinfo("Lore", "Otwórz najpierw rozdział (plik tekstowy).", parent=self)
            return
        try:
            self._lore.powiaz_z_dokumentem(name, path)
            self._lore.zapisz()
            self.odswiez()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _dlg_polacz(self) -> None:
        a = self._selected_name()
        if not a:
            messagebox.showinfo("Lore", "Wybierz pierwszy element z listy.", parent=self)
            return
        b = simpledialog.askstring("Połącz", "Drugi element (nazwa):", parent=self)
        if not b:
            return
        rel = simpledialog.askstring(
            "Połącz",
            f"Relacja ({', '.join(RELACJE_LORE[:4])}…):",
            initialvalue="koliguje z",
            parent=self,
        ) or "koliguje z"
        try:
            self._lore.polacz(a, b, rel)
            self._lore.zapisz()
            self.odswiez()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _szukaj(self) -> None:
        q = self._search_var.get().strip()
        if not q:
            return
        try:
            hits = self._lore.szukaj(q)
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)
            return
        self._list.delete(0, tk.END)
        self._items = [{"nazwa": h, "typ": "?", "opis": ""} for h in hits]
        for h in hits:
            self._list.insert(tk.END, h)
        self._set_detail(f"Znaleziono: {len(hits)}")