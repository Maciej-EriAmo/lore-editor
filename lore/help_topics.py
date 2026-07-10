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
1. Otwórz folder powieści (lub utwórz .lore-project z linią name=NazwaProjektu).
2. Uruchom: lore-editor
3. Plik → Otwórz… — wybierz rozdział (.txt / .md).
4. Panel Lore (po prawej) → + Postać / + Pomysł / + Wpływ.
5. Ctrl+S — zapisuje rozdział i lore w jednym kroku.

PIERWSZE URUCHOMIENIE
Automatycznie powstaje folder .lore-history/ (snapshoty ratunkowe).
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

PROJEKT
• Nazwa = nazwa folderu lub wpis w .lore-project.
• Format lore: Lore Pack — jeden plik .kafd, bez shards/.
• Stary format (*.meta.json + shards/) migruje się przy zapisie.

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
  Zespół          Sync przez cynober-server (tryb lokalny)
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
    "O programie",
    f"""
Lore Editor v{__version__}
Silnik lore: Cynober DB (cynober-db >= 8.0.1)
Repozytorium: github.com/Maciej-EriAmo/lore-editor

Funkcje: kontekst czasowy lore, zapytania semantyczne, termodynamika wpisów,
historia zmian projektu, transakcyjny zapis tekstu + grafu.

Tryb offline-first — bez serwera, bez Lua.
Opcjonalnie: --rpc dla współpracy przez cynober-server.

Instalacja:
  pip install "cynober-db>=8.0.1"
  pip install -e .
  lore-editor

Pakiet exe: .\\scripts\\build_nuitka.ps1

Licencja: MIT
""",
)

DEFAULT_TOPIC = "Przewodnik pisarza"


def topic_titles() -> list[str]:
    return list(TOPICS.keys())


def get_topic(title: str) -> tuple[str, str]:
    return TOPICS.get(title, TOPICS[DEFAULT_TOPIC])