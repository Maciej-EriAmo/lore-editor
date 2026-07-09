#!/usr/bin/env python3
"""
Lore Editor — edytor rozdziałów z panelem lore (bez KarminQL).

    cd ~/Documents/MojaPowiesc && lore-editor
    lore-editor --project-dir .
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _open_lore(
    project: str | None,
    project_dir: str | None,
    rpc: bool,
    host: str,
    port: int,
    profile: str | None,
):
    from lore.store import LoreStore

    if rpc:
        return LoreStore.open_rpc(
            project,
            host=host,
            port=port,
            profile=profile,
            project_dir=project_dir,
        )
    return LoreStore.open_local(project, project_dir=project_dir)


def _run_standalone(
    project: str | None,
    file_path: str | None,
    *,
    project_dir: str | None,
    rpc: bool,
    host: str,
    port: int,
    profile: str | None,
) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    from lore.document_hooks import on_file_opened, on_file_saved
    from lore.panel import LorePanel
    from lore.text_io import read_text_smart, write_text
    from lore.theme import apply_theme, style_text

    lore = _open_lore(project, project_dir, rpc, host, port, profile)
    proj = lore.nazwa_projektu()
    proj_root = lore.katalog_projektu()

    root = tk.Tk()
    root.title(f"Lore Editor — {proj}")
    root.geometry("1150x720")
    root.minsize(900, 560)
    apply_theme(root)

    top = ttk.Frame(root, padding=(8, 6))
    top.pack(fill="x")

    ttk.Label(top, text="Lore Editor", style="Head.TLabel").pack(side="left")
    ttk.Label(top, text=f"  ·  {proj}", style="Dim.TLabel").pack(side="left")

    toolbar = ttk.Frame(top)
    toolbar.pack(side="right")
    status_var = tk.StringVar(value="Gotowy")

    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    left = ttk.Frame(paned)
    paned.add(left, weight=3)

    bar = ttk.Frame(left)
    bar.pack(fill="x", pady=(0, 4))
    ttk.Button(bar, text="Otwórz…", command=lambda: _open()).pack(side="left", padx=(0, 4))
    ttk.Button(bar, text="Zapisz", command=lambda: _save()).pack(side="left", padx=(0, 8))
    file_lbl = ttk.Label(bar, text="(brak pliku)", style="Dim.TLabel")
    file_lbl.pack(side="left", fill="x", expand=True)

    text = scrolledtext.ScrolledText(left, wrap="word", undo=True)
    style_text(text, height=1, mono=True)
    text.configure(height=1)
    text.pack(fill="both", expand=True)

    state = {"path": file_path or "", "dirty": False, "encoding": "utf-8"}

    def current_file() -> str:
        return state["path"]

    def _set_file_label(path: str) -> None:
        if not path:
            file_lbl.configure(text="(brak pliku)")
            return
        try:
            rel = Path(path).resolve().relative_to(proj_root)
            label = str(rel)
        except ValueError:
            label = Path(path).name
        file_lbl.configure(text=label)

    panel = LorePanel(paned, lore, get_current_file=current_file)
    paned.add(panel, weight=1)

    def _open():
        p = filedialog.askopenfilename(
            initialdir=str(proj_root),
            filetypes=[("Tekst", "*.txt *.md"), ("Wszystkie", "*.*")],
        )
        if not p:
            return
        try:
            content, enc = read_text_smart(p)
        except (OSError, ValueError) as e:
            messagebox.showerror("Błąd", str(e))
            return
        text.delete("1.0", tk.END)
        text.insert("1.0", content)
        state["path"] = p
        state["encoding"] = enc
        state["dirty"] = False
        root.title(f"Lore Editor — {proj} — {Path(p).name}")
        _set_file_label(p)
        status_var.set(f"Otwarto: {Path(p).name} ({enc})")
        on_file_opened(lore, p, panel)

    def _save():
        p = state["path"]
        if not p:
            p = filedialog.asksaveasfilename(
                initialdir=str(proj_root),
                defaultextension=".txt",
                filetypes=[("Tekst", "*.txt *.md")],
            )
            if not p:
                return
            state["path"] = p
        try:
            write_text(p, text.get("1.0", tk.END), state.get("encoding", "utf-8"))
            state["dirty"] = False
            _set_file_label(p)
            status_var.set(f"Zapisano ({state.get('encoding', 'utf-8')})")
            on_file_saved(lore, p, panel)
        except OSError as e:
            messagebox.showerror("Błąd", str(e))

    if file_path and Path(file_path).is_file():
        try:
            content, enc = read_text_smart(file_path)
        except (OSError, ValueError) as e:
            messagebox.showerror("Błąd", str(e))
            content, enc = "", "utf-8"
        text.delete("1.0", tk.END)
        text.insert("1.0", content)
        state["path"] = file_path
        state["encoding"] = enc
        _set_file_label(file_path)
        on_file_opened(lore, file_path, panel)
        root.title(f"Lore Editor — {proj} — {Path(file_path).name}")

    status = ttk.Frame(root, padding=(8, 4))
    status.pack(fill="x", side="bottom")
    ttk.Label(status, textvariable=status_var, style="Dim.TLabel").pack(side="left")
    ttk.Label(
        status,
        text=str(proj_root),
        style="Dim.TLabel",
    ).pack(side="right")

    def on_close():
        try:
            lore.zapisz()
            lore.close()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


def _run_astraedit(
    project: str | None,
    files: list[str],
    *,
    project_dir: str | None,
    rpc: bool,
    host: str,
    port: int,
    profile: str | None,
) -> None:
    from lore.astraedit_bridge import attach_lore_to_astraedit
    from lore.astraedit_loader import load_astraedit_gui

    lore = _open_lore(project, project_dir, rpc, host, port, profile)

    try:
        AstraEditGUI = load_astraedit_gui()
    except ImportError as e:
        print(e)
        print("Użyj: lore-editor  (standalone)")
        sys.exit(1)

    gui = AstraEditGUI(files or None)
    attach_lore_to_astraedit(gui, lore)
    try:
        gui.run()
    finally:
        lore.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lore Editor — pisarz + Cynober lore",
        epilog="W katalogu projektu utwórz .lore-project z linią name=NazwaProjektu",
    )
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="Nazwa świata (domyślnie: .lore-project lub nazwa folderu)",
    )
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Folder projektu; domyślnie cwd lub katalog z .lore-project",
    )
    parser.add_argument("--file", "-f", default=None, help="Plik do otwarcia")
    parser.add_argument("--astraedit", action="store_true", help="Użyj AstraEdit zamiast prostego edytora")
    parser.add_argument("--rpc", action="store_true", help="Lore na serwerze (cynober-server)")
    parser.add_argument("--host", default="127.0.0.1", help="Host cynober-server")
    parser.add_argument("--port", type=int, default=8080, help="Port cynober-server")
    parser.add_argument("--profile", default=None, help="Profil cynober-client")
    parser.add_argument("files", nargs="*", help="Pliki (tryb --astraedit)")
    args = parser.parse_args()

    kw = dict(
        project_dir=args.project_dir,
        rpc=args.rpc,
        host=args.host,
        port=args.port,
        profile=args.profile,
    )

    if args.astraedit:
        _run_astraedit(args.project, args.files or ([args.file] if args.file else []), **kw)
    else:
        _run_standalone(args.project, args.file, **kw)


if __name__ == "__main__":
    main()