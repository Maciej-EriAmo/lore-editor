# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).  
**Pisarz nie widzi bazy danych** — tylko przyciski i panel boczny.

## Wymagania

```bash
pip install cynober-db>=8.0.1
pip install -e .   # z katalogu lore-editor
```

## Szybki start (standalone)

```bash
python run_lore_editor.py --project MojaPowiesc
```

- Lewa strona: rozdział (txt/md)
- Prawa strona: **Lore** — postacie, pomysły, wpływy przy tym rozdziale
- Zapis pliku = zapis tekstu + automatyczny zapis lore na dysk

Dane lore: `~/.lore_editor/worlds/<projekt>/` (format Cynober `.kafd` + shardy).

## Z AstraEdit

```bash
set ASTRAEDIT_PATH=C:\Users\...\Documents\AstraEdit
python run_lore_editor.py --project MojaPowiesc --astraedit rozdzial_01.txt
```

Menu **Lore** w AstraEdit: odśwież panel, zapisz projekt.

## API (dla integracji — nie dla pisarza)

```python
from lore import LoreStore

lore = LoreStore.open_local("MojaPowiesc")
lore.otworz_dokument("/ścieżka/rozdzial_07.txt")
lore.dodaj_postac("Kasia", notatka="Protagonistka")
lore.wklej_pomysl_do_dokumentu("Koniec aktu II — zdrada")
lore.polacz("Tolkien", "Kasia", "inspiruje")
lore.powiaz_z_dokumentem("Kasia")
lore.zapisz()
lore.close()
```

## Co robi pod spodem (ukryte)

| Pisarz klika | Cynober (niewidoczne) |
|--------------|------------------------|
| + Postać | `UTRWAL` + `WSTRZYKNIJ Typ=Postać` |
| + Pomysł | bąbel Pomysł + `POŁĄCZ` z dokumentem |
| Powiąż z rozdziałem | `rel:wystepuje_w` w grafie |
| Połącz z… | `POŁĄCZ JAKO wplywa_na` / `koliguje_z` |
| Zapisz | `ZAPISZ ŚWIAT` + plik tekstowy |

## Testy

```bash
python -m unittest discover -s tests -v
```

## Struktura

```
lore-editor/
  lore/
    store.py          # LoreStore — API pisarza
    panel.py          # Panel Tkinter
    backend.py        # Local / RPC Cynober
    astraedit_bridge.py
  run_lore_editor.py
```

## Licencja

MIT