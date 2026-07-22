#!/usr/bin/env python3
"""Audyt lore-editor.meta.json vs runtime Cynober."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.store import LoreStore
from lore.types import TypLore


def load_meta() -> dict:
    p = ROOT / "lore-editor.meta.json"
    return json.loads(p.read_text(encoding="utf-8"))


def audit_indexes(meta: dict) -> list[str]:
    issues: list[str] = []
    qi = meta.get("query_indexes", {})
    inv = qi.get("inv_index", {})
    atom = qi.get("atom_index", {})
    si = meta.get("shard_index", {})
    regions = si.get("regions", [])

    shard_atoms: set[str] = set()
    shard_bubbles: set[str] = set()
    for r in regions:
        shard_atoms.update(r.get("atoms", []))
        shard_bubbles.update(r.get("bubbles", []))

    for atom_id, bubbles in atom.items():
        if not bubbles:
            issues.append(f"atom_index: {atom_id} → pusta lista")
        for b in bubbles:
            if b not in shard_bubbles:
                issues.append(f"atom_index: {atom_id} wskazuje na {b}, brak w shard_index")

    for atom_id in shard_atoms:
        if atom_id not in atom:
            issues.append(f"shard atom {atom_id} brak w atom_index")

    orphan_atoms = set(atom) - shard_atoms
    for a in sorted(orphan_atoms):
        issues.append(f"osierocony atom_index: {a} → {atom[a]}")

    typ_inv = inv.get("Typ", {})
    for val, bubbles in typ_inv.items():
        if val.endswith(".txt"):
            issues.append(f'inv_index Typ: wartość wygląda jak plik: "{val}" → {bubbles}')
        for b in bubbles:
            if b.startswith("Dok_") and val != TypLore.DOKUMENT.value:
                issues.append(f'inv_index Typ: Dokument {b} ma Typ="{val}" zamiast Dokument')

    notatka_inv = inv.get("Notatka", {})
    for val, bubbles in notatka_inv.items():
        if val.endswith(".txt"):
            issues.append(f'inv_index Notatka: wartość wygląda jak plik: "{val}" → {bubbles}')

    plik_inv = inv.get("Plik", {})
    for plik, docs in plik_inv.items():
        expected = {f"Dok_{plik.replace('.', '_')}"}
        if plik == "rozdzial.txt":
            expected = {"Dok_rozdzial"}
        elif plik == "rozdzial2.txt":
            expected = {"Dok_rozdzial2"}
        if set(docs) != expected:
            issues.append(f"inv_index Plik: {plik} → {docs}, oczekiwano ~{expected}")

    idx_path = ROOT / "shards" / "lore-editor" / "index.json"
    if idx_path.is_file():
        shard_idx = json.loads(idx_path.read_text(encoding="utf-8"))
        if shard_idx != si:
            issues.append("shard_index w meta ≠ shards/lore-editor/index.json")
    else:
        issues.append(f"brak {idx_path}")

    return issues


def audit_runtime(store: LoreStore) -> dict:
    report: dict = {}
    bubbles = store.wszystkie_wpisy()
    report["wszystkie_wpisy"] = bubbles

    for name in bubbles:
        data = store.podglad(name)
        report[name] = {
            k: v for k, v in data.items() if k not in ("_relations",)
        }
        report[name]["_relations"] = data.get("_relations", [])

    for path in [ROOT / "rozdzial.txt", ROOT / "rozdzial2.txt"]:
        doc = store.otworz_dokument(str(path))
        report[f"lore@{path.name}"] = {
            "doc": doc,
            "powiazane": store.lore_przy_dokumencie(str(path)),
            "sasiedzi": store.sasiedzi(doc, promien=1),
        }

    report["lista_Postac"] = store.lista_po_typie(TypLore.POSTAĆ)
    report["lista_Dokument"] = store.lista_po_typie(TypLore.DOKUMENT)

    runtime_issues: list[str] = []
    adam = report.get("Adam", {})
    if adam.get("Typ") != TypLore.POSTAĆ.value:
        runtime_issues.append(f"Adam.Typ = {adam.get('Typ')!r}, oczekiwano {TypLore.POSTAĆ.value!r}")
    notatka = adam.get("Notatka", "")
    if notatka.endswith(".txt") or notatka == "rozdzial.txt":
        runtime_issues.append(f"Adam.Notatka = {notatka!r} — wygląda na ścieżkę pliku")

    for doc_key in ("lore@rozdzial.txt", "lore@rozdzial2.txt"):
        info = report.get(doc_key, {})
        if "Adam" not in [x["nazwa"] for x in info.get("powiazane", [])]:
            runtime_issues.append(f"Adam nie powiązany z {doc_key}")

    report["runtime_issues"] = runtime_issues
    return report


def main() -> int:
    meta = load_meta()
    index_issues = audit_indexes(meta)

    store = LoreStore.open_local(project_dir=ROOT)
    runtime = audit_runtime(store)
    store.close()

    print("=== META (lore-editor.meta.json) ===")
    print(f"bubbles: {meta.get('bubbles')}, shard_regions: {meta.get('shard_regions')}")
    print()

    print("=== PROBLEMY INDEKSÓW (meta) ===")
    if index_issues:
        for i in index_issues:
            print(f"  ✗ {i}")
    else:
        print("  ✓ brak")
    print()

    print("=== RUNTIME (Cynober) ===")
    for name in runtime.get("wszystkie_wpisy", []):
        d = runtime.get(name, {})
        rels = d.get("_relations", [])
        props = {k: v for k, v in d.items() if k != "_relations"}
        print(f"  {name}: {props}")
        if rels:
            for r in rels:
                print(f"    → {r}")
    print()

    for key in ("lore@rozdzial.txt", "lore@rozdzial2.txt"):
        info = runtime.get(key, {})
        print(f"=== {key} ===")
        print(f"  doc={info.get('doc')}, sasiedzi={info.get('sasiedzi')}")
        for it in info.get("powiazane", []):
            print(f"    {it['typ']:<10} {it['nazwa']}: {it['opis'][:60]}")
        print()

    print("=== PROBLEMY RUNTIME ===")
    ri = runtime.get("runtime_issues", [])
    if ri:
        for i in ri:
            print(f"  ✗ {i}")
    else:
        print("  ✓ brak")
    print()

    print("=== TYPY ===")
    print(f"  Postać: {runtime.get('lista_Postac')}")
    print(f"  Dokument: {runtime.get('lista_Dokument')}")

    return 1 if (index_issues or ri) else 0


if __name__ == "__main__":
    raise SystemExit(main())