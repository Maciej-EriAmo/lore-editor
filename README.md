# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).

Narzędzie **pisarskie** (offline-first) — bez Lua, bez silnika gry.

## Instalacja

```bash
pip install cynober-db>=8.0.1
pip install -e .
```

Windows:

```powershell
.\scripts\install_writer.ps1 -Project MojaPowiesc
```

## Projekt — zero konfiguracji

**Opcja A:** uruchom z folderu powieści — cwd = projekt:

```powershell
cd ~/Documents/MojaPowiesc
lore-editor
```

Nazwa projektu = nazwa folderu (np. `MojaPowiesc`).

**Opcja B:** plik `.lore-project` w katalogu:

```
name=MojaPowiesc
```

Edytor szuka pliku w cwd i katalogach nadrzędnych.

**Opcja C:** jawnie:

```bash
lore-editor --project-dir ~/Documents/MojaPowiesc
```

Przy pierwszym uruchomieniu tworzy się `.lore-project` i pliki `.kafd`.

## Layout folderu

```
MojaPowiesc/
  .lore-project
  rozdzial_01.txt
  rozdzial_02.md
  MojaPowiesc.kafd    # całe lore + indeksy (Lore Pack, jeden plik)
```

Stary format (`*.meta.json` + `shards/`) jest automatycznie migrowany przy zapisie.

## Uruchomienie

```bash
lore-editor                              # z katalogu projektu
lore-editor --file rozdzial_01.txt       # jeden plik
lore-editor rozdzial_01.txt rozdzial_02.md   # kilka kart
lore-editor --rpc --host 192.168.1.10    # lore na serwerze
```

### Edytor tekstu

- **Karty** — wiele plików naraz; zamknij: `×` na karcie, `Ctrl+W`, środkowy przycisk myszy
- **Plik** — Nowy, Otwórz, Zapisz, Zapisz jako…
- **Edycja** — Cofnij/Ponów, Znajdź (`Ctrl+F`), przełącz zawijanie wierszy
- **Skróty** — `Ctrl+N` `Ctrl+O` `Ctrl+S` `Ctrl+Shift+S` `Ctrl+W` `Ctrl+F`
- **Status** — liczba słów i znaków, kodowanie pliku
- **Autosave** — co 60 s (tylko pliki już zapisane na dysku)
- **Wygląd** — presety czcionek (szkic, druk, czytelność), rozmiar 11–12 pt, interlinia 1,0 / 1,5

### Panel lore (zakładki Rozdział · Szukaj · Zespół)

**Ważne:** powiązania z rozdziałem wymagają **otwartego pliku** w edytorze (karta z zapisaną lub otwartą ścieżką na dysku).

#### Dodawanie wpisów

| Przycisk | Co robi |
|----------|---------|
| **+ Postać** | Tworzy postać; jeśli masz otwarty rozdział — automatycznie go powiązuje |
| **+ Pomysł** | Zapisuje myśl i wiąże z otwartym rozdziałem |
| **+ Wpływ** | Dodaje inspirację (np. autor, mit) i wiąże z rozdziałem |

#### Powiązania z rozdziałem

| Akcja | Kiedy użyć |
|-------|------------|
| **Powiąż z rozdziałem** | Wybierz wpis z listy (lub otwórz dialog, gdy lista pusta) |
| **Powiąż inny wpis…** | Wpisz nazwę istniejącej postaci/pomysłu — przydatne gdy lista rozdziału jest pusta |
| **Połącz z…** | Połączenie dwóch wpisów lore (np. postać ↔ wpływ), niezależnie od pliku |
| **Odłącz od rozdziału** | Usuwa powiązanie z tym rozdziałem; wpis zostaje w projekcie |
| **Usuń wpis** | Trwale kasuje element z grafu lore (`Delete` na liście); czyści relacje i przebudowuje indeksy |
| **Mapa powiązań** | Graficzny podgląd koligacji |
| **Szukaj** | Znajdź wpisy po fragmencie tekstu, potem powiąż z rozdziałem |

#### Zespół (sync)

Wymaga trybu lokalnego i uruchomionego `cynober-server`. Przyciski: Wyślij / Pobierz / Synchronizuj.

## Pakiet exe (Nuitka)

```powershell
.\scripts\build_nuitka.ps1
# wynik: dist\run_lore_editor.dist\run_lore_editor.exe
```

Skopiuj **cały folder** `run_lore_editor.dist` do katalogu projektu lub uruchamiaj exe z folderu z `.lore-project`.  
Pierwszy build Nuitka trwa długo (~5–15 min); paczka ma ~25–80 MB (Cynober w środku).

## Testy

```bash
python -m unittest discover -s tests -v
```

## Licencja

MIT