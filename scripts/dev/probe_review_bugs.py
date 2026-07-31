"""Adversarial probes for lore-editor (dirty, restore, auth)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from lore.backend import LoreBackendError, connect_rpc, query_may_mutate
from lore.history import LoreHistoria
from lore.store import LoreStore
from lore.team_sync import ZespolLore
from lore.paths import ProjectPaths


def main() -> None:
    print(
        "ROZWIŃ mutate",
        query_may_mutate(
            'ROZWIŃ "X" PROMIEŃ 1',
            [{"status": "ok", "action": "UNFOLD"}],
        ),
    )
    print(
        "ZNAJDŹ mutate",
        query_may_mutate(
            'ZNAJDŹ GDZIE "Typ" = "Postać"',
            [{"status": "ok", "action": "FIND_WHERE"}],
        ),
    )

    with tempfile.TemporaryDirectory() as tmp:
        s = LoreStore.open_local(project="c1", project_dir=tmp)
        s.dodaj_postac("Ala")
        s.zapisz()
        n1 = len(s.lista_historii())
        s._dirty = False
        if s._backend._world is not None:
            s._backend._world.dirty = False
        s.close(zapisz_lore=True)
        s2 = LoreStore.open_local(project="c1", project_dir=tmp)
        n2 = len(s2.lista_historii())
        print("history after clean close", n1, "->", n2)
        s2.dodaj_postac("Bob")
        print("store dirty after dodaj", s2.lore_niezapisane())
        print("world dirty after dodaj", s2._backend._world.dirty)
        s2.close(zapisz_lore=False)
        s3 = LoreStore.open_local(project="c1", project_dir=tmp)
        names = s3.lista_po_typie("Postać")
        print("characters after discard close", names)
        s3.close(zapisz_lore=False)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("A", encoding="utf-8")
        (root / "w.kafd").write_bytes(b"x")
        h = LoreHistoria(root, "w")
        h.inicjalizuj()
        snap = h.utworz(label="s1", force=True)
        assert snap is not None
        (root / "b.txt").write_text("NEW", encoding="utf-8")
        h.przywroc(snap.id, strict=True)
        print("strict restore orphan gone", not (root / "b.txt").exists())

    for k in (
        "LORE_RPC_USER",
        "LORE_RPC_TOKEN",
        "CYNOBER_USER",
        "CYNOBER_TOKEN",
        "LORE_RPC_ALLOW_ANON",
        "LORE_RPC_REQUIRE_AUTH",
    ):
        os.environ.pop(k, None)
    with patch("cynober_client.connect", return_value=MagicMock()):
        try:
            connect_rpc("10.0.0.2", 8080)
            print("remote auth: FAIL")
        except LoreBackendError:
            print("remote auth: OK (raised)")
    with tempfile.TemporaryDirectory() as tmp:
        z = ZespolLore(ProjectPaths.resolve("t", tmp))
        try:
            z.ustaw_serwer("10.0.0.2", 8080)
            print("team remote: FAIL")
        except ValueError:
            print("team remote: OK (raised)")


if __name__ == "__main__":
    main()
