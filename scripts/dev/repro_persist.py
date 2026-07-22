#!/usr/bin/env python3
import os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.paths import ProjectPaths
from lore.backend import connect_local
from lore.store import LoreStore
from lore.types import TypLore


def dump(label, paths):
    b = connect_local(paths)
    w = b._attach()
    api = w.runtime.engine.api
    print(f"\n=== {label} ===")
    for name, bubble in sorted(api._bubble_index.items()):
        print(f"  bubble {name}:")
        for key, aid in sorted(bubble.bindings.items()):
            atom = api.store.get_atom(aid)
            folded = atom.metadata.get("_folded") if atom else None
            v = atom.metadata.get("v") if atom else None
            E = getattr(atom, "E", None) if atom else None
            S = getattr(atom, "S", None) if atom else None
            print(f"    {key} -> {aid} S={S!r} E={E!r} v={v!r} folded={folded}")
    b.close()


def cycle(tmp, label):
    paths = ProjectPaths.resolve("persist_test", tmp)
    paths.write_marker()
    lore = LoreStore.open_local(project="persist_test", project_dir=tmp)
    p = str(Path(tmp) / "rozdzial.txt")
    Path(p).write_text("hello", encoding="utf-8")
    lore.otworz_dokument(p)
    d = lore.podglad("Dok_rozdzial")
    print(f"\n[{label} przed zapisem] Typ={d.get('Typ')!r}")
    lore.zapisz()
    lore.close()
    dump(f"{label} po zapisie (reload)", paths)
    # drugi proces symulowany — nowy backend
    dump(f"{label} drugi attach", paths)


with tempfile.TemporaryDirectory() as tmp:
    cycle(tmp, "temp")

print("\n\n======== USER PROJECT ========")
paths = ProjectPaths.discover(project_dir=ROOT)
dump("user project", paths)