#!/usr/bin/env python3
"""Repro: dwa dokumenty → korupcja bindingów po zapisie."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.backend import connect_local
from lore.paths import ProjectPaths
from lore.store import LoreStore


def dump_bindings(paths: ProjectPaths, label: str) -> None:
    backend = connect_local(paths)
    world = backend._attach()
    api = world.runtime.engine.api
    print(f"\n=== {label} ===")
    for name, bubble in sorted(api._bubble_index.items()):
        print(f"{name}: {dict(bubble.bindings)}")
        for key, aid in sorted(bubble.bindings.items()):
            if key.startswith("hist:"):
                continue
            atom = api.store.get_atom(aid)
            if atom is None:
                print(f"  {key} -> {aid}: MISSING")
                continue
            print(
                f"  {key} -> {aid}: S={atom.S!r} E={atom.E!r} "
                f"v={atom.metadata.get('v')!r} folded={atom.metadata.get('_folded')}"
            )
    backend.close()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "rozdzial.txt").write_text("a", encoding="utf-8")
        (work / "rozdzial2.txt").write_text("b", encoding="utf-8")
        paths = ProjectPaths.resolve("test", work)
        paths.write_marker()
        p1 = str(work / "rozdzial.txt")
        p2 = str(work / "rozdzial2.txt")

        lore = LoreStore.open_local(project="test", project_dir=work)
        lore.otworz_dokument(p1)
        dump_bindings(paths, "po dok1 (przed zapisem)")

        lore.zapisz()
        lore.close()
        dump_bindings(paths, "po zapisie dok1 (reload)")

        lore = LoreStore.open_local(project="test", project_dir=work)
        lore.otworz_dokument(p2)
        dump_bindings(paths, "po dok2 (przed zapisem)")

        lore.zapisz()
        lore.close()
        dump_bindings(paths, "po zapisie obu (reload)")

        lore = LoreStore.open_local(project="test", project_dir=work)
        for name in ("Dok_rozdzial", "Dok_rozdzial2"):
            print(f"podglad {name}:", lore.podglad(name))
        lore.close()


if __name__ == "__main__":
    main()