"""Treści pomocy wbudowanej — język polski."""

from __future__ import annotations

from lore import __version__

TOPICS: dict[str, tuple[str, str]] = {}


def _topic(title: str, body: str) -> None:
    TOPICS[title] = (title, body.strip())


_topic(
    "Przewodnik pisarza",
    f"""
Lore Editor v{__version__} — edytor rozdziałów z panelem lore (postacie, pomysły, wpływy).

SZYBKI START
1. Uruchom: lore-editor
   • domyślny katalog: ../dokumenty/lore (obok repo lore-editor)
   • albo: lore-editor --project-dir ŚCIEŻKA
   • albo: cd do folderu z .lore-project
2. Plik → Otwórz… — wybierz rozdział (.txt / .md).
3. Panel Lore (po prawej) → + Postać / + Pomysł / + Wpływ.
4. Ctrl+S — zapisuje rozdział i lore w jednym kroku.
5. Opcjonalnie: Ctrl+Shift+D (słownik nazw) · F7 (pisownia SJP).

KATALOG PRACY (kolejność)
1. --project-dir DIR
2. zmienna LORE_PROJECT_DIR
3. plik .lore-project w cwd lub rodzicach
4. ostatni wybór z GUI (Plik → Katalog projektu…)
5. domyślnie ../dokumenty/lore (nadpisz: LORE_DEFAULT_WORK_DIR)

W PROGRAMIE (GUI)
  Plik → Katalog projektu… (Ctrl+Shift+O) — wybierz folder powieści
  Plik → Domyślny katalog (dokumenty/lore)
  Pasek narzędzi: „Katalog…” · klik w ścieżkę na pasku statusu

SESJA (automatycznie)
  Przy starcie: ostatni katalog pracy + ostatni plik rozdziału
  (jeśli plik nadal istnieje). Zapis: otwarcie / zapis / zmiana karty.
  Plik sesji: %USERPROFILE%\\.lore_editor\\last_work_dir.json
  (pola path + last_file). Marker .lore-project w folderze kodu
  lore-editor jest ignorowany — nie zastępuje katalogu powieści.

PIERWSZE URUCHOMIENIE
W katalogu pracy powstaje .lore-project i .lore-history/ (snapshoty).
Istniejący projekt dostaje snapshot „Stan początkowy projektu”.
Uwzględnij .lore-history/ w backupie (chmura, dysk zewnętrzny).

ZAPIS
• Ctrl+S / autosave — tekst rozdziału + graf lore (.kafd) transakcyjnie.
• Lore → Zapisz projekt lore — tylko graf, bez ponownego zapisu tekstu.
• Przy zamknięciu — ostrzeżenie, jeśli lore jest niezapisane.

WARSTWY PROJEKTU
• .txt / .md — Twoja proza (rozdziały)
• .kafd — graf lore (postacie, relacje, stany czasowe)
• .lore-history/ — historia zmian (przywracanie całego projektu)
• .lore-spelling.json — słowa dodane przy F7 (opcjonalnie)

PROJEKT
• Katalog: --project-dir / LORE_PROJECT_DIR / .lore-project / ../dokumenty/lore
• Nazwa = name= w .lore-project, --project, albo nazwa folderu.
• Format lore: Lore Pack — jeden plik .kafd (magazyn atomów Karmazyn), bez shards/.
• Stary format (*.meta.json + shards/) migruje się przy zapisie.
• Domyślnie BEZ sieci — silnik Cynober DB w tym samym procesie.

SIEĆ (skrót)
To NIE jest zwykłe TCP/HTTP. Tryb --rpc = protokół Karmazyn + cynober-server.
Szczegóły: temat „Sieć: Karmazyn i Cynober DB”.

PASEK STATUSU
Ścieżka · słowa · strony · (Courier) ~minut scenariusza · kodowanie.
""",
)

