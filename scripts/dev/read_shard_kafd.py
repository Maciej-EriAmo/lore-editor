#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import karmazyn_kernel as kernel
import karmazyn_store

shard = ROOT / "shards" / "lore-editor" / "region_0.kafd"
manifest = ROOT / "lore-editor.kafd"

for label, path in [("manifest", manifest), ("shard", shard)]:
    print(f"\n=== {label}: {path.name} ({path.stat().st_size} B) ===")
    store = kernel.Store(thermal=True)
    n = karmazyn_store.load_documents(store, str(path), proca_index=None)
    print(f"  loaded {n} atoms")
    for a in store.reg.atoms():
        if a.S == "__bubble__":
            print(f"  {a.id} __bubble__ E={a.E!r} bindings={a.metadata.get('bindings')}")
        else:
            print(f"  {a.id} S={a.S!r} E={a.E!r} v={a.metadata.get('v')!r}")