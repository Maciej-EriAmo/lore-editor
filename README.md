# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).

Narzędzie **pisarskie** (offline-first) — bez Lua, bez silnika gry.

**Wersja:** zobacz `lore-editor --version` lub menu **Pomoc → O programie** (skrót **F1**).

## Instalacja

```bash
pip install "cynober-db>=8.0.1"
pip install -e .
```

Zależności obejmują m.in. `python-docx` (eksport rękopisu do Worda).

Windows — skrót na pulpicie i pakiet:

```powershell
.\scripts\install_writer.ps1 -Project MojaPowiesc
```

Opcjonalne czcionki (Lexend, OpenDyslexic):

```powershell
.\scripts\install_fonts.ps1
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

Przy **pierwszym uruchomieniu** tworzy się:

- `.lore-project` (znacznik projektu)
- `.lore-history/` (historia zmian — snapshoty lore + rozdziałów)
- `Nazwa.kafd` (przy pierwszym zapisie lore)

## Layout folderu

```
MojaPowiesc/
  .lore-project          # opcjonalny znacznik projektu
  .lore-history/         # historia zmian (auto przy 1. uruchomieniu)
    README.txt           # opis folderu — nie usuwać
    manifest.json        # rejestr snapshotów
    snapshots/           # kopie zapasowe
  rozdzial_01.txt        # treść — edytujesz w edytorze
  rozdzial_02.md
  MojaPowiesc.kafd       # lore: postacie, relacje, indeksy (Lore Pack)