_topic(
    "Skróty klawiszowe",
    """
PLIK
  Ctrl+N          Nowa karta
  Ctrl+O          Otwórz plik
  Ctrl+S          Zapisz rozdział + lore
  Ctrl+Shift+S    Zapisz jako…
  Ctrl+W          Zamknij kartę

EDYCJA
  Ctrl+Z          Cofnij
  Ctrl+Y          Ponów
  Ctrl+F          Znajdź (w tekście rozdziału)
  Ctrl+Shift+D    Słownik nazw (lore)
  Ctrl+Shift+O    Katalog projektu…
  F7              Sprawdź pisownię

INNE
  F1              Ta pomoc (przewodnik)
  Środkowy klik   Zamknij kartę (na nazwie karty)
  × na karcie     Zamknij kartę

MENU LORE
  Odśwież panel
  Zapisz projekt lore
  Utwórz punkt przywracania…
  Historia zmian…

Autosave: co 60 s (tylko zapisane pliki) — tekst + lore + snapshot.
""",
)

_topic(
    "Czcionki i wygląd",
    """
Menu: Wygląd

SZKIC (drafting) — wielogodzinne pisanie
  Courier New      Klasyczny maszynopis; licznik stron jak scenariusz
  Courier Prime    Nowoczesny wariant maszynopisu
  Calibri          Bezszeryfowa, lekka
  Arial            Prosta bezszeryfowa (Windows)

DRUK I PUBLIKACJA
  Garamond         Powieść / druk elegancki
  Times New Roman  Standard wydawnictw (rękopis)

CZYTELNOŚĆ
  OpenDyslexic     Litery rozdzielone — dysleksja
  Lexend           Wysoka czytelność przy zmęczonym wzroku

ROZMIAR: 11 lub 12 pt
INTERLINIA:
  1,5 — szkic roboczy (zalecane przy pisaniu)
  1,0 — tekst gotowy do druku

Ustawienia zapisują się w: %USERPROFILE%\\.lore_editor\\typography.json

CZCIONKI OPCJONALNE
Uruchom w PowerShell: .\\scripts\\install_fonts.ps1
(Lexend, OpenDyslexic). Courier Prime: fonts.google.com/specimen/Courier+Prime
""",
)

_topic(
    "Wydruk i eksport",
    """
Menu: Wydruk

PODGLĄD STRON
Miniatury stron z marginesami i fragmentem tekstu.

  Scenariusz (Courier)
    • 55 wierszy na stronę (format Letter)
    • Reguła: 1 strona ≈ 1 minuta filmu
    • Licznik w pasku statusu: „12 str. · ~12 min”

  Rękopis do wysyłki
    • Times New Roman 12 pt, interlinia 2,0
    • Margines ~2,5 cm (1 cal), A4
    • ~250 słów na stronę

  Gotowy do druku
    • Times New Roman 12 pt, interlinia 1,0
    • A4, margines 2 cm
    • ~350 słów na stronę

EKSPORT DOCX
Zapisuje plik Word z czcionką i marginesami profilu.
Wymaga: pip install python-docx (jest w zależnościach pakietu).

Podgląd to orientacyjna paginacja — przed wysyłką do wydawcy sprawdź DOCX w Wordzie.
""",
)

_topic(
    "Słownik i pisownia",
    """
Menu: Edycja

SŁOWNIK NAZW (Ctrl+Shift+D)
Szybki podgląd postaci, miejsc i innych wpisów z grafu lore.
• Wpisz fragment nazwy (lub zaznacz słowo w tekście — pole wyszukiwania się wypełni).
• Filtruj po typie (Postać, Miejsce, …).
• Dwuklik lub „Wstaw do tekstu” — wstawia nazwę w miejscu kursora.
• Nie jest to słownik PWN — to spis nazw własnych Twojego świata.

SPRAWDŹ PISOWNIĘ (F7)
Offline, bez sieci. Silnik (w tej kolejności):
1. Nazwy z lore + Twój słownik projektu (.lore-spelling.json)
2. Słownik ortograficzny SJP.PL (format hunspell, licencja m.in. Apache 2.0)
   — pełna fleksja polska; wymaga pakietu spylls (jest w zależnościach)
3. Zapas: lista częstych słów PL (gdy brak SJP/spylls)

Źródło SJP: https://sjp.pl/slownik/ort/ — atrybucja w lore/data/sjp/NOTICE.txt

W oknie korekty:
  Zamień — wstaw wybraną sugestię
  Ignoruj — pomiń w tej sesji
  Dodaj do słownika — zapisz w .lore-spelling.json
  Szukaj w lore… — otwórz słownik nazw dla tego słowa

Podkreślenie na czerwono = słowo spoza SJP i lore. Akronimy (np. FBI) są
traktowane jako poprawne.

Wskazówka: najpierw uzupełnij panel Lore (postacie, miejsca) — wtedy korekta
nie zgłasza ich jako błędy.
""",
)

