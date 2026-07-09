# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).  
**Pisarz nie widzi bazy danych** — tylko przyciski i panel boczny.

## Wymagania

```bash
pip install cynober-db>=8.0.1
pip install -e .   # z katalogu lore-editor
```

Windows — jednym skryptem:

```powershell
.\scripts\install_writer.ps1 -Project MojaPowiesc
```

Instalator: `cynober-db`, `lore-editor`, klon AstraEdit do `vendor/`, skrót na pulpicie.

## Szybki start (standalone)

```bash
python run_lore_editor.py --project MojaPowiesc
```

- Lewa strona: rozdział (txt/md)
- Prawa strona: **Lore** — postacie, pomysły, wpływy przy tym rozdziale
- **Mapa powiązań** — graf wokół rozdziału lub wybranej postaci
- Zapis pliku = zapis tekstu + automatyczny zapis lore na dysk

Dane lore: `~/.lore_editor/worlds/<projekt>/` (format Cynober `.kafd` + shardy).

## Z AstraEdit

```bash
python run_lore_editor.py --project MojaPowiesc --astraedit rozdzial_01.txt
```

Ładuje AstraEdit z `vendor/Astraedit/` (po instalatorze), lokalnej kopii lub `ASTRAEDIT_PATH`.

Menu **Lore** w AstraEdit: odśwież panel, zapisz projekt.

## Zespół (cynober-server)

Na komputerze „serwerowym” uruchom:

```bash
cynober-server
```

W panelu Lore wpisz adres (np. `192.168.1.10`) i port (`8080`):

| Przycisk | Działanie |
|----------|-----------|
| Wyślij | Lokalny projekt → serwer |
| Pobierz | Serwer → lokal (nadpisuje) |
| Synchronizuj | Nowsza wersja wygrywa |

## API (dla integracji — nie dla pisarza)

```python
from lore import LoreStore

lore = LoreStore.open_local("MojaPowiesc")
lore.otworz_dokument("/ścieżka/rozdzial_07.txt")
lore.dodaj_postac("Kasia", notatka="Protagonistka")
lore.wklej_pomysl_do_dokumentu("Koniec aktu II — zdrada")
lore.polacz("Tolkien", "Kasia", "inspiruje")
lore.powiaz_z_dokumentem("Kasia")
lore.graf_powiazan("Kasia", promien=2)
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
| Mapa powiązań | `ROZWIJ` + `POKAŻ` relacji |
| Wyślij / Pobierz | `push_world` / `pull_world` przez TCP |
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
    panel.py          # Panel Tkinter + zespół
    graph_view.py     # Mapa powiązań
    team_sync.py      # Sync przez cynober-server
    backend.py        # Local / RPC Cynober
    astraedit_bridge.py
  scripts/install_writer.ps1
  run_lore_editor.py
```

## Licencja

MIT