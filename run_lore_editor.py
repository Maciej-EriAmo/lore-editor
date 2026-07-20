#!/usr/bin/env python3
"""
Lore Editor — edytor rozdziałów z panelem lore.

    cd ~/Documents/MojaPowiesc && lore-editor
    lore-editor --project-dir .

Pierwsze uruchomienie tworzy .lore-project i .lore-history/ (snapshoty).
Pomoc: F1 w aplikacji lub lore-editor --help.
"""

from __future__ import annotations

import argparse


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
    try:
        run_editor_window(lore, initial_files=initial_files)
    finally:
        try:
            lore.close()
        except Exception:
            pass


def main() -> None:
    from lore import __version__

    parser = argparse.ArgumentParser(
        prog="lore-editor",
        description=(
            "Lore Editor — rozdziały, panel lore, historia zmian, eksport DOCX"
        ),
        epilog=(
            "Projekt: .lore-project (name=Nazwa) lub uruchom z folderu powieści. "
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
        help="Folder projektu; domyślnie cwd lub katalog z .lore-project",
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

    _run_standalone(
        args.project,
        project_dir=args.project_dir,
        rpc=args.rpc,
        host=args.host,
        port=args.port,
        profile=args.profile,
        initial_files=initial,
    )


if __name__ == "__main__":
    main()