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
    *,
    rpc_user: str | None = None,
    rpc_token: str | None = None,
):
    from lore.store import LoreStore

    if rpc:
        return LoreStore.open_rpc(
            project,
            host=host,
            port=port,
            profile=profile,
            project_dir=project_dir,
            user=rpc_user,
            token=rpc_token,
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
    rpc_user: str | None = None,
    rpc_token: str | None = None,
) -> None:
    from lore.editor_window import run_editor_window

    from lore.paths import save_last_work_dir

    lore = _open_lore(
        project,
        project_dir,
        rpc,
        host,
        port,
        profile,
        rpc_user=rpc_user,
        rpc_token=rpc_token,
    )
    # Dialogi „Otwórz…” i względne ścieżki plików — w katalogu projektu
    try:
        os.chdir(lore.katalog_projektu())
    except OSError:
        pass
    save_last_work_dir(lore.katalog_projektu())
    try:
        run_editor_window(lore, initial_files=initial_files)
    finally:
        try:
            # GUI zwykle już zamknęło store; drugi close jest no-op / bezpieczny
            if getattr(lore, "_backend", None) is not None:
                lore.close(zapisz_lore=False)
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
    parser.add_argument(
        "--rpc-user",
        default=None,
        help="Login RPC (auth.json); albo LORE_RPC_USER / profil user",
    )
    parser.add_argument(
        "--rpc-token",
        default=None,
        help="Token RPC; albo LORE_RPC_TOKEN / profil token",
    )
    parser.add_argument(
        "--locale",
        default=None,
        metavar="CODE",
        help="Język UI: pl, en, tlh, … (pluginy: docs/PLUGINY_JEZYKOWE.md)",
    )
    parser.add_argument("files", nargs="*", help="Pliki do otwarcia w kartach")
    args = parser.parse_args()

    from lore.i18n import discover_and_load, set_locale

    discover_and_load()
    if args.locale:
        try:
            set_locale(args.locale, persist=True)
        except KeyError as e:
            raise SystemExit(f"[!] {e}") from e

    initial: list[str] = []
    if args.file:
        initial.append(args.file)
    initial.extend(args.files)

    project_dir = args.project_dir

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
        rpc_user=args.rpc_user,
        rpc_token=args.rpc_token,
    )


if __name__ == "__main__":
    main()