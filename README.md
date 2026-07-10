# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).

Narzędzie **pisarskie** (offline-first) — bez Lua, bez silnika gry.

**Wersja:** zobacz `lore-editor --help` lub menu **Pomoc → O programie** (skrót **F1** — przewodnik).

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

Przy pierwszym uruchomieniu tworzy się `.lore-project` i plik `Nazwa.kafd`.

## Layout folderu

```
MojaPowiesc/
  .lore-project          # opcjonalny znacznik projektu
  rozdzial_01.txt        # treść — edytujesz w edytorze
  rozdzial_02.md
  MojaPowiesc.kafd       # lore: postacie, relacje, indeksy (Lore Pack)
```

| Plik | Co trzyma |
|------|-----------|
| `.txt` / `.md` | Tekst rozdziału (Twoja proza) |
| `.kafd` | Graf lore + wskaźniki do plików tekstowych |
| `.lore-project` | Nazwa świata Cynober |

Stary format (`*.meta.json` + `shards/`) jest **automatycznie migrowany** przy zapisie do jednego `.kafd`.

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
| Przewodnik pisarza | Szybki start, dwa rodzaje zapisu |
| Skróty klawiszowe | Ctrl+S, Ctrl+W, Ctrl+F… |
| Czcionki i wygląd | Presety szkic / druk / czytelność |
| Wydruk i eksport | Podgląd stron, DOCX, scenariusz |
| Panel Lore | Postacie, powiązania, sync |
| Pliki i Lore Pack | Co jest w `.kafd` |
| O programie | Wersja, linki |

## Edytor tekstu

### Plik i karty

- **Karty** — wiele plików naraz
- Zamknij kartę: `×` na karcie, **Ctrl+W**, środkowy przycisk myszy
- **Autosave** rozdziału co 60 s (tylko pliki już zapisane na dysku)

### Skróty

| Skrót | Akcja |
|-------|--------|
| Ctrl+N | Nowa karta |
| Ctrl+O | Otwórz |
| Ctrl+S | Zapisz rozdział |
| Ctrl+Shift+S | Zapisz jako… |
| Ctrl+W | Zamknij kartę |
| Ctrl+Z / Ctrl+Y | Cofnij / Ponów |
| Ctrl+F | Znajdź |
| F1 | Pomoc |

### Dwa rodzaje zapisu

| Akcja | Co zapisuje |
|-------|-------------|
| **Zapisz** (Ctrl+S) | Tekst bieżącego rozdziału (`.txt`) |
| **Zapisz projekt lore** | Graf lore w `Nazwa.kafd` |

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
| **Usuń wpis** | Trwałe skasowanie (`Delete` na liście) |
| **Mapa powiązań** | Graf koligacji |
| **Szukaj** | Fraza w notatkach i opisach |

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