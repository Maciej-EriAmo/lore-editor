#!/usr/bin/env python3
"""
Test Zespół: PUSH / PULL / SYNC świata lore ↔ cynober-server.

  # terminal 1 — serwer (osobny katalog światów):
  set CYNOBER_WORLDS_DIR=%TEMP%\\cynober_team_server
  set CYNOBER_SHARDED=0
  python -m cynober_server 127.0.0.1 49777

  # terminal 2:
  python scripts/test_team_replicate.py --host 127.0.0.1 --port 49777
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DBASE = Path(r"C:\Users\drwis\DBase")
for p in (_DBASE, _ROOT):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

# Lore pack: bez shardów
os.environ.setdefault("CYNOBER_SHARDED", "0")
os.environ.setdefault("CYNOBER_LAZY_LOAD", "0")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    host, port = args.host, int(args.port)

    ok = fail = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  OK  {name}" + (f" — {detail}" if detail else ""))
        else:
            fail += 1
            print(f" FAIL {name}" + (f" — {detail}" if detail else ""))

    print(f"=== Zespół PUSH/PULL/SYNC  {host}:{port} ===\n")

    from lore.backend import LocalLoreBackend
    from lore.paths import ProjectPaths
    from lore.store import LoreStore
    from lore.team_sync import ZespolLore
    from cynober_client import connect
    from cynober_worlds import _kafd_path

    work_a = Path(tempfile.mkdtemp(prefix="lore_team_a_"))
    work_b = Path(tempfile.mkdtemp(prefix="lore_team_b_"))
    project = "team_lore_demo"
    print(f"Pisarz A: {work_a}")
    print(f"Pisarz B: {work_b}\n")

    # ── A: lokalny projekt + zapis na dysk ─────────────────────────────────
    print("1) Pisarz A — lokalny graf + zapisz()")
    paths_a = ProjectPaths.resolve(project, work_a)
    backend_a = LocalLoreBackend(paths_a)
    lore_a = LoreStore(backend_a, paths_a)
    lore_a._ensure_project()
    lore_a.dodaj_postac("Frodo", notatka="Pierścień")
    lore_a.dodaj_postac("Sam", notatka="Ogrodnik")
    lore_a.zapisz()
    kafd_a = paths_a.root / f"{project}.kafd"
    check("A: plik .kafd po zapisz()", kafd_a.is_file(), str(kafd_a))
    hits_a = lore_a.szukaj("Pierścień")
    check("A: szukaj Frodo lokalnie", "Frodo" in hits_a, str(hits_a))
    lore_a.close()

    # ── PUSH na serwer ─────────────────────────────────────────────────────
    print("\n2) PUSH — A → cynober-server")
    zespol_a = ZespolLore(paths_a)
    try:
        wynik = zespol_a.wyslij_na_serwer(host, port)
        check("A: wyslij_na_serwer", wynik.ok, wynik.komunikat)
        check("A: kierunek push", wynik.kierunek == "push", wynik.kierunek)
    except Exception as e:
        check("A: wyslij_na_serwer", False, repr(e))
        print(f"\n=== WYNIK: {ok} OK, {fail} FAIL (przerwane) ===")
        return 1

    # weryfikacja po stronie serwera (RPC — inna sesja, ten sam dysk światów)
    print("\n3) Serwer — świat widoczny po IMPORT")
    c = connect(host, port)
    try:
        r = c.query("LISTA ŚWIATÓW")
        row = r.get("results", [{}])[0]
        worlds = row.get("worlds") or []
        names = [w.get("name") if isinstance(w, dict) else w for w in worlds]
        check("serwer: LISTA ŚWIATÓW zawiera projekt", project in names, str(names)[:200])
        r = c.query(f'WYBIERZ ŚWIAT "{project}"')
        check("serwer: WYBIERZ ŚWIAT", r.get("results", [{}])[0].get("status") == "ok")
        r = c.query('POKAŻ "Frodo"')
        row = r.get("results", [{}])[-1]
        check(
            "serwer: POKAŻ Frodo",
            row.get("status") == "ok",
            str(row.get("data") or row.get("message"))[:120],
        )
    except Exception as e:
        check("serwer: weryfikacja", False, repr(e))
    finally:
        c.close()

    # ── PULL na maszynę B (pusty katalog) ──────────────────────────────────
    print("\n4) PULL — serwer → pisarz B (pusty katalog)")
    paths_b = ProjectPaths.resolve(project, work_b)
    # stub .lore-project / katalog
    paths_b.root.mkdir(parents=True, exist_ok=True)
    (paths_b.root / ".lore-project").write_text(project, encoding="utf-8")
    zespol_b = ZespolLore(paths_b)
    try:
        wynik = zespol_b.pobierz_z_serwera(host, port)
        check("B: pobierz_z_serwera", wynik.ok, wynik.komunikat)
        kafd_b = paths_b.root / f"{project}.kafd"
        check("B: .kafd po PULL", kafd_b.is_file(), str(kafd_b))
    except Exception as e:
        check("B: pobierz_z_serwera", False, repr(e))
        print(f"\n=== WYNIK: {ok} OK, {fail} FAIL ===")
        return 1

    backend_b = LocalLoreBackend(paths_b)
    lore_b = LoreStore(backend_b, paths_b)
    lore_b._ensure_project()
    hits_b = lore_b.szukaj("Pierścień")
    check("B: szukaj Frodo po PULL", "Frodo" in hits_b, str(hits_b))
    hits_sam = lore_b.szukaj("Ogrodnik")
    check("B: szukaj Sam po PULL", "Sam" in hits_sam, str(hits_sam))

    # ── B dodaje postać, PUSH, A PULL/SYNC ─────────────────────────────────
    print("\n5) B edytuje → PUSH → A SYNC")
    lore_b.dodaj_postac("Gandalf", notatka="Szary")
    lore_b.zapisz()
    # nowszy modified_at
    time.sleep(1.05)
    lore_b.zapisz()
    lore_b.close()

    try:
        wynik = zespol_b.wyslij_na_serwer(host, port)
        check("B: push po edycji", wynik.ok, wynik.komunikat)
    except Exception as e:
        check("B: push po edycji", False, repr(e))

    # A synchronizuje (powinien pull jeśli serwer nowszy)
    try:
        wynik = zespol_a.synchronizuj(host, port)
        check("A: synchronizuj", wynik.ok, f"{wynik.kierunek}: {wynik.komunikat}")
    except Exception as e:
        check("A: synchronizuj", False, repr(e))

    backend_a2 = LocalLoreBackend(paths_a)
    lore_a2 = LoreStore(backend_a2, paths_a)
    lore_a2._ensure_project()
    hits_g = lore_a2.szukaj("Szary")
    check("A: ma Gandalfa po SYNC", "Gandalf" in hits_g, str(hits_g))
    lore_a2.close()

    # ── SYNC gdy równe ─────────────────────────────────────────────────────
    print("\n6) SYNC gdy już zsynchronizowane")
    try:
        wynik = zespol_a.synchronizuj(host, port)
        check(
            "A: SYNC direction none lub push/pull",
            wynik.ok and wynik.kierunek in ("none", "push", "pull"),
            f"{wynik.kierunek}: {wynik.komunikat}",
        )
    except Exception as e:
        check("A: SYNC idle", False, repr(e))

    print(f"\n=== WYNIK: {ok} OK, {fail} FAIL ===")
    if fail == 0:
        print("Replikacja pliku świata (.kafd) po RPC działa (PUSH/PULL/SYNC).")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
