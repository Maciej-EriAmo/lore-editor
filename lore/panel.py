"""
Panel lore dla edytora — Tkinter, bez KarminQL.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional

from lore.graph_view import open_graph_window
from lore.store import LoreStore
from lore.theme import style_listbox, style_text
from lore.types import (
    POLE_NOTATKA,
    POLE_OPIS,
    POLE_STANY,
    POLE_TEKST,
    POLE_ŹRÓDŁO,
    RELACJE_LORE,
    TypLore,
)

_POLA_EDYCJI: dict[str, tuple[str, ...]] = {
    TypLore.POSTAĆ.value: (POLE_NOTATKA, POLE_OPIS),
    TypLore.WPŁYW.value: (POLE_NOTATKA, POLE_ŹRÓDŁO),
    TypLore.POMYSŁ.value: (POLE_TEKST, POLE_ŹRÓDŁO),
    TypLore.DOKUMENT.value: (POLE_OPIS,),
    TypLore.MIEJSCE.value: (POLE_NOTATKA, POLE_OPIS),
    TypLore.SCENA.value: (POLE_NOTATKA, POLE_OPIS),
    TypLore.INNE.value: (POLE_NOTATKA, POLE_OPIS, POLE_TEKST),
}


def pola_do_edycji(typ: str) -> tuple[str, ...]:
    """Pola lore edytowalne w panelu — zależne od typu wpisu."""
    return _POLA_EDYCJI.get(typ, _POLA_EDYCJI[TypLore.INNE.value])


class _EditEntityDialog(tk.Toplevel):
    """Okno edycji notatki, opisu, tekstu pomysłu itd."""

    def __init__(
        self,
        parent: LorePanel,
        lore: LoreStore,
        name: str,
        typ: str,
        fields: tuple[str, ...],
        data: dict,
    ) -> None:
        super().__init__(parent)
        self._panel = parent
        self._lore = lore
        self._name = name
        self._fields = fields
        self._widgets: dict[str, tk.Text] = {}

        self.title(f"Edytuj — {name}")
        self.transient(parent.winfo_toplevel())
        self.resizable(True, True)
        self.minsize(320, 240)

        hdr = ttk.Frame(self, padding=8)
        hdr.pack(fill="x")
        ttk.Label(hdr, text=name, style="Head.TLabel").pack(anchor="w")
        ttk.Label(hdr, text=typ, style="Dim.TLabel").pack(anchor="w")

        body = ttk.Frame(self, padding=(8, 0))
        body.pack(fill="both", expand=True)

        for field in fields:
            block = ttk.Frame(body)
            block.pack(fill="x", pady=(0, 8))
            ttk.Label(block, text=field).pack(anchor="w")
            height = 5 if field in (POLE_TEKST, POLE_OPIS, POLE_NOTATKA) else 2
            txt = tk.Text(block, height=height, wrap="word")
            style_text(txt, height=height)
            txt.pack(fill="x", expand=True)
            val = data.get(field)
            if val is not None and val != "":
                txt.insert("1.0", str(val))
            self._widgets[field] = txt

        btns = ttk.Frame(self, padding=8)
        btns.pack(fill="x")
        ttk.Button(btns, text="Zapisz", command=self._save).pack(side="right", padx=(4, 0))
        ttk.Button(btns, text="Anuluj", command=self.destroy).pack(side="right")

        self.bind("<Escape>", lambda _e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grab_set()
        if self._widgets:
            next(iter(self._widgets.values())).focus_set()

    def _save(self) -> None:
        try:
            for field, widget in self._widgets.items():
                value = widget.get("1.0", "end-1c").strip()
                self._lore.ustaw(self._name, field, value)
            self._lore.zapisz()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)
            return
        self.destroy()
        self._panel._po_edycji_wpisu(self._name)


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
        super().__init__(parent, padding=4, **kwargs)
        self._lore = lore
        self._get_file = get_current_file or (lambda: "")
        self._on_open = on_open_entity

        self._build_ui()
        self.odswiez()

    def _build_ui(self) -> None:
        hdr = ttk.Frame(self)
        hdr.pack(fill="x", pady=(0, 6))
        ttk.Label(hdr, text="Lore", style="Head.TLabel").pack(anchor="w")
        ttk.Label(
            hdr,
            text=self._lore.nazwa_projektu(),
            style="Dim.TLabel",
        ).pack(anchor="w")
        folder = str(self._lore.katalog_projektu())
        if len(folder) > 42:
            folder = "…" + folder[-39:]
        ttk.Label(hdr, text=folder, style="Dim.TLabel").pack(anchor="w")

        add = ttk.LabelFrame(self, text="Dodaj", padding=4)
        add.pack(fill="x", pady=(0, 6))
        row = ttk.Frame(add)
        row.pack(fill="x")
        ttk.Button(row, text="+ Postać", command=self._dlg_postac).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(row, text="+ Pomysł", command=self._dlg_pomysl).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(row, text="+ Wpływ", command=self._dlg_wplyw).pack(side="left", expand=True, fill="x", padx=1)

        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True)

        tab_lore = ttk.Frame(self._notebook, padding=2)
        self._notebook.add(tab_lore, text="Rozdział")

        ttk.Label(tab_lore, text="Powiązane z tym plikiem:", style="Dim.TLabel").pack(anchor="w", pady=(0, 4))

        list_frame = ttk.Frame(tab_lore)
        list_frame.pack(fill="both", expand=True)
        self._list = tk.Listbox(list_frame, height=10)
        style_listbox(self._list)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._list.yview)
        self._list.configure(yscrollcommand=scroll.set)
        self._list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._list.bind("<Double-Button-1>", self._on_double_click)
        self._list.bind("<<ListboxSelect>>", self._on_select)
        self._list.bind("<Delete>", lambda _e: self._usun_wpis())

        act = ttk.Frame(tab_lore)
        act.pack(fill="x", pady=6)
        ttk.Button(act, text="Powiąż z rozdziałem", command=self._powiaz).pack(fill="x", pady=1)
        ttk.Button(act, text="Powiąż inny wpis…", command=self._dlg_powiaz).pack(fill="x", pady=1)
        ttk.Button(act, text="Połącz z…", command=self._dlg_polacz).pack(fill="x", pady=1)
        ttk.Button(act, text="Odłącz od rozdziału", command=self._odlacz).pack(fill="x", pady=1)
        ttk.Button(act, text="Edytuj wpis", command=self._dlg_edytuj).pack(fill="x", pady=1)
        ttk.Button(act, text="Usuń wpis", command=self._usun_wpis).pack(fill="x", pady=1)
        ttk.Button(act, text="Mapa powiązań", command=self._mapa).pack(fill="x", pady=1)
        ttk.Button(act, text="Odśwież", command=self.odswiez).pack(fill="x", pady=1)

        self._detail = tk.Text(tab_lore, height=5)
        style_text(self._detail, height=5)
        self._detail.pack(fill="x", pady=(4, 0))
        self._detail.configure(state="disabled")

        tab_search = ttk.Frame(self._notebook, padding=4)
        self._notebook.add(tab_search, text="Szukaj")
        sf = ttk.Frame(tab_search)
        sf.pack(fill="x", pady=4)
        self._search_var = tk.StringVar()
        ttk.Entry(sf, textvariable=self._search_var).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(sf, text="Szukaj", command=self._szukaj).pack(side="left")
        ttk.Label(
            tab_search,
            text=(
                "Zapytanie semantyczne lub fraza.\n"
                "Np.: postacie przy Anna nie od 5\n"
                "typ:Postać \"sojusznik\"  ·  wyniki → Rozdział"
            ),
            style="Dim.TLabel",
            wraplength=240,
        ).pack(anchor="w", pady=8)

        if self._lore.tryb_lokalny():
            tab_team = ttk.Frame(self._notebook, padding=4)
            self._notebook.add(tab_team, text="Zespół")
            ttk.Label(
                tab_team,
                text="Sync lore przez cynober-server.\nNajpierw zapisz projekt lokalnie.",
                style="Dim.TLabel",
                wraplength=240,
            ).pack(anchor="w", pady=(0, 8))
            team_row = ttk.Frame(tab_team)
            team_row.pack(fill="x", pady=2)
            self._host_var = tk.StringVar(value="127.0.0.1")
            self._port_var = tk.StringVar(value="8080")
            ttk.Label(team_row, text="Host").pack(side="left")
            ttk.Entry(team_row, textvariable=self._host_var, width=12).pack(side="left", fill="x", expand=True, padx=4)
            ttk.Label(team_row, text=":").pack(side="left")
            ttk.Entry(team_row, textvariable=self._port_var, width=5).pack(side="left", padx=2)
            ttk.Button(tab_team, text="Wyślij na serwer", command=self._sync_wyslij).pack(fill="x", pady=3)
            ttk.Button(tab_team, text="Pobierz z serwera", command=self._sync_pobierz).pack(fill="x", pady=3)
            ttk.Button(tab_team, text="Synchronizuj", command=self._sync_auto).pack(fill="x", pady=3)
        else:
            self._host_var = tk.StringVar()
            self._port_var = tk.StringVar()

    def _sciezka_rozdzialu(self) -> str:
        path = self._get_file()
        if not path:
            raise ValueError("Otwórz najpierw rozdział (plik tekstowy) w edytorze.")
        return path

    def odswiez(self) -> None:
        self._notebook.select(0)
        path = self._get_file()
        if path:
            try:
                self._lore.otworz_dokument(path)
            except Exception as e:
                self._set_detail(f"Błąd otwarcia dokumentu: {e}")
                return
        self._list.delete(0, tk.END)
        try:
            items = self._lore.lore_przy_dokumencie(path or None)
        except Exception as e:
            items = []
            self._set_detail(f"Błąd: {e}")
        for it in items:
            typ = it.get("typ", "?")
            temp = it.get("temperatura") or ""
            badge = f"[{temp[:4]}] " if temp else ""
            self._list.insert(tk.END, f"  {badge}{typ:<8}  {it['nazwa']}")
        self._items = items
        if items and not self._list.curselection():
            self._list.selection_set(0)
            self._on_select()

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
            as_of = self._lore.dokument_biezacy(self._get_file() or None)
            data = self._lore.podglad(name, as_of=as_of)
            ctx = data.get("_as_of", "")
            temp = data.get("_temperatura", "")
            hdr = f"【{name}】"
            if ctx:
                hdr += f"  ·  rozdział: {ctx}"
            if temp:
                hdr += f"  ·  {temp}"
            lines = [hdr]
            for k, v in sorted(data.items()):
                if k.startswith("_") or k in ("BĄBEL", POLE_STANY) or v in (None, ""):
                    continue
                lines.append(f"{k}: {v}")
            self._set_detail("\n".join(lines))
        except Exception as e:
            self._set_detail(str(e))

    def _on_double_click(self, _event=None) -> None:
        name = self._selected_name()
        if not name:
            return
        if self._on_open:
            self._on_open(name)
        else:
            self._dlg_edytuj()

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
            encja = self._lore.dodaj_postac(nazwa, notatka=notatka)
            try:
                path = self._sciezka_rozdzialu()
                self._lore.powiaz_z_dokumentem(encja, path)
            except ValueError:
                pass
            self._lore.zapisz()
            self.odswiez()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _dlg_pomysl(self) -> None:
        tekst = simpledialog.askstring("Pomysł", "Zapisz myśl / pomysł:", parent=self)
        if not tekst:
            return
        try:
            path = None
            try:
                path = self._sciezka_rozdzialu()
            except ValueError:
                pass
            self._lore.wklej_pomysl_do_dokumentu(tekst, sciezka_pliku=path)
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
            encja = self._lore.dodaj_wplyw(nazwa, notatka=notatka)
            try:
                path = self._sciezka_rozdzialu()
                self._lore.powiaz_z_dokumentem(encja, path, relacja="inspiruje")
            except ValueError:
                pass
            self._lore.zapisz()
            self.odswiez()
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _powiaz_wpis(self, name: str, *, relacja: str = "występuje w") -> None:
        path = self._sciezka_rozdzialu()
        self._lore.powiaz_z_dokumentem(name, path, relacja=relacja)
        self._lore.zapisz()
        self.odswiez()

    def _powiaz(self) -> None:
        name = self._selected_name()
        if not name:
            self._dlg_powiaz()
            return
        try:
            self._powiaz_wpis(name)
        except ValueError as e:
            messagebox.showinfo("Lore", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _dlg_powiaz(self) -> None:
        try:
            path = self._sciezka_rozdzialu()
        except ValueError as e:
            messagebox.showinfo("Lore", str(e), parent=self)
            return
        name = simpledialog.askstring(
            "Powiąż z rozdziałem",
            "Nazwa istniejącego wpisu lore (postać, pomysł, wpływ…):",
            parent=self,
        )
        if not name:
            return
        try:
            self._lore.powiaz_z_dokumentem(name.strip(), path)
            self._lore.zapisz()
            self.odswiez()
            messagebox.showinfo("Lore", f"Powiązano „{name.strip()}” z rozdziałem.", parent=self)
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _dlg_edytuj(self) -> None:
        name = self._selected_name()
        if not name:
            messagebox.showinfo("Lore", "Wybierz wpis do edycji.", parent=self)
            return
        try:
            as_of = self._lore.dokument_biezacy(self._get_file() or None)
            data = self._lore.podglad(name, as_of=as_of)
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)
            return
        typ = str(data.get("Typ") or TypLore.INNE.value)
        fields = pola_do_edycji(typ)
        _EditEntityDialog(self, self._lore, name, typ, fields, data)

    def _po_edycji_wpisu(self, name: str) -> None:
        """Odśwież listę i ponownie pokaż zaktualizowany podgląd."""
        self.odswiez()
        for idx, item in enumerate(getattr(self, "_items", [])):
            if item.get("nazwa") == name:
                self._list.selection_clear(0, tk.END)
                self._list.selection_set(idx)
                self._list.see(idx)
                break
        self._on_select()

    def _odlacz(self) -> None:
        name = self._selected_name()
        if not name:
            messagebox.showinfo("Lore", "Wybierz element z listy.", parent=self)
            return
        try:
            path = self._sciezka_rozdzialu()
            self._lore.odlacz_od_dokumentu(name, path)
            self._lore.zapisz()
            self.odswiez()
        except ValueError as e:
            messagebox.showinfo("Lore", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)

    def _usun_wpis(self) -> None:
        name = self._selected_name()
        if not name:
            messagebox.showinfo("Lore", "Wybierz element do usunięcia.", parent=self)
            return
        if not messagebox.askyesno(
            "Usuń wpis",
            f"Trwale usunąć „{name}” z projektu lore?\nTej operacji nie można cofnąć.",
            parent=self,
        ):
            return
        try:
            self._lore.usun_encje(name)
            self._lore.zapisz()
            self._set_detail("")
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
            hits = self._lore.zapytaj(q)
        except Exception as e:
            messagebox.showerror("Lore", str(e), parent=self)
            return
        self._notebook.select(0)
        self._list.delete(0, tk.END)
        self._items = hits
        for it in hits:
            typ = it.get("typ", "?")
            temp = it.get("temperatura") or ""
            badge = f"[{temp[:4]}] " if temp else ""
            self._list.insert(tk.END, f"  {badge}{typ:<8}  {it['nazwa']}")
        self._set_detail(f"Znaleziono: {len(hits)}")

    def _mapa(self) -> None:
        seed = self._selected_name()
        if not seed:
            path = self._get_file()
            if path:
                try:
                    seed = self._lore.otworz_dokument(path)
                except Exception:
                    seed = None
        try:
            open_graph_window(self.winfo_toplevel(), self._lore, seed=seed)
        except Exception as e:
            messagebox.showerror("Mapa lore", str(e), parent=self)

    def _sync_host_port(self) -> tuple[str, int]:
        host = self._host_var.get().strip()
        if not host:
            raise ValueError("Podaj adres serwera.")
        try:
            port = int(self._port_var.get().strip() or "8080")
        except ValueError as e:
            raise ValueError("Port musi być liczbą.") from e
        return host, port

    def _sync_wyslij(self) -> None:
        try:
            host, port = self._sync_host_port()
            self._lore.zapisz()
            wynik = self._lore.zespol().wyslij_na_serwer(host, port)
            messagebox.showinfo("Zespół", wynik.komunikat, parent=self)
        except Exception as e:
            messagebox.showerror("Zespół", str(e), parent=self)

    def _sync_pobierz(self) -> None:
        try:
            host, port = self._sync_host_port()
            wynik = self._lore.zespol().pobierz_z_serwera(host, port)
            self.odswiez()
            messagebox.showinfo("Zespół", wynik.komunikat, parent=self)
        except Exception as e:
            messagebox.showerror("Zespół", str(e), parent=self)

    def _sync_auto(self) -> None:
        try:
            host, port = self._sync_host_port()
            self._lore.zapisz()
            wynik = self._lore.zespol().synchronizuj(host, port)
            self.odswiez()
            messagebox.showinfo("Zespół", wynik.komunikat, parent=self)
        except Exception as e:
            messagebox.showerror("Zespół", str(e), parent=self)