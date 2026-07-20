#!/usr/bin/env python3
"""
Lore Editor — edytor rozdziałów z panelem lore.

    lore-editor
    lore-editor --project-dir ~/dokumenty/inna-powiesc
    cd folder-z-.lore-project && lore-editor

Domyślny katalog pracy (gdy brak --project-dir i .lore-project):
    ../dokumenty/lore  (względem korzenia repo lore-editor)
    albo LORE_DEFAULT_WORK_DIR / LORE_PROJECT_DIR

Pierwsze uruchomienie tworzy .lore-project i .lore-history/ (snapshoty).
Pomoc: F1 w aplikacji lub lore-editor --help.
"""

from __future__ import annotations

import argparse
import os
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
    *,
    project_dir: str | None,
    rpc: bool,
    host: str,
    port: int,
    profile: str | None,
    initial_files: list[str],
) -> None:
    from lore.editor_window import run_editor_window

    lore = _open_lore(project, project_dir, rpc, host, port, profile)
    # Dialogi „Otwórz…” i względne ścieżki plików — w katalogu projektu
    try:
        os.chdir(lore.katalog_projektu())
    except OSError:
        pass
    try:
        run_editor_window(lore, initial_files=initial_files)
    finally:
        try:
            lore.close()
        except Exception:
            pass


def main() -> None:
    from lore import __version__
    from lore.paths import default_work_dir

    default_root = default_work_dir()

    parser = argparse.ArgumentParser(
        prog="lore-editor",
        description=(
            "Lore Editor — rozdziały, panel lore, historia zmian, eksport DOCX"
        ),
        epilog=(
            "Katalog pracy: --project-dir, LORE_PROJECT_DIR, .lore-project (cwd), "
            f"albo domyślnie {default_root}. "
            "Przy pierwszym starcie: .lore-history/ ze snapshotami. "
            "Pomoc: menu Pomoc lub F1."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="Nazwa świata (domyślnie: .lore-project lub nazwa folderu)",
    )
    parser.add_argument(
        "--project-dir",
        default=None,
        metavar="DIR",
        help=(
            "Folder projektu (rozdziały + .kafd). "
            f"Domyślnie: .lore-project w cwd/rodzicach, inaczej {default_root} "
            "(../dokumenty/lore względem repo; nadpisz LORE_DEFAULT_WORK_DIR)"
        ),
    )
    parser.add_argument("--file", "-f", default=None, help="Plik do otwarcia")
    parser.add_argument(
        "--rpc",
        action="store_true",
        help="Lore przez cynober-server (TCP + protokół Karmazyn/HSL + KarminQL-RPC — nie zwykłe HTTP)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host cynober-server")
    parser.add_argument("--port", type=int, default=8080, help="Port cynober-server")
    parser.add_argument("--profile", default=None, help="Profil cynober-client")
    parser.add_argument("files", nargs="*", help="Pliki do otwarcia w kartach")
    args = parser.parse_args()

    initial: list[str] = []
    if args.file:
        initial.append(args.file)
    initial.extend(args.files)

    # Względne ścieżki plików: najpierw względem cwd wywołania, potem katalogu projektu
    project_dir = args.project_dir
    if project_dir is None and not os.environ.get("LORE_PROJECT_DIR", "").strip():
        # allow discover() to pick default; resolve file paths after open
        pass

    resolved_initial: list[str] = []
    for f in initial:
        p = Path(f).expanduser()
        if p.is_file():
            resolved_initial.append(str(p.resolve()))
        else:
            resolved_initial.append(str(p))

    _run_standalone(
        args.project,
        project_dir=project_dir,
        rpc=args.rpc,
        host=args.host,
        port=args.port,
        profile=args.profile,
        initial_files=resolved_initial,
    )


if __name__ == "__main__":
    main()