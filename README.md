# Lore Editor

Edytor lore dla **pisarzy** — postacie, pomysły, wpływy, koligacje — na silniku [Cynober DB](https://github.com/Maciej-EriAmo/DBase).

Narzędzie **pisarskie** (offline-first) — bez Lua, bez silnika gry.

Graf lore opiera się na **dedykowanej bazie Cynober DB** (format atomów **Karmazyn**, plik `.kafd`). To nie jest zwykła sieć ani SQL — szczegóły w sekcji [Komunikacja i sieć](#komunikacja-i-sieć).

**Wersja:** zobacz `lore-editor --version` lub menu **Pomoc → O programie** (skrót **F1**).

## Instalacja

```bash
pip install "cynober-db>=8.0.1"
pip install -e .
```

Zależności obejmują m.in.:

| Pakiet | Rola |
|--------|------|
| `cynober-db` | Silnik grafu lore (Karmazyn / KarminQL) |
| `python-docx` | Eksport rękopisu do Worda |
| `spylls` | Silnik hunspell (korekta pisowni + słownik SJP.PL) |

Windows — skrót na pulpicie i pakiet:

```powershell
.\scripts\install_writer.ps1 -Project MojaPowiesc
```

Opcjonalne czcionki (Lexend, OpenDyslexic):

```powershell
.\scripts\install_fonts.ps1
```

## Projekt — zero konfiguracji

### Katalog pracy (kolejność)

1. **`--project-dir DIR`** — wskazany folder  
2. **`LORE_PROJECT_DIR`** — zmienna środowiskowa  
3. **`.lore-project`** — w cwd lub katalogach nadrzędnych  
4. **Ostatni wybór z GUI** — `Plik → Katalog projektu…` (zapis w `~/.lore_editor/last_work_dir.json`)  
5. **Domyślnie:** `../dokumenty/lore` względem korzenia repo `lore-editor`  
   (np. `C:\Users\…\dokumenty\lore` obok `…\lore-editor`)  
   Nadpisz: `LORE_DEFAULT_WORK_DIR`.

**Z poziomu okna (GUI):**

| Akcja | Gdzie |
|-------|--------|
| Wybierz folder powieści | **Plik → Katalog projektu…** (`Ctrl+Shift+O`) lub przycisk **Katalog…** |
| Wróć do `dokumenty/lore` | **Plik → Domyślny katalog (dokumenty/lore)** |
| Szybki klik | ścieżka projektu na **pasku statusu** (prawo) |

**Sesja:** przy starcie otwierany jest ostatni katalog pracy i **ostatni plik** rozdziału (jeśli nadal istnieje). Zapamiętywane przy otwarciu/zapisie/zmianie karty w `~/.lore_editor/last_work_dir.json`. Marker `.lore-project` w folderze kodu `lore-editor` jest pomijany.

**Opcja A — domyślny folder (zalecane przy starcie ze skrótu / z repo):**

```powershell
lore-editor
# → …/dokumenty/lore  (tworzony przy pierwszym starcie)
```

**Opcja B — wskazany katalog:**

```bash
lore-editor --project-dir ~/dokumenty/InnaPowiesc
# albo
set LORE_PROJECT_DIR=D:\Pisanie\Saga
lore-editor
```

**Opcja C — folder z markerem (cd do powieści):**

```powershell
cd ~/dokumenty/MojaPowiesc   # zawiera .lore-project
lore-editor
```

Plik `.lore-project`:

```
name=MojaPowiesc
```

Nazwa świata = `name=` z markera, `--project`, albo nazwa folderu.

Przy **pierwszym uruchomieniu** w wybranym katalogu tworzy się:

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
  .lore-spelling.json    # opcjonalnie: słowa dodane przy korekcie pisowni
```

| Plik / folder | Co trzyma |
|---------------|-----------|
| `.txt` / `.md` | Tekst rozdziału (Twoja proza) |
| `.kafd` | Graf lore + wskaźniki do plików tekstowych |
| `.lore-project` | Nazwa świata Cynober |
| `.lore-history/` | Snapshoty lore + rozdziałów do przywracania |
| `.lore-spelling.json` | Słownik pisowni projektu (F7 → „Dodaj do słownika”) |

### Słownik nazw i pisownia

- **Edycja → Słownik nazw…** (`Ctrl+Shift+D`) — podgląd postaci/miejsc z lore, wstawianie nazwy do tekstu.
- **Edycja → Sprawdź pisownię…** (`F7`) — korekta offline:
  - **SJP.PL** (słownik hunspell, m.in. Apache 2.0 — [sjp.pl/slownik/ort](https://sjp.pl/slownik/ort/)), silnik [spylls](https://pypi.org/project/spylls/)
  - nazwy z lore + `.lore-spelling.json` w projekcie

Atrybucja SJP: `lore/data/sjp/NOTICE.txt`. Szczegóły: **Pomoc → Słownik i pisownia**.

Stary format (`*.meta.json` + `shards/`) jest **automatycznie migrowany** przy zapisie do jednego `.kafd`.

**Backup:** kopiuj cały folder projektu, w tym `.lore-history/` i opcjonalnie `.lore-spelling.json` — warstwa ratunkowa przy utracie rozdziału lub zepsuciu `.kafd`.

## Uruchomienie

```bash
lore-editor                              # domyślnie: ../dokumenty/lore (bez sieci)
lore-editor --project-dir D:\Pisanie\X   # wskazany katalog pracy
lore-editor --file rozdzial_01.txt       # jeden plik
lore-editor rozdzial_01.txt rozdzial_02.md   # kilka kart
lore-editor --rpc --host 192.168.1.10    # lore przez cynober-server (patrz niżej)
```

## Komunikacja i sieć

**Pułapka:** `--host` i port `8080` sugerują „zwykłe TCP”, ale Lore Editor **nie** gada po HTTP, REST ani SQL. W trybie sieciowym używasz **protokołu Karmazyn** (handshake HSS, link HSL, ramki binarne) i **KarminQL-RPC** w JSON — na serwerze **cynober-server** z pakietu **cynober-db**.

### Tryb domyślny — bez sieci (zalecany dla pisarza)

| Warstwa | Technologia |
|---------|-------------|
| Edytor → lore | Wywołania w jednym procesie Pythona |
| Silnik grafu | **Cynober DB** (KarminQL) |
| Zapis lore | Plik `.kafd` — atomowy magazyn **Karmazyn** |
| Rozdziały | Zwykłe `.txt` / `.md` na dysku |

Żadnego socketu. Firewall i router nie mają znaczenia.

### Praca w sieci — protokół Karmazyn + Cynober DB

Włączasz jawnie: `lore-editor --rpc --host ADRES [--port 8080]`.

| Warstwa | Co to jest |
|---------|------------|
| Transport | TCP/IP (`socket`, domyślnie port **8080**) |
| Handshake | **Karmazyn HSS** (`karmazyn_handshake`) — negocjacja, szyfrowanie |
| Sesja | **Karmazyn HSL** (`karmazyn_hsl`) — capability RPC |
| Ramki | `_send_frame` / `_recv_frame` — **nie** surowy tekst HTTP |
| Payload | JSON z polem `"query"` = linia **KarminQL** |
| Wersja protokołu | `Cynober-Secure-1.2` (klient `cynober_client`) |
| Serwer | **cynober-server** — ten sam stos co w cynober-db |

Rozdziały nadal leżą **lokalnie** u pisarza; po sieci chodzi tylko **graf lore** (operacje na świecie Cynober).

```bash
# Na maszynie z lore (np. zespół):
cynober-server          # nasłuch, domyślnie :8080

# Na laptopie pisarza:
lore-editor --rpc --host 192.168.1.10 --port 8080
```

Profil połączenia (host, port, HSS) można też trzymać w `~/.karmazyn_client.json` — wtedy `cynober_client.connect(profile="nazwa")`.

### Sync zespołu (zakładka Zespół)

Osobna ścieżka: **cynober_replicate** (push / pull / sync) — znowu TCP do **cynober-server**, nie zwykły upload plików. Wymaga trybu lokalnego (`.kafd` zapisany na dysku przed wysyłką).

### To nie jest (typowe pomyłki)

Lore Editor **nie** implementuje ani **nie** oczekuje:

| Myślisz, że… | W rzeczywistości |
|--------------|------------------|
| To HTTP/REST na porcie 8080 | **Nie.** Brak nagłówków HTTP, ścieżek `/api/…` i JSON-API. Port 8080 to domyślny **cynober-server**, nie serwer WWW. |
| Lore siedzi w SQL | **Nie.** Graf to **Cynober DB** — atomy **Karmazyn** w pliku `.kafd`, nie tabele PostgreSQL/SQLite/MySQL. |
| Wystarczy TCP z własnym JSON-em | **Nie.** Najpierw **Karmazyn HSS** (handshake), **HSL** (sesja), **ramki binarne**; wewnątrz dopiero JSON z `"query"` (KarminQL-RPC). |
| Sync = FTP/SFTP/rsync pliku `.kafd` | **Nie** jako protokół aplikacji. Zespół i `--rpc` wymagają **cynober-server** i **Cynober replicate** — nie zwykłego wrzucenia pliku. |
| Podłączę własny backend | **Nie** bez **cynober-server**. Klient `--rpc` mówi wyłącznie protokołem **Cynober-Secure-1.2**. |

**Dozwolone obok tego:** ręczna kopia folderu projektu (`.kafd` + rozdziały + `.lore-history/`) na backup lub chmurę — to archiwum plików, **nie** zastępuje komunikacji Karmazyn między edytorami.

Więcej: menu **Pomoc → Sieć: Karmazyn i Cynober DB** (F1).

## Pomoc w aplikacji

Menu **Pomoc** (lub **F1**):

| Temat | Zawartość |
|-------|-----------|
| Przewodnik pisarza | Szybki start, zapis, historia |
| Skróty klawiszowe | Ctrl+S, Ctrl+W, Ctrl+F… |
| Czcionki i wygląd | Presety szkic / druk / czytelność |
| Wydruk i eksport | Podgląd stron, DOCX, scenariusz |
| Panel Lore | Postacie, powiązania, sync |
| Słownik i pisownia | Nazwy z lore, F7, SJP.PL |
| Kontekst czasowy | Stany postaci per rozdział |
| Zapytania semantyczne | Wyszukiwanie po grafie lore |
| Historia zmian | Snapshoty, przywracanie projektu |
| Pliki i Lore Pack | Co jest w `.kafd` |
| Sieć: Karmazyn i Cynober DB | Nie zwykłe TCP — protokół i `--rpc` |
| O programie | Wersja, linki, licencje składowych |

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
| Ctrl+Shift+D | Słownik nazw (lore) |
| Ctrl+Shift+O | Katalog projektu… |
| F7 | Sprawdź pisownię (SJP + lore) |
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

Wymaga trybu lokalnego i **cynober-server** (protokół Karmazyn / Cynober replicate — nie zwykły transfer plików). Przyciski: Wyślij / Pobierz / Synchronizuj. Zobacz też **Pomoc → Sieć: Karmazyn i Cynober DB**.

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

Kod Lore Editor: **MIT**.

### Składowe zewnętrzne (pisownia)

| Składowa | Źródło | Licencja (wybór) |
|----------|--------|------------------|
| Słownik ortograficzny PL | [SJP.PL](https://sjp.pl/slownik/ort/) (`lore/data/sjp/`) | m.in. **Apache 2.0**, GPL 2, LGPL 2.1, MPL 1.1, CC BY 4.0 |
| Silnik hunspell (Python) | [spylls](https://pypi.org/project/spylls/) | zgodnie z pakietem PyPI |

W tym projekcie słownik SJP.PL jest używany na podstawie **Apache 2.0** z atrybucją — zob. `lore/data/sjp/NOTICE.txt` i `README_pl_PL.txt`.

Szerszy opis funkcji: [docs/SLOWNIK_I_PISOWNIA.md](docs/SLOWNIK_I_PISOWNIA.md).