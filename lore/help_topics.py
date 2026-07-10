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
5. Plik → Zapisz projekt lore — zapisuje graf postaci i powiązań.

DWA RODZAJE ZAPISU
• Zapisz (Ctrl+S) — zapisuje TEKST rozdziału na dysku.
• Zapisz projekt lore — zapisuje LORE (postacie, relacje) w jednym pliku Nazwa.kafd.

Tekst rozdziału i lore to osobne warstwy: .txt to Twoja proza, .kafd to graf powiązań.

PROJEKT
• Nazwa projektu = nazwa folderu lub wpis w .lore-project.
• Plik lore: NazwaProjektu.kafd (format Lore Pack — jeden plik, bez shards/).
• Stary format (*.meta.json + shards/) migruje się automatycznie przy zapisie.

PASEK STATUSU
Pokazuje: ścieżkę · liczbę słów · liczbę stron · (dla Courier) ~minut scenariusza · kodowanie.
""",
)

_topic(
    "Skróty klawiszowe",
    """
PLIK
  Ctrl+N          Nowa karta
  Ctrl+O          Otwórz plik
  Ctrl+S          Zapisz rozdział
  Ctrl+Shift+S    Zapisz jako…
  Ctrl+W          Zamknij kartę

EDYCJA
  Ctrl+Z          Cofnij
  Ctrl+Y          Ponów
  Ctrl+F          Znajdź

INNE
  F1              Ta pomoc (przewodnik)
  Środkowy klik   Zamknij kartę (na nazwie karty)
  × na karcie     Zamknij kartę

Autosave rozdziału: co 60 s (tylko pliki już zapisane na dysku).
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
Panel po prawej stronie — zakładki Rozdział · Szukaj · Zespół.

WAŻNE: Otwórz rozdział w edytorze (karta z plikiem), zanim powiążesz lore.

DODAWANIE
  + Postać    Tworzy postać; przy otwartym rozdziale — auto-powiązanie
  + Pomysł    Zapisuje myśl i wiąże z rozdziałem
  + Wpływ     Inspiracja (np. autor, mit) — relacja „inspiruje”

POWIĄZANIA
  Powiąż z rozdziałem   Wpis z listy → ten plik
  Powiąż inny wpis…     Wpisz nazwę ręcznie
  Połącz z…             Relacja między dwoma wpisami lore
  Odłącz od rozdziału   Usuwa więź z plikiem; wpis zostaje
  Usuń wpis             Trwałe skasowanie (Delete na liście)

INNE
  Mapa powiązań   Graf koligacji
  Szukaj          Fraza w notatkach i opisach
  Zespół          Sync przez cynober-server (tryb lokalny)
""",
)

_topic(
    "Pliki i Lore Pack",
    """
STRUKTURA FOLDERU
  MojaPowiesc/
    .lore-project       Opcjonalny znacznik (name=MojaPowiesc)
    rozdzial_01.txt     Tekst — edytujesz w edytorze
    MojaPowiesc.kafd    Całe lore w jednym pliku (Lore Pack)

CO JEST W .kafd
  • Bąble: postacie, pomysły, dokumenty (wskaźnik do .txt), wpływy
  • Relacje: występuje w, koliguje z, wpływa na, inspiruje…
  • Indeksy zapytań (cache) — odtwarzalne z danych

CO NIE JEST W .kafd
  • Treść rozdziałów — zawsze w plikach .txt / .md

.gitignore zaleca ignorowanie *.kafd — lore traktuj jak dane robocze.

BACKUP
Kopiuj folder projektu: pliki tekstowe + .kafd + .lore-project.
""",
)

_topic(
    "O programie",
    f"""
Lore Editor v{__version__}
Silnik lore: Cynober DB (cynober-db >= 8.0.1)
Repozytorium: github.com/Maciej-EriAmo/lore-editor

Tryb offline-first — bez serwera, bez Lua.
Opcjonalnie: --rpc dla współpracy przez cynober-server.

Instalacja:
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