```

| Plik / folder | Co trzyma |
|---------------|-----------|
| `.txt` / `.md` | Tekst rozdziału (Twoja proza) |
| `.kafd` | Graf lore + wskaźniki do plików tekstowych |
| `.lore-project` | Nazwa świata Cynober |
| `.lore-history/` | Snapshoty lore + rozdziałów do przywracania |

Stary format (`*.meta.json` + `shards/`) jest **automatycznie migrowany** przy zapisie do jednego `.kafd`.

**Backup:** kopiuj cały folder projektu, w tym `.lore-history/` — to warstwa ratunkowa przy utracie rozdziału lub zepsuciu `.kafd`.

## Uruchomienie

```bash
lore-editor                              # z katalogu projektu
lore-editor --file rozdzial_01.txt       # jeden plik
lore-editor rozdzial_01.txt rozdzial_02.md   # kilka kart
lore-editor --rpc --host 192.168.1.10    # lore na serwerze
```

## Pomoc w aplikacji

Menu **Pomoc** (lub **F1**):

| Temat | Zawartość |
|-------|-----------|
| Przewodnik pisarza | Szybki start, zapis, historia |
| Skróty klawiszowe | Ctrl+S, Ctrl+W, Ctrl+F… |
| Czcionki i wygląd | Presety szkic / druk / czytelność |
| Wydruk i eksport | Podgląd stron, DOCX, scenariusz |
| Panel Lore | Postacie, powiązania, sync |
| Kontekst czasowy | Stany postaci per rozdział |
| Zapytania semantyczne | Wyszukiwanie po grafie lore |
| Historia zmian | Snapshoty, przywracanie projektu |
| Pliki i Lore Pack | Co jest w `.kafd` |
| O programie | Wersja, linki |

## Edytor tekstu

### Plik i karty

- **Karty** — wiele plików naraz
- Zamknij kartę: `×` na karcie, **Ctrl+W**, środkowy przycisk myszy
- **Autosave** rozdziału co 60 s (tylko pliki już zapisane na dysku) — zapisuje też lore

### Skróty

| Skrót | Akcja |
|-------|--------|
| Ctrl+N | Nowa karta |
| Ctrl+O | Otwórz |
| Ctrl+S | Zapisz rozdział **i** lore (transakcyjnie) |
| Ctrl+Shift+S | Zapisz jako… |
| Ctrl+W | Zamknij kartę |
| Ctrl+Z / Ctrl+Y | Cofnij / Ponów |
| Ctrl+F | Znajdź (w tekście rozdziału) |
| F1 | Pomoc |

### Zapis projektu

| Akcja | Co zapisuje |
|-------|-------------|
| **Zapisz** (Ctrl+S) | Tekst rozdziału (`.txt`) **oraz** graf lore (`.kafd`) — jedna operacja |
| **Autosave** | To samo co Ctrl+S, co 60 s |
| **Zapisz projekt lore** (menu Lore) | Tylko graf lore — bez ponownego zapisu tekstu |

Ctrl+S zapisuje tekst atomowo (plik tymczasowy → replace), potem od razu flushuje `.kafd`. Przy zamykaniu edytora ostrzeżenie, jeśli lore pozostało niezapisane.

Każdy zapis rozdziału tworzy też wpis w `.lore-history/` (snapshot lore + wszystkich rozdziałów).

### Wygląd — czcionki

Menu **Wygląd** — ustawienia w `%USERPROFILE%\.lore_editor\typography.json`.

**Szkic (drafting)**

| Preset | Zastosowanie | Domyślnie |
|--------|--------------|-----------|
| Courier New | Maszynopis, scenariusz | 12 pt, interlinia 1,5 |
| Courier Prime | Scenariusz (nowoczesny) | 12 pt, 1,5 |
| Calibri | Długie sesje pisania | 11 pt, 1,5 |
| Arial | Bezszeryfowa, prosta | 11 pt, 1,5 |

**Druk i publikacja**

| Preset | Zastosowanie | Domyślnie |
|--------|--------------|-----------|
| Garamond | Powieść / druk | 12 pt, 1,0 |
| Times New Roman | Rękopis wydawniczy | 12 pt, 1,0 |

**Czytelność**

| Preset | Zastosowanie |
|--------|--------------|
| OpenDyslexic | Dysleksja — litery rozdzielone |
| Lexend | Zmęczony wzrok |

Rozmiar **11 / 12 pt** i interlinia **1,0 / 1,5** można ustawić niezależnie od presetu.

### Wydruk i eksport

Menu **Wydruk**.

**Podgląd stron** — miniatury z marginesami i fragmentem tekstu:

| Profil | Format | Uwagi |
|--------|--------|--------|
| Scenariusz | Courier, Letter | 55 wierszy/str., **1 str. ≈ 1 min** |
| Rękopis do wysyłki | TNR 12, interlinia 2,0, A4 | Margines ~2,5 cm, ~250 słów/str. |
| Gotowy do druku | TNR 12, interlinia 1,0, A4 | ~350 słów/str. |

**Eksport DOCX** — plik Word z czcionką i marginesami profilu (do wysyłki wydawnictwu).

Pasek statusu pokazuje m.in. liczbę stron i (dla Courier) szacowany czas scenariusza.

## Panel lore

Zakładki: **Rozdział · Szukaj · Zespół**.

**Ważne:** powiązania z rozdziałem wymagają **otwartego pliku** w edytorze.

### Dodawanie wpisów

| Przycisk | Co robi |
|----------|---------|
| **+ Postać** | Tworzy postać; przy otwartym rozdziale — auto-powiązanie |
| **+ Pomysł** | Zapisuje myśl i wiąże z rozdziałem |
| **+ Wpływ** | Inspiracja (np. autor, mit), relacja „inspiruje” |

### Powiązania

| Akcja | Kiedy użyć |
|-------|------------|
| **Powiąż z rozdziałem** | Wpis z listy → ten plik |
| **Powiąż inny wpis…** | Nazwa istniejącego wpisu (gdy lista pusta) |
| **Połącz z…** | Relacja między dwoma wpisami (np. postać ↔ wpływ) |
| **Odłącz od rozdziału** | Usuwa więź z plikiem; wpis zostaje w projekcie |
| **Usuń wpis** | Trwałe skasowanie (`Delete` na liście) — poprzedzane snapshotem |
| **Mapa powiązań** | Graf koligacji wokół rozdziału lub wpisu |
| **Edytuj wpis** | Notatka / opis — w kontekście bieżącego rozdziału |

### Kontekst czasowy

Edycja notatki lub opisu przy **otwartym rozdziale** zapisuje mutację na osi narracji — nie nadpisuje stanu z innych rozdziałów.

Panel pokazuje stan postaci **adekwatny do pliku**, nad którym pracujesz. W podglądzie widać bieżący rozdział i temperaturę wpisu.

### Termodynamika wpisów

Lista w zakładce Rozdział sortuje wpisy według „temperatury”:

| Stan | Znaczenie |
|------|-----------|
| **gorący** | Ostatnio edytowany lub powiązany z bieżącym rozdziałem |
| **ciepły** | Niedawno używany |
| **zimny** | Dawno nietknięty |
| **grobowiec** | Ukryty na liście — dawno nieużywany balast |

### Zapytania semantyczne (zakładka Szukaj)

Pole Szukaj obsługuje frazy tekstowe **i** zapytania po grafie lore:

```
postacie przy Anna nie od 5
typ:Postać "sojusznik"
postacie przy Twierdza
```

- `postacie przy X` — wpisy powiązane z encją X
- `nie od N` — nie występowały w tekście od N-tego rozdziału (oś = kolejność plików)
- `typ:Postać` — filtr typu
- `"fraza"` — szukanie w notatkach i opisach

Wyniki pojawiają się w zakładce Rozdział.

### Historia zmian (menu Lore)

| Akcja | Opis |
|-------|------|
| **Utwórz punkt przywracania…** | Ręczny snapshot z opisem |
| **Historia zmian…** | Lista snapshotów, przywracanie |

Snapshot obejmuje `.kafd` i wszystkie rozdziały. Przed przywróceniem bieżący stan jest zapisywany automatycznie.

### Zespół (sync)

Wymaga trybu lokalnego i `cynober-server`. Przyciski: Wyślij / Pobierz / Synchronizuj.

## Pakiet exe (Nuitka)

```powershell
.\scripts\build_nuitka.ps1
# wynik: dist\run_lore_editor.dist\run_lore_editor.exe
```

Skopiuj **cały folder** `run_lore_editor.dist` do katalogu projektu lub uruchamiaj exe z folderu z `.lore-project`.  
Pierwszy build Nuitka trwa długo (~5–15 min); paczka ma ~25–80 MB.

## Testy

```bash
python -m unittest discover -s tests -v
```

## Licencja

MIT