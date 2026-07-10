"""Okno historii zmian — przegląd i przywracanie snapshotów."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional

from lore.history import LoreHistoria, SnapshotInfo
from lore.store import LoreStore
from lore.theme import FONT_SMALL, style_listbox


class HistoryWindow(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        lore: LoreStore,
        *,
        on_restored: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._lore = lore
        self._on_restored = on_restored
        self._items: list[SnapshotInfo] = []

        self.title("Historia zmian")
        self.transient(parent.winfo_toplevel())
        self.geometry("520x380")
        self.minsize(420, 300)

        hdr = ttk.Frame(self, padding=8)
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Historia projektu", style="Head.TLabel").pack(anchor="w")
        ttk.Label(
            hdr,
            text="Snapshoty: lore (.kafd) + rozdziały (.txt/.md). Przywrócenie tworzy kopię bieżącego stanu.",
            style="Dim.TLabel",
            wraplength=480,
        ).pack(anchor="w", pady=(4, 0))

        body = ttk.Frame(self, padding=(8, 0))
        body.pack(fill="both", expand=True)
        self._list = tk.Listbox(body, font=FONT_SMALL, height=12)
        style_listbox(self._list)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self._list.yview)
        self._list.configure(yscrollcommand=scroll.set)
        self._list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._list.bind("<<ListboxSelect>>", self._on_select)

        self._detail = tk.Text(body, height=4, wrap="word", state="disabled")
        self._detail.pack_forget()

        btns = ttk.Frame(self, padding=8)
        btns.pack(fill="x")
        ttk.Button(btns, text="Utwórz punkt przywracania…", command=self._create).pack(side="left")
        ttk.Button(btns, text="Przywróć zaznaczone", command=self._restore).pack(side="left", padx=6)
        ttk.Button(btns, text="Odśwież", command=self._reload).pack(side="left")
        ttk.Button(btns, text="Zamknij", command=self.destroy).pack(side="right")

        self._reload()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _historia(self) -> LoreHistoria:
        return self._lore.historia()

    def _reload(self) -> None:
        self._items = self._historia().lista()
        self._list.delete(0, tk.END)
        for snap in self._items:
            reason = snap.reason
            line = f"{snap.data_utworzenia()}  ·  {snap.label}  [{reason}]"
            self._list.insert(tk.END, line)
        if self._items:
            self._list.selection_set(0)
            self._on_select()

    def _selected(self) -> Optional[SnapshotInfo]:
        sel = self._list.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        if 0 <= idx < len(self._items):
            return self._items[idx]
        return None

    def _on_select(self, _event=None) -> None:
        snap = self._selected()
        if not snap:
            return
        lines = [
            f"ID: {snap.id}",
            f"Plików: {len(snap.files)}",
        ]
        if snap.files:
            preview = ", ".join(snap.files[:6])
            if len(snap.files) > 6:
                preview += f" … (+{len(snap.files) - 6})"
            lines.append(f"Zawartość: {preview}")
        self._detail.configure(state="normal")
        self._detail.delete("1.0", tk.END)
        self._detail.insert("1.0", "\n".join(lines))
        self._detail.configure(state="disabled")

    def _create(self) -> None:
        label = simpledialog.askstring(
            "Punkt przywracania",
            "Opis (opcjonalnie):",
            parent=self,
        )
        try:
            info = self._historia().utworz(label=label or "", reason="manual", force=True)
        except OSError as e:
            messagebox.showerror("Historia", str(e), parent=self)
            return
        if info is None:
            messagebox.showinfo("Historia", "Brak zmian od ostatniego snapshotu.", parent=self)
            return
        self._reload()
        messagebox.showinfo("Historia", f"Utworzono: {info.label}", parent=self)

    def _restore(self) -> None:
        snap = self._selected()
        if not snap:
            messagebox.showinfo("Historia", "Wybierz snapshot z listy.", parent=self)
            return
        if not messagebox.askyesno(
            "Przywróć projekt",
            f"Przywrócić stan z:\n{snap.data_utworzenia()} — {snap.label}?\n\n"
            "Bieżący stan zostanie zapisany jako osobny snapshot.",
            parent=self,
        ):
            return
        try:
            self._lore.przywroc_historie(snap.id)
        except Exception as e:
            messagebox.showerror("Historia", str(e), parent=self)
            return
        if self._on_restored:
            self._on_restored()
        self._reload()
        messagebox.showinfo(
            "Historia",
            "Przywrócono. Otwarte karty rozdziałów zostały odświeżone z dysku.",
            parent=self,
        )


def open_history_window(
    parent: tk.Misc,
    lore: LoreStore,
    *,
    on_restored: Optional[Callable[[], None]] = None,
) -> None:
    if isinstance(parent, HistoryWindow) and parent.winfo_exists():
        parent.lift()
        return
    HistoryWindow(parent, lore, on_restored=on_restored)