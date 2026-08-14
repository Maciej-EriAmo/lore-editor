#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weryfikacja toru mediów lore-editor:

  1) Lokalnie: plik → LoreStore.dodaj_media → zapisz → reopen → lista/odczyt
  2) RPC (opcjonalnie): put_media / MEDIA LIST / get_media gdy serwer na :8080

Użycie:
  python scripts/dev/verify_media_pipeline.py
  python scripts/dev/verify_media_pipeline.py --rpc 127.0.0.1:8080
  python scripts/dev/verify_media_pipeline.py --rpc 127.0.0.1:8080 --user u --token t
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

_MIN_PNG = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D,
        0xB0, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ]
)


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL {msg}")


def verify_local() -> bool:
    print("== 1) Lokalnie (LoreStore → .kafd) ==")
    from lore.store import LoreStore

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "VerifyMedia"
        root.mkdir()
        (root / ".lore-project").write_text("name=VerifyMedia\n", encoding="utf-8")
        png = root / "t.png"
        png.write_bytes(_MIN_PNG)
        st = LoreStore.open_local(project_dir=root)
        st.dodaj_postac("Tester")
        info = st.dodaj_media("Tester", "portret", png)
        st.zapisz()
        st._backend.close(flush=False)
        st2 = LoreStore.open_local(project_dir=root)
        listed = st2.lista_mediow("Tester")
        if not listed:
            _fail("lista_mediow pusta po reopen")
            return False
        _ok(f"lista_mediow={listed}")
        data, mime = st2.odczyt_media("Tester", "portret")
        if data != _MIN_PNG:
            _fail(f"odczyt mismatch size={len(data)} mime={mime}")
            return False
        _ok(f"odczyt {len(data)} B mime={mime} atom={info.get('atom_id')}")
    return True


def verify_rpc(host: str, port: int, user: str, token: str) -> bool:
    print(f"== 2) RPC {host}:{port} (KAFS put/list/get) ==")
    try:
        from cynober_client import CynoberClient, CynoberClientError
    except ImportError as e:
        _fail(f"brak cynober_client: {e}")
        return False

    client = CynoberClient()
    try:
        client.connect(host, port, user=user or None, token=token or None)
    except Exception as e:
        _fail(f"connect: {e}")
        return False

    info = {}
    if hasattr(client, "session_info"):
        try:
            info = client.session_info() or {}
        except Exception:
            info = {
                "kafs_enabled": getattr(client, "kafs_enabled", False),
            }
    else:
        info = {"kafs_enabled": getattr(client, "kafs_enabled", False)}
    print(f"  session kafs_enabled={info.get('kafs_enabled')} info={info}")

    if not getattr(client, "kafs_enabled", False):
        _fail("kafs-stream nie wynegocjowany — put_media nie zadziała")
        client.close()
        return False

    # Świat tymczasowy na serwerze — użyj istniejącego profilu / domyślnego
    atom_id = "m_verify_lore_portret"
    bubble = "VerifyMediaNPC"
    try:
        # upewnij się że jest świat (best-effort)
        try:
            client.query_line('LISTA ŚWIATÓW')
        except Exception:
            pass
        end = client.put_media(
            atom_id,
            _MIN_PNG,
            mime="image/png",
            bubble=bubble,
            binding="portret",
        )
        if not isinstance(end, dict) or end.get("status") != "ok":
            _fail(f"put_media: {end}")
            return False
        _ok(f"put_media → {end}")

        row = client.query_line(f'MEDIA LIST "{bubble}"')
        media = (row or {}).get("media") or []
        if not media:
            _fail(f"MEDIA LIST pusta: {row}")
            return False
        _ok(f"MEDIA LIST → {media}")

        data, mime, meta = client.get_media(atom_id)
        if data != _MIN_PNG:
            _fail(f"get_media mismatch len={len(data)} meta={meta}")
            return False
        _ok(f"get_media {len(data)} B mime={mime}")
    except CynoberClientError as e:
        _fail(str(e))
        return False
    except Exception as e:
        _fail(f"{type(e).__name__}: {e}")
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Weryfikacja mediów lore-editor")
    p.add_argument("--rpc", default="", help="host:port serwera Cynober (opcjonalnie)")
    p.add_argument("--user", default="", help="RPC user")
    p.add_argument("--token", default="", help="RPC token")
    args = p.parse_args(argv)

    # repo root na path
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    ok = verify_local()
    if args.rpc:
        host, _, port_s = args.rpc.partition(":")
        port = int(port_s or "8080")
        ok = verify_rpc(host or "127.0.0.1", port, args.user, args.token) and ok
    else:
        print("== 2) RPC pominięte (podaj --rpc host:port) ==")
        print("  DBase unit: python -m unittest tests.test_media_kafs_rpc")

    print()
    print("WYNIK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
