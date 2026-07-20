# Słownik nazw i sprawdzanie pisowni

**Status:** zaimplementowane (offline-first)  
**UI:** menu **Edycja** · skróty **Ctrl+Shift+D**, **F7**  
**Pomoc w aplikacji:** temat „Słownik i pisownia”

---

## Cel

Dwie osobne funkcje pisarskie:

1. **Słownik nazw (lore)** — szybki podgląd i wstawianie postaci, miejsc i innych wpisów z grafu projektu.
2. **Sprawdzanie pisowni** — korekta ortografii polskiej w tekście rozdziału, bez sieci.

To **nie** jest tezaurus PWN ani glosariusz definicji encyklopedycznych. Nazwy własne świata biorą się z panelu Lore; ortografia z SJP.PL.

---

## Słownik nazw (Ctrl+Shift+D)

| Element | Zachowanie |
|---------|------------|
| Źródło danych | `LoreStore.wszystkie_wpisy()` + `podglad()` |
| Wyszukiwanie | Fragment nazwy lub treść notatki/opisu |
| Filtr | Typ lore (Postać, Miejsce, …) |
| Zaznaczenie w edytorze | Wypełnia pole wyszukiwania |
| Wstaw do tekstu | Nazwa w miejscu kursora (zastępuje zaznaczenie) |

Moduł UI: `lore/dictionary_view.py` → `NameDictionaryDialog`.

---

## Sprawdzanie pisowni (F7)

### Kolejność decyzji „czy słowo jest OK”

1. **Sesja** — słowa oznaczone „Ignoruj” w bieżącym oknie F7  
2. **Lore** — pełne nazwy i tokeny z grafu (postacie, miejsca…)  
3. **Projekt** — plik `.lore-spelling.json` w folderze powieści  
4. **Akronimy** — same wielkie litery, długość 2–6 (np. FBI)  
5. **SJP.PL** (gdy dostępny) — hunspell `pl_PL` przez **spylls**  
6. **Zapas** — `lore/data/pl_common.txt.gz` (lista frekwencyjna), tylko gdy brak SJP/spylls  

### Silnik SJP.PL

| Plik | Rola |
|------|------|
| `lore/data/sjp/pl_PL.aff` | Reguły afiksów (fleksja) |
| `lore/data/sjp/pl_PL.dic` | Lemat + flagi |
| `lore/data/sjp/NOTICE.txt` | Atrybucja i wybór licencji |
| `lore/data/sjp/README_pl_PL.txt` | Oryginalny README dystrybucji SJP |

- Źródło: <https://sjp.pl/slownik/ort/> (paczka myspell/hunspell)  
- Wersja wbudowana: zob. data w `README_pl_PL.txt`  
- **Licencja (do wyboru u upstream):** GPL 2, LGPL 2.1, MPL 1.1, **Apache 2.0**, CC BY 4.0  
- **W Lore Editorze przyjmujemy Apache 2.0** + atrybucja (kompatybilne z MIT kodu aplikacji)

Silnik: pakiet PyPI **`spylls`** (czysty Python, hunspell lookup + suggest).

Ładowanie: `lore.spellcheck.load_sjp_dictionary()` (cache). Etykieta UI: `backend_label()`.

### Plik projektu `.lore-spelling.json`

Powstaje przy pierwszej akcji **„Dodaj do słownika”** w oknie F7.

```json
{
  "version": 1,
  "words": ["mojesłowo", "neologizm"]
}
```

Słowa są porównywane w formie `casefold()`. Warto uwzględnić plik w backupie folderu powieści.

### UI korekty

| Przycisk | Działanie |
|----------|-----------|
| Zamień | Wstawia wybraną sugestię w tekście |
| Ignoruj | Pomija słowo do końca sesji dialogu |
| Dodaj do słownika | Zapis do `.lore-spelling.json` |
| Dalej | Następne nieznane słowo |
| Szukaj w lore… | Otwiera słownik nazw dla bieżącego słowa |

Nieznane słowa są podkreślane w edytorze (tag `spell_err`).

Moduły: `lore/spellcheck.py` (logika), `lore/dictionary_view.py` (dialog).

---

## Zależności i pakietowanie

```toml
# pyproject.toml
dependencies = [
  # …
  "spylls>=0.1.7",
]

[tool.setuptools.package-data]
lore = ["data/*.gz", "data/*.txt", "data/sjp/*"]
```

Build Nuitka / exe: dołącz katalog `lore/data/` (w tym `sjp/`), inaczej F7 spadnie na listę frekwencyjną.

---

## Testy

```bash
python -m unittest discover -s tests -p "test_spellcheck.py" -v
```

Pokrycie: tokenizacja PL, lore, słownik projektu, ładowanie SJP, fleksja (`poszedłem`, `koty`…), sugestie.

---

## Ograniczenia

- Brak tezaurusa (synonimów stylistycznych) — tylko ortografia + nazwy lore.  
- Brak sprawdzania „na żywo” przy każdym naciśnięciu klawisza (uruchamiane F7).  
- Pierwsze załadowanie `pl_PL.dic` przez spylls może zająć kilka sekund.  
- Neologizmy i celowe błędy postaci: **Dodaj do słownika** lub wpis w lore.
