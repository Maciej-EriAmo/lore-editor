"""Probe: does LocalLoreBackend mark world dirty on read-only queries?"""
from __future__ import annotations

import tempfile

from lore.store import LoreStore


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        s = LoreStore.open_local(project="bugtest", project_dir=tmp)
        s._dirty = False
        w = s._backend._world
        if w is not None:
            w.dirty = False
        s._run_line("STATYSTYKI", strict=False)
        w = s._backend._world
        print("after STATYSTYKI world.dirty =", getattr(w, "dirty", None))
        print("after STATYSTYKI store._dirty =", s._dirty)
        if w is not None:
            w.dirty = False
        s._dirty = False
        s._run_line('ZNAJDŹ GDZIE "Typ" = "Postać"', strict=False)
        w = s._backend._world
        print("after ZNAJDŹ world.dirty =", getattr(w, "dirty", None))
        row = s._run_line('ROZWIŃ "X" PROMIEŃ 1', strict=False)
        print("ROZWIŃ (missing seed) status =", row.get("status"), row.get("action"))
        s.close(zapisz_lore=False)


if __name__ == "__main__":
    main()
