"""Podgląd stron A4 / Letter w oknie Tk."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from lore.manuscript import ManuscriptStats, paginate
from lore.theme import BG, BG_INPUT, BG_PANEL, BORDER, FG, FG_DIM


def open_print_preview(
    parent: tk.Misc,
    text: str,
    *,
    profile_id: str = "print_ready",
    title: str = "Podgląd druku",
) -> None:
    stats = paginate(text, profile_id)
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("720x640")
    win.minsize(480, 400)
    win.transient(parent)
    win.configure(bg=BG)

    hdr = ttk.Frame(win, padding=8)
    hdr.pack(fill="x")
    ttk.Label(hdr, text=stats.profile.label, style="Head.TLabel").pack(anchor="w")
    ttk.Label(
        hdr,
        text=_header_detail(stats),
        style="Dim.TLabel",
        wraplength=680,
    ).pack(anchor="w", pady=(4, 0))

    canvas_frame = ttk.Frame(win)
    canvas_frame.pack(fill="both", expand=True, padx=8, pady=4)

    canvas = tk.Canvas(canvas_frame, bg="#4a4a4a", highlightthickness=0)
    scroll_y = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scroll_y.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    inner = ttk.Frame(canvas)
    canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_configure(_event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    inner.bind("<Configure>", _on_configure)
    canvas.bind("<Configure>", _on_configure)

    w_mm, h_mm = stats.profile.page_size_mm
    scale = 1.4  # px per mm (miniatura)
    page_w = int(w_mm * scale)
    page_h = int(h_mm * scale)
    margin_px = int(stats.profile.margin_mm * scale)

    slices = stats.page_slices or ()
    if not slices:
        slices = ()

    for sl in slices:
        frame = tk.Frame(inner, bg=BORDER, padx=1, pady=1)
        frame.pack(pady=10, padx=12)

        page = tk.Canvas(frame, width=page_w, height=page_h, bg="white", highlightthickness=0)
        page.pack()
        page.create_rectangle(
            margin_px,
            margin_px,
            page_w - margin_px,
            page_h - margin_px,
            outline="#cccccc",
            dash=(4, 2),
        )
        page.create_text(
            margin_px + 4,
            margin_px + 4,
            text=f"Strona {sl.number}",
            anchor="nw",
            fill="#888888",
            font=("Segoe UI", 8),
        )
        body = sl.preview or "(pusto)"
        if len(body) > 900:
            body = body[:900] + "…"
        page.create_text(
            margin_px + 6,
            margin_px + 22,
            text=body,
            anchor="nw",
            fill="#222222",
            font=("Times New Roman", 7),
            width=page_w - 2 * margin_px - 12,
        )

    if not slices:
        ttk.Label(inner, text="Brak treści do podglądu.", style="Dim.TLabel").pack(pady=20)

    btn = ttk.Frame(win, padding=8)
    btn.pack(fill="x")
    ttk.Button(btn, text="Zamknij", command=win.destroy).pack(side="right")


def _header_detail(stats: ManuscriptStats) -> str:
    prof = stats.profile
    w, h = prof.page_size_mm
    fmt = prof.page_format
    base = (
        f"{stats.summary()} · {prof.font_family} {prof.font_size_pt} pt · "
        f"interlinia {prof.line_spacing:g} · margines {prof.margin_mm:.0f} mm · "
        f"{fmt} ({w:.0f}×{h:.0f} mm)"
    )
    if prof.screenplay_timing:
        base += " · reguła: 1 strona ≈ 1 minuta"
    return base