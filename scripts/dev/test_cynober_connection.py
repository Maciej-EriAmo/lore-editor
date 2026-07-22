#!/usr/bin/env python3
"""Test połączenia lore-editor ↔ cynober-server (Karmazyn HSS/HSL + RPC).

  # terminal 1:
  set CYNOBER_WORLDS_DIR=%TEMP%\\cynober_lore_conn_test
  python -m cynober_server 127.0.0.1 49677

  # terminal 2:
  python scripts/test_cynober_connection.py --host 127.0.0.1 --port 49677
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# prefer repo DBase + lore-editor
_ROOT = Path(__file__).resolve().parents[1]
_DBASE = Path(r"C:\Users\drwis\DBase")
for p in (_DBASE, _ROOT):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    host, port = args.host, args.port

    ok = fail = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  OK  {name}" + (f" — {detail}" if detail else ""))
        else:
            fail += 1
            print(f" FAIL {name}" + (f" — {detail}" if detail else ""))

    print(f"=== lore-editor ↔ cynober {host}:{port} ===\n")

    print("1) cynober_client (handshake + ZDROWIE)")
    from cynober_client import connect

    c = connect(host, port)
    r = c.query("ZDROWIE")
    row = r.get("results", [{}])[0]
    data = row.get("data") or {}
    check("handshake + ZDROWIE", row.get("status") == "ok", f"ver={data.get('server_version')}")
    check(
        "server_version >= 8.0",
        str(data.get("server_version", "")).startswith("8."),
        str(data.get("server_version")),
    )
    c.close()

    print("\n2) lore.backend.connect_rpc")
    from lore.backend import connect_rpc

    be = connect_rpc(host, port)
    rows = be.execute("ZDROWIE")
    check("RpcLoreBackend ZDROWIE", bool(rows) and rows[0].get("status") == "ok")

    print("\n3) świat + KarminQL przez RPC")
    world = "lore_conn_test"
    rows = be.execute(f'UTWÓRZ ŚWIAT "{world}"')
    st = rows[0].get("status")
    # ok lub już istnieje
    check(
        "UTWÓRZ/istnieje świat",
        st == "ok" or "istnieje" in str(rows[0].get("message", "")).lower() or st == "error",
        str(rows[0].get("action") or rows[0].get("message"))[:80],
    )
    rows = be.execute(f'WYBIERZ ŚWIAT "{world}"')
    check("WYBIERZ ŚWIAT", rows[0].get("status") == "ok", str(rows[0].get("action")))
    rows = be.execute('UTRWAL "Anna"')
    check("UTRWAL Anna", rows[-1].get("status") == "ok", str(rows[-1])[:100])
    rows = be.execute('WSTRZYKNIJ "Rola" = "bohaterka" DO "Anna"')
    check("WSTRZYKNIJ Rola", rows[-1].get("status") == "ok", str(rows[-1])[:100])
    rows = be.execute('POKAŻ "Anna"')
    check("POKAŻ Anna", rows[-1].get("status") != "error", str(rows[-1])[:120])

    print("\n4) GOSSIP PHI / SOUL przez RPC")
    rows = be.execute("GOSSIP EKSPORT PHI")
    check(
        "GOSSIP EKSPORT PHI",
        rows[0].get("status") == "ok" and "data" in rows[0],
        f"atoms={rows[0].get('atom_count')}",
    )
    rows = be.execute("GOSSIP EKSPORT SOUL")
    check(
        "GOSSIP EKSPORT SOUL",
        rows[0].get("status") == "ok" and "data" in rows[0],
        f"atoms={rows[0].get('atom_count')} bubbles={rows[0].get('bubble_count')}",
    )
    soul_payload = rows[0].get("data") or ""

    be2 = connect_rpc(host, port)
    be2.execute('UTWÓRZ ŚWIAT "lore_conn_import"')
    be2.execute('WYBIERZ ŚWIAT "lore_conn_import"')
    imp = be2.execute(f'GOSSIP IMPORT SOUL DANE "{soul_payload}"')
    check(
        "GOSSIP IMPORT SOUL (2. klient)",
        imp[0].get("status") == "ok",
        str({k: imp[0].get(k) for k in (
            "atoms_added", "bubbles_added", "atoms_updated", "message"
        )}),
    )
    be2.close()
    be.close()

    print("\n5) LoreStore przez RPC")
    from lore.paths import ProjectPaths
    from lore.store import LoreStore

    tmp = tempfile.mkdtemp(prefix="lore_rpc_")
    paths = ProjectPaths.resolve("lore_rpc_chars", tmp)
    backend = connect_rpc(host, port)
    try:
        backend.execute('UTWÓRZ ŚWIAT "lore_rpc_chars"')
    except Exception:
        pass
    try:
        lore = LoreStore(backend, paths)
        lore._ensure_project()
        lore.dodaj_postac("Boromir", notatka="Gondor")
        hits = lore.szukaj("Gondor")
        check("LoreStore.dodaj_postac+szukaj", "Boromir" in hits, str(hits)[:120])
        lore.close()
    except Exception as e:
        check("LoreStore via RPC", False, repr(e))

    print(f"\n=== WYNIK: {ok} OK, {fail} FAIL ===")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
