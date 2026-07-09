#!/usr/bin/env python3
"""
Lore Editor — edytor rozdziałów z panelem lore (bez KarminQL).

    python run_lore_editor.py --project MojaPowiesc
    python run_lore_editor.py --project MojaPowiesc --project-dir ~/Documents/MojaPowiesc
    python run_lore_editor.py --project MojaPowiesc --astraedit
    python run_lore_editor.py --project MojaPowiesc --rpc --host 192.168.1.10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _open_lore(project: str, project_dir: str | None, rpc: bool, host: str, port: int, profile: str | None):
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
    project: str,
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

    lore = _open_lore(project, project_dir, rpc, host, port, profile)
    proj_root = lore.katalog_projektu()

    root = tk.Tk()
    root.title(f"Lore Editor — {project}")
    root.geometry("1100x700")
    root.configure(bg="#1e1e1e")

    paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill="both", expand=True)

    left = ttk.Frame(paned)
    paned.add(left, weight=3)

    toolbar = ttk.Frame(left)
    toolbar.pack(fill="x")
    ttk.Button(toolbar, text="Otwórz…", command=lambda: _open()).pack(side="left", padx=4, pady=4)
    ttk.Button(toolbar, text="Zapisz", command=lambda: _save()).pack(side="left", padx=4, pady=4)

    text = scrolledtext.ScrolledText(
        left, wrap="word", undo=True, font=("Consolas", 11),
        bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
    )
    text.pack(fill="both", expand=True)

    state = {"path": file_path or "", "dirty": False}

    def current_file() -> str:
        return state["path"]

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
            content = Path(p).read_text(encoding="utf-8")
        except OSError as e:
            messagebox.showerror("Błąd", str(e))
            return
        text.delete("1.0", tk.END)
        text.insert("1.0", content)
        state["path"] = p
        state["dirty"] = False
        root.title(f"Lore Editor — {project} — {Path(p).name}")
        on_file_opened(lore, p, panel)

    def _save():
        p = state["path"]
        if not p:
            p = filedialog.asksaveasfilename(
                initialdir=str(proj_root),
                defaultextension=".txt",
            )
            if not p:
                return
            state["path"] = p
        try:
            Path(p).write_text(text.get("1.0", tk.END), encoding="utf-8")
            state["dirty"] = False
            on_file_saved(lore, p, panel)
        except OSError as e:
            messagebox.showerror("Błąd", str(e))

    if file_path and Path(file_path).is_file():
        content = Path(file_path).read_text(encoding="utf-8")
        text.delete("1.0", tk.END)
        text.insert("1.0", content)
        state["path"] = file_path
        on_file_opened(lore, file_path, panel)
        root.title(f"Lore Editor — {project} — {Path(file_path).name}")

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
    project: str,
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
        print("Użyj: python run_lore_editor.py --project Nazwa  (standalone)")
        sys.exit(1)

    gui = AstraEditGUI(files or None)
    attach_lore_to_astraedit(gui, lore)
    try:
        gui.run()
    finally:
        lore.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Lore Editor — pisarz + Cynober lore")
    parser.add_argument("--project", "-p", default="MojaPowiesc", help="Nazwa projektu / świata lore")
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Folder projektu (rozdziały + .kafd); domyślnie ~/.lore_editor/worlds/<projekt>",
    )
    parser.add_argument("--file", "-f", default=None, help="Plik do otwarcia")
    parser.add_argument("--astraedit", action="store_true", help="Użyj AstraEdit zamiast prostego edytora")
    parser.add_argument("--rpc", action="store_true", help="Lore na serwerze (cynober-server); rozdziały lokalnie")
    parser.add_argument("--host", default="127.0.0.1", help="Host cynober-server (--rpc lub sync)")
    parser.add_argument("--port", type=int, default=8080, help="Port cynober-server")
    parser.add_argument("--profile", default=None, help="Profil cynober-client zamiast --host/--port")
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