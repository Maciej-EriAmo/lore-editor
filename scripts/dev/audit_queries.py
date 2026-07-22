import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lore.paths import ProjectPaths
from lore.backend import connect_local
paths = ProjectPaths.discover(project_dir=ROOT)
b = connect_local(paths)
for name in ["Adam", "Dok_rozdzial", "Dok_rozdzial2"]:
    r = b.execute(f'POKAŻ "{name}"', strict=False)[-1]
    print(name, r.get("ok"), r.get("error"))
row = b.execute('ZNAJDŹ GDZIE "BĄBEL" = "Adam"', strict=False)[-1]
print("BĄBEL Adam:", row.get("matches"))
row2 = b.execute('ZNAJDŹ GDZIE "Typ" = "rozdzial.txt"', strict=False)[-1]
print("Typ=rozdzial.txt:", row2.get("matches"))
b.close()