_topic(
    "Panel Lore",
    """
Panel po prawej — zakładki Rozdział · Szukaj · Zespół.

WAŻNE: Otwórz rozdział w edytorze, zanim powiążesz lore.

DODAWANIE
  + Postać    Postać; przy otwartym rozdziale — auto-powiązanie
  + Pomysł    Myśl powiązana z rozdziałem
  + Wpływ     Inspiracja (autor, mit…) — relacja „inspiruje”

POWIĄZANIA
  Powiąż z rozdziałem   Wpis z listy → ten plik
  Powiąż inny wpis…     Nazwa ręcznie
  Połącz z…             Relacja między dwoma wpisami
  Odłącz od rozdziału   Usuwa więź z plikiem
  Usuń wpis             Trwałe skasowanie (Delete) — poprzedza snapshot
  Edytuj wpis           Notatka / opis w kontekście rozdziału

LISTA ROZDZIAŁU
  Wpisy sortowane po „temperaturze” (gorące na górze).
  Badge [gorą] / [ciep] / [zimn] — jak świeży jest wpis.
  Wpisy „grobowca” są ukryte (dawny balast).

INNE
  Mapa powiązań   Graf wokół rozdziału lub wpisu
  Szukaj          Zapytania semantyczne — patrz temat „Zapytania semantyczne”
  Zespół          Sync przez cynober-server (protokół Karmazyn — patrz temat Sieć)
""",
)

_topic(
    "Kontekst czasowy",
    """
Postać w rozdziale 1 może być sojusznikiem, w rozdziale 10 — wrogiem.
Lore Editor nie trzyma jednego globalnego stanu — zapisuje mutacje per rozdział.

JAK TO DZIAŁA
• Otwórz rozdział w edytorze (karta z plikiem).
• Edytuj notatkę lub opis postaci (Edytuj wpis).
• Zmiana trafia do pola Stany w .kafd — powiązana z tym rozdziałem.
• Panel pokazuje stan adekwatny do bieżącego pliku, nie do całej powieści.

PODGLĄD
Nagłówek szczegółów wpisu zawiera:
  · rozdział (kontekst as_of)
  · temperaturę wpisu

OŚ CZASU
Rozdziały są sortowane po ścieżce pliku (np. rozdzial_01, rozdzial_02…).
Zapytania „nie od 5” korzystają z tej kolejności.

WSKAZÓWKA
Pracując nad rozdziałem 2, nie zobaczysz notatki dopisanej w rozdziale 10 —
dopóki nie otworzysz pliku z aktywnością w tym rozdziale lub późniejszym.
""",
)

_topic(
    "Zapytania semantyczne",
    """
Zakładka Szukaj w panelu lore — frazy tekstowe i zapytania po grafie.

PRZYKŁADY
  postacie przy Anna
  postacie przy Twierdza nie od 5
  typ:Postać "sojusznik"
  "mgła nad rzeką"

SKŁADNIA
  postacie / miejsca / typ:Postać   — filtr typu
  przy X / powiązane z X            — sąsiedzi encji X w grafie
  nie od N                          — ostatnie wystąpienie przed N-tym rozdziałem
  "fraza"                           — szukanie w notatkach, opisach, tekstach pomysłów

Wyniki pojawiają się w zakładce Rozdział (z badge temperatury).

PROSTA FRAZA
Sam tekst bez słów kluczowych działa jak dawniej — przeszukuje pola tekstowe.

ZAPYTANIA ZŁOŻONE
Można łączyć: typ + przy + nie od + fraza w cudzysłowie.
""",
)

_topic(
    "Pliki i Lore Pack",
    """
STRUKTURA FOLDERU
  MojaPowiesc/
    .lore-project         Znacznik (name=MojaPowiesc)
    .lore-history/        Historia zmian (auto)
    rozdzial_01.txt       Tekst rozdziału
    MojaPowiesc.kafd      Graf lore (Lore Pack)

CO JEST W .kafd
  • Format: Lore Pack w magazynie atomów Karmazyn (silnik Cynober DB)
  • Bąble: postacie, pomysły, dokumenty, wpływy, miejsca…
  • Relacje: występuje w, koliguje z, wpływa na, inspiruje…
  • Stany — mutacje notatek/opisów per rozdział (kontekst czasowy)
  • OstatniDotyk — znacznik aktywności wpisu (termodynamika)
  • Indeksy zapytań (cache) — odtwarzalne z danych

CO NIE JEST W .kafd
  • Treść rozdziałów — zawsze w .txt / .md

.gitignore często ignoruje *.kafd — rozważ commitowanie lore w prywatnym repo.

BACKUP (pełny projekt)
  pliki .txt / .md
  Nazwa.kafd
  .lore-project
  .lore-history/        ← warstwa ratunkowa
""",
)

_topic(
    "Historia zmian",
    """
Folder .lore-history/ tworzy się AUTOMATYCZNIE przy pierwszym uruchomieniu
edytora w katalogu projektu (README.txt wyjaśnia przeznaczenie folderu).

CO ZAWIERA KAŻDY SNAPSHOT
  • Nazwa.kafd — cały graf lore
  • rozdzialy/ — kopie wszystkich .txt i .md (z podfolderami)
  • .lore-project — jeśli istnieje

KIEDY POWSTAJĄ KOPIE
  • Ctrl+S / autosave rozdziału (z etykietą nazwy pliku)
  • Co ~2 min przy zapisie lore (jeśli coś się zmieniło)
  • Przed usunięciem wpisu lore
  • Przed przywróceniem starszej wersji
  • Ręcznie: Lore → Utwórz punkt przywracania…
  • Pierwsze otwarcie istniejącego projektu: „Stan początkowy”

PRZYWRACANIE
  Lore → Historia zmian… → wybierz datę → Przywróć.
  Bieżący stan zapisywany jest automatycznie przed przywróceniem.
  Otwarte karty rozdziałów przeładowują się z dysku.

ROTACJA
Przechowywane jest do 40 ostatnich snapshotów.

BACKUP
Nie pomijaj .lore-history/ — ratuje przy skasowanym rozdziale,
zepsutym .kafd lub przypadkowym usunięciu postaci.
""",
)

_topic(
    "Sieć: Karmazyn i Cynober DB",
    """
UWAGA — TO NIE JEST „ZWYKŁA SIEĆ”
Port 8080 i --host sugerują zwykłe TCP. W rzeczywistości Lore Editor w trybie
sieciowym używa protokołu Karmazyn (handshake HSS, link HSL, ramki binarne)
oraz KarminQL-RPC w JSON — na serwerze cynober-server z pakietu cynober-db.
Nie ma tu HTTP, REST ani SQL.

DOMYŚLNIE: BEZ SIECI (offline-first)
  • Edytor → silnik Cynober DB w jednym procesie Pythona
  • Zapis lore: plik .kafd (atomowy magazyn Karmazyn)
  • Rozdziały: zwykłe .txt / .md na dysku
  • Żaden socket — zalecane dla pisania solo

PRACA W SIECI (jawnie: --rpc)
  lore-editor --rpc --host ADRES [--port 8080]

  Stos połączenia:
    TCP/IP  →  Karmazyn HSS (handshake, szyfrowanie)
            →  Karmazyn HSL (sesja RPC)
            →  ramki _send_frame / _recv_frame
            →  JSON { "query": "linia KarminQL" }
            →  cynober-server (Cynober-Secure-1.2)

  Po sieci idzie tylko GRAF LORE (świat Cynober). Tekst rozdziałów zostaje
  lokalnie u pisarza.

SERWER
  Uruchom na hoście z lore:  cynober-server  (port 8080)
  Klient: pakiet cynober-db, moduł cynober_client

PROFIL (opcjonalnie)
  ~/.karmazyn_client.json — host, port, ustawienia HSS
  lore-editor --rpc --profile nazwa

SYNC ZESPOŁU (zakładka Zespół)
  Osobna ścieżka: cynober_replicate (push / pull / sync).
  Znowu TCP + protokół Cynober/Karmazyn — nie upload FTP/SFTP pliku .kafd
  jako „protokół aplikacji”. Wymaga trybu lokalnego i wcześniejszego zapisu .kafd.

TO NIE JEST (typowe pomyłki)

  HTTP / REST / WebSocket
    Port 8080 ≠ serwer WWW. Brak GET /api/…, nagłówków HTTP i JSON-API.

  Baza SQL (PostgreSQL, SQLite, MySQL…)
    Lore = Cynober DB, atomy Karmazyn w .kafd — nie tabele SQL.

  „Zwykły” TCP z własnym JSON-em
    Najpierw Karmazyn HSS + HSL + ramki binarne; dopiero wewnątrz JSON
    z polem "query" (KarminQL-RPC, Cynober-Secure-1.2).

  FTP / SFTP / rsync jako sync aplikacji
    Nie zastępuje cynober-server ani cynober_replicate. Wrzucenie .kafd
    na dysk to backup pliku, nie protokół współpracy między edytorami.

  Własny backend bez cynober-server
    --rpc łączy się wyłącznie z serwerem Cynober-Secure-1.2.

  DOZWOLONE OBOK TEGO
    Ręczna kopia całego folderu projektu na backup/chmurę — archiwum
    plików; nie zastępuje komunikacji Karmazyn w trybie --rpc lub Zespół.

BAZA DANYCH
  Dedykowany silnik: Cynober DB (cynober-db >= 8.0.1).
  Format na dysku: .kafd = Lore Pack w vfs Karmazyn.
  Zapytania: KarminQL (ukryte pod API LoreStore dla pisarza).
""",
)

_topic(
    "O programie",
    f"""
Lore Editor v{__version__}
Silnik lore: Cynober DB (cynober-db >= 8.0.1) — magazyn atomów Karmazyn (.kafd)
Repozytorium: github.com/Maciej-EriAmo/lore-editor

Funkcje: kontekst czasowy lore, zapytania semantyczne, termodynamika wpisów,
historia zmian projektu, transakcyjny zapis tekstu + grafu, słownik nazw,
sprawdzanie pisowni (SJP.PL + spylls).

Tryb offline-first — bez serwera, bez Lua.
Sieć (opcjonalnie): protokół Karmazyn + cynober-server (--rpc). Patrz temat
„Sieć: Karmazyn i Cynober DB”.

Instalacja:
  pip install "cynober-db>=8.0.1"
  pip install -e .
  lore-editor

Pakiet exe: .\\scripts\\build_nuitka.ps1

Licencja kodu: MIT

Składowe (pisownia):
  • Słownik SJP.PL (hunspell pl_PL) — Apache 2.0 (oraz GPL/LGPL/MPL/CC BY)
    https://sjp.pl/slownik/ort/ — atrybucja: lore/data/sjp/NOTICE.txt
  • spylls — silnik hunspell w Pythonie (zależność PyPI)
""",
)

DEFAULT_TOPIC = "Przewodnik pisarza"


def topic_titles() -> list[str]:
    return list(TOPICS.keys())


def get_topic(title: str) -> tuple[str, str]:
    return TOPICS.get(title, TOPICS[DEFAULT_TOPIC])