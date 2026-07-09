#!/usr/bin/env python3
"""
Lore Editor — edytor rozdziałów z panelem lore (bez KarminQL).

    python run_lore_editor.py --project MojaPowiesc
    python run_lore_editor.py --project MojaPowiesc --astraedit
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _run_standalone(project: str, file_path: str | None) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    from lore.panel import LorePanel
    from lore.store import LoreStore

    lore = LoreStore.open_local(project)

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
            filetypes=[("Tekst", "*.txt *.md"), ("Wszystkie", "*.*")]
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
        lore.otworz_dokument(p)
        panel.odswiez()

    def _save():
        p = state["path"]
        if not p:
            p = filedialog.asksaveasfilename(defaultextension=".txt")
            if not p:
                return
            state["path"] = p
        try:
            Path(p).write_text(text.get("1.0", tk.END), encoding="utf-8")
            lore.otworz_dokument(p)
            lore.zapisz()
            state["dirty"] = False
            panel.odswiez()
        except OSError as e:
            messagebox.showerror("Błąd", str(e))

    if file_path and Path(file_path).is_file():
        content = Path(file_path).read_text(encoding="utf-8")
        text.delete("1.0", tk.END)
        text.insert("1.0", content)
        state["path"] = file_path
        lore.otworz_dokument(file_path)
        panel.odswiez()
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


def _run_astraedit(project: str, files: list[str]) -> None:
    """Uruchom AstraEdit z panelem lore (wymaga AstraEdit na PYTHONPATH)."""
    from lore.astraedit_bridge import attach_lore_to_astraedit
    from lore.store import LoreStore

    lore = LoreStore.open_local(project)

    # Szukaj AstraEdit
    candidates = [
        Path(os.environ.get("ASTRAEDIT_PATH", "")),
        Path.home() / "Documents" / "AstraEdit",
        Path(__file__).resolve().parent.parent / "AstraEdit",
    ]
    for base in candidates:
        if not base or not base.is_dir():
            continue
        sys.path.insert(0, str(base))

    try:
        from AstraEdit import AstraEditGUI  # type: ignore
    except ImportError:
        try:
            # KarmazynOS edition — moduł jako plik
            import importlib.util

            for name in ("AstraEdit.pyw", "AstraEdit.py"):
                p = candidates[0] / name if candidates[0].is_dir() else None
                if p and p.is_file():
                    spec = importlib.util.spec_from_file_location("astraedit_mod", p)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    AstraEditGUI = mod.AstraEditGUI
                    break
            else:
                raise ImportError("Brak AstraEdit")
        except Exception as e:
            print(f"Nie znaleziono AstraEdit: {e}")
            print("Użyj: python run_lore_editor.py --project Nazwa  (standalone)")
            print("Lub ustaw ASTRAEDIT_PATH na katalog z AstraEdit.pyw")
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
    parser.add_argument("--file", "-f", default=None, help="Plik do otwarcia")
    parser.add_argument("--astraedit", action="store_true", help="Użyj AstraEdit zamiast prostego edytora")
    parser.add_argument("files", nargs="*", help="Pliki (tryb --astraedit)")
    args = parser.parse_args()

    if args.astraedit:
        _run_astraedit(args.project, args.files or ([args.file] if args.file else []))
    else:
        _run_standalone(args.project, args.file)


if __name__ == "__main__":
    main()