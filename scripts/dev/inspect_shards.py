#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lore.paths import ProjectPaths
from lore.backend import connect_local

paths = ProjectPaths.discover(project_dir=ROOT)
b = connect_local(paths)
w = b._attach()
api = w.runtime.engine.api
store = w.runtime.bridge.store

print("folded_atoms:", w.runtime.folded_atoms)
print("shard_index:", w.runtime.shard_index)

for aid in ["a0", "a2", "a5"]:
    atom = store.get_atom(aid)
    if atom:
        print(f"\n{aid}: S={atom.S!r} E={atom.E!r} T={atom.T} meta={atom.metadata}")
    else:
        print(f"\n{aid}: MISSING")

# unfold
from cynober_worlds import unfold_runtime
with w.runtime.lock:
    u = unfold_runtime(w.runtime, ["Dok_rozdzial"], radius=1)
print("\nunfold:", u)

for aid in ["a0", "a2", "a5"]:
    atom = store.get_atom(aid)
    if atom:
        print(f"after unfold {aid}: S={atom.S!r} E={atom.E!r} v={atom.metadata.get('v')!r}")

b.close()