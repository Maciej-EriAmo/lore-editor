# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).  
**Pisarz nie widzi bazy danych** — tylko przyciski i panel boczny.

To narzędzie **pisarskie**, nie silnik gry — bez Lua, bez skryptów runtime.

## Wymagania

```bash
pip install cynober-db>=8.0.1
pip install -e .   # z katalogu lore-editor
```

Windows — jednym skryptem:

```powershell
.\scripts\install_writer.ps1 -Project MojaPowiesc
```

## Jeden folder projektu

Rozdziały i lore mogą żyć razem:

```
~/Documents/MojaPowiesc/
  rozdzial_01.txt
  rozdzial_02.md
  MojaPowiesc.kafd
  MojaPowiesc.meta.json
```

```bash
python run_lore_editor.py --project MojaPowiesc --project-dir ~/Documents/MojaPowiesc
```

Bez `--project-dir` dane trafiają do `~/.lore_editor/worlds/<projekt>/`.

## Szybki start (standalone, offline)

```bash
python run_lore_editor.py --project MojaPowiesc
```

- Lewa strona: rozdział (txt/md)
- Prawa strona: **Lore** — postacie, pomysły, wpływy przy tym rozdziale
- **Mapa powiązań** — graf wokół rozdziału lub wybranej postaci
- Zapis pliku = zapis tekstu + automatyczny zapis lore na dysk
- **Internet nie jest wymagany**

## Z AstraEdit

```bash
python run_lore_editor.py --project MojaPowiesc --astraedit rozdzial_01.txt
```

## Lore na serwerze (opcjonalnie)

Rozdziały nadal lokalnie; lore przez `cynober-server`:

```bash
cynober-server   # na hoście zespołu
python run_lore_editor.py --project MojaPowiesc --rpc --host 192.168.1.10
```

Tryb lokalny + sync plików (Wyślij / Pobierz / Synchronizuj) w panelu — gdy nie używasz `--rpc`.

## API

```python
from lore import LoreStore

lore = LoreStore.open_local("MojaPowiesc", project_dir="~/Documents/MojaPowiesc")
lore.otworz_dokument("rozdzial_07.txt")
lore.dodaj_postac("Kasia", notatka="Protagonistka")
lore.graf_powiazan("Kasia", promien=2)
lore.zapisz()
lore.close()
```

## Struktura

```
lore-editor/
  lore/
    paths.py            # jeden katalog projektu
    store.py            # LoreStore — API pisarza
    panel.py            # Panel Tkinter
    graph_view.py       # Mapa powiązań
    team_sync.py        # Sync plików (nie RPC)
    document_hooks.py   # wspólne open/save
    astraedit_loader.py # ładowanie AstraEdit
    backend.py          # Local / RPC Cynober
  run_lore_editor.py
```

## Testy

```bash
python -m unittest discover -s tests -v
```

## Licencja

MIT