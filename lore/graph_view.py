"""Wizualizacja grafu lore — okno dla pisarza (bez KarminQL)."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from lore.store import LoreStore

_NODE_COLORS = {
    "Postać": "#4a9eff",
    "Miejsce": "#6bcb77",
    "Scena": "#ffd93d",
    "Pomysł": "#c77dff",
    "Wpływ": "#ff6b6b",
    "Dokument": "#858585",
    "Inne": "#5c5c5c",
}


def _layout_circular(
    node_ids: List[str],
    seed: str,
    cx: float,
    cy: float,
    radius: float,
) -> Dict[str, Tuple[float, float]]:
    if not node_ids:
        return {}
    if seed in node_ids:
        ordered = [seed] + [n for n in node_ids if n != seed]
    else:
        ordered = list(node_ids)
    n = len(ordered)
    pos: Dict[str, Tuple[float, float]] = {}
    if n == 1:
        pos[ordered[0]] = (cx, cy)
        return pos
    for i, nid in enumerate(ordered):
        angle = (2 * math.pi * i / n) - math.pi / 2
        r = radius * 0.35 if i == 0 and seed in node_ids else radius
        pos[nid] = (cx + r * math.cos(angle), cy + r * math.sin(angle))
    return pos


class LoreGraphWindow(tk.Toplevel):
    """Mapa powiązań wokół rozdziału lub wybranej encji."""

    def __init__(self, parent, lore: "LoreStore", seed: str | None = None, promien: int = 2):
        super().__init__(parent)
        self.title("Mapa lore")
        self.geometry("520x420")
        self.minsize(400, 300)

        self._lore = lore
        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=4)
        ttk.Label(top, text="Promień:").pack(side="left")
        self._promien = tk.IntVar(value=promien)
        ttk.Spinbox(top, from_=1, to=5, width=4, textvariable=self._promien).pack(side="left", padx=4)
        ttk.Button(top, text="Odśwież", command=self._redraw).pack(side="left", padx=4)

        self._canvas = tk.Canvas(self, bg="#1e1e1e", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True, padx=4, pady=4)

        self._seed = seed
        self._redraw()

    def _redraw(self) -> None:
        self._canvas.delete("all")
        try:
            graph = self._lore.graf_powiazan(self._seed, promien=int(self._promien.get()))
        except Exception as e:
            self._canvas.create_text(20, 20, anchor="nw", fill="#ff6b6b", text=str(e))
            return

        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []
        if not nodes:
            self._canvas.create_text(
                20, 20, anchor="nw", fill="#aaa",
                text="Brak powiązań.\nDodaj postać lub pomysł przy rozdziale.",
            )
            return

        w = max(self._canvas.winfo_width(), 400)
        h = max(self._canvas.winfo_height(), 300)
        ids = [n["id"] for n in nodes]
        pos = _layout_circular(ids, graph.get("seed", ""), w / 2, h / 2, min(w, h) * 0.35)

        for edge in edges:
            a, b = edge.get("from"), edge.get("to")
            if a not in pos or b not in pos:
                continue
            x1, y1 = pos[a]
            x2, y2 = pos[b]
            self._canvas.create_line(x1, y1, x2, y2, fill="#555", width=1, arrow=tk.LAST)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            rel = edge.get("rel", "")
            if rel:
                self._canvas.create_text(mx, my - 8, text=rel, fill="#888", font=("Segoe UI", 9))

        for node in nodes:
            nid = node["id"]
            if nid not in pos:
                continue
            x, y = pos[nid]
            typ = node.get("typ", "Inne")
            color = _NODE_COLORS.get(typ, _NODE_COLORS["Inne"])
            r = 28 if nid == graph.get("seed") else 22
            self._canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="#fff", width=1)
            label = nid if len(nid) <= 14 else nid[:12] + "…"
            self._canvas.create_text(x, y, text=label, fill="#111", font=("Segoe UI", 10, "bold"), width=r * 1.8)


def open_graph_window(parent, lore: "LoreStore", seed: str | None = None) -> LoreGraphWindow:
    return LoreGraphWindow(parent, lore, seed=seed)