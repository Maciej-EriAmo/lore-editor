# Pluginy językowe (locale packs)

**[English → LANGUAGE_PLUGINS.md](LANGUAGE_PLUGINS.md)**

**Wersja aplikacji:** 0.7.5+  
**Moduł:** `lore/i18n/` · wbudowane: `lore/locales/en/` · przykład: `plugins/locales/tlh/`

Lore Editor trzyma **język UI** osobno od protokołu KarminQL i wartości w `.kafd`.  
Komendy bazy (`UTRWAL`, `ZNAJDŹ`) oraz typy w grafie (`Postać`, …) zostają stabilne — tłumaczone są etykiety menu, toolbara, panelu, statusu i (opcjonalnie) pomocy.

## Szybki start

```powershell
# Angielski (wbudowany)
lore-editor --locale en

# Klingoński — przykładowy plugin z repo
$env:LORE_LOCALE="tlh"
lore-editor

# Albo tylko na jedną sesję:
lore-editor --locale tlh
```

Preferencja jest zapisywana w `%USERPROFILE%\.lore_editor\settings.json` (`"locale": "en"`).

Zmienna środowiskowa **`LORE_LOCALE`** ma pierwszeństwo przy starcie.

W aplikacji: menu **Język** (lista zarejestrowanych paczek).

---

## Co zawiera paczka

Katalog z co najmniej:

| Plik | Wymagany | Opis |
|------|----------|------|
| `meta.json` | tak | `code`, `name`, `native_name`, `spell` |
| `ui.json` | tak | mapa `klucz` → tekst UI |
| `help.json` | nie | tematy pomocy `{ id: { title, body } }` |

### `meta.json` (przykład klingoński)

```json
{
  "code": "tlh",
  "name": "Klingon",
  "native_name": "tlhIngan Hol",
  "spell": "tlh",
  "author": "Ty",
  "version": "0.1"
}
```

- **`code`** — identyfikator (`en`, `ja`, `tlh`)  
- **`spell`** — backend korekty: `pl`, `en`, lub własny kod (fallback: nazwy lore + słownik projektu)  
- **`native_name`** — etykieta w menu **Język**

### `ui.json`

Klucze jak w `lore/locales/en/ui.json`, np.:

```json
{
  "menu.file": "teywI'",
  "file.save": "pol",
  "app.ready": "ruch"
}
```

Brakujący klucz spada na **polski** wbudowany, potem na sam klucz.

---

## Gdzie umieścić plugin

### 1. Katalog pluginów (najprostsze)

```
plugins/locales/<code>/
  meta.json
  ui.json
  help.json      # opcjonalnie
```

W repozytorium jest gotowy przykład: **`plugins/locales/tlh/`** (klingoński).

Dodatkowe ścieżki:

```powershell
$env:LORE_LOCALE_PATHS="D:\moje-locale;D:\inne\tlh"
```

Każdy element to albo katalog z `ui.json`, albo folder zawierający podkatalogi-paczki.

### 2. Entry point (pakiet pip)

W `pyproject.toml` Twojego pluginu:

```toml
[project.entry-points."lore_editor.locale"]
tlh = "moj_pakiet_tlh:get_pack"
```

```python
# moj_pakiet_tlh.py
from pathlib import Path
from lore.i18n import LocalePack, load_locale_dir

def get_pack():
    return load_locale_dir(Path(__file__).parent / "data")
    # albo:
    # return LocalePack(code="tlh", name="Klingon", ui={...}, spell="tlh")
```

---

## Jak dodać język krok po kroku (klingoński jako szablon)

1. Skopiuj folder:
   ```text
   plugins/locales/tlh  →  plugins/locales/ja
   ```
2. Zmień `meta.json`: `"code": "ja"`, `"native_name": "日本語"`, `"spell": "ja"`.
3. Przetłumacz wszystkie stringi w `ui.json` (zacznij od `menu.*` i `file.*`).
4. (Opcja) Napisz `help.json` z tematem `writer_guide`.
5. Uruchom:
   ```powershell
   lore-editor --locale ja
   ```
6. W menu **Język** powinna pojawić się nowa pozycja.

Dla **japońskiego** korekta ortografii nie używa hunspell PL — na start wystarczą nazwy z grafu lore + `.lore-spelling.json`. Pełny morph (Sudachi/MeCab) to osobny backend `spell`.

---

## Korekta pisowni a locale

| `spell` | Zachowanie |
|---------|------------|
| `pl` | SJP.PL (`lore/data/sjp/pl_PL`) + zapas |
| `en` | hunspell `lore/data/en_US` jeśli jest; inaczej common EN + lore |
| inny | lore + słownik projektu + sesja „ignoruj” |

Tokenizacja na razie jest „łacińska + PL” — CJK wymaga osobnego tokenizera w przyszłej wersji.  
Szczegóły: [SLOWNIK_I_PISOWNIA.md](SLOWNIK_I_PISOWNIA.md) · EN: [SPELLING_AND_DICTIONARY.md](SPELLING_AND_DICTIONARY.md).

---

## Ważniejsze klucze `ui.json`

| Prefiks | Przykłady |
|---------|-----------|
| `app.*` | `app.name`, `app.ready`, `app.language` |
| `menu.*` | `menu.file`, `menu.edit`, `menu.lore`, `menu.help` |
| `file.*` | `file.new`, `file.save`, `file.quit` |
| `edit.*` | `edit.find`, `edit.spellcheck` |
| `panel.*` | `panel.add_character`, `panel.tab_chapter`, `panel.push` |
| `help.*` | `help.writer_guide`, `help.title` |
| `dialog.*` | `dialog.save`, `dialog.unsaved_lore_ask` |
| `status.*` | `status.autosave_failed`, `status.close_save_failed` |

Pełna lista referencyjna: `lore/locales/en/ui.json` (i wbudowany PL w `lore/i18n/core.py`).

### `help.json` (opcjonalnie)

```json
{
  "writer_guide": { "title": "…", "body": "…" },
  "shortcuts": { "title": "…", "body": "…" },
  "spell": { "title": "…", "body": "…" }
}
```

Id mapowane na tematy PL: `writer_guide`, `shortcuts`, `fonts`, `print`, `panel`, `spell`, `temporal`, `query`, `history`.

---

## API w kodzie

```python
from lore.i18n import t, set_locale, list_locales, discover_and_load

discover_and_load()
set_locale("en")
print(t("menu.file"))  # "File"

for pack in list_locales():
    print(pack.code, pack.display_name(), pack.source)
```

---

## Czego **nie** tłumaczyć w pluginie

- Komend KarminQL / RPC (`WYBIERZ ŚWIAT`, …)
- Kluczy relacji w grafie (`wplywa_na`, …)
- Wartości `Typ` zapisanych w istniejących projektach (`Postać`, …) — UI może dostać etykiety później; storage zostaje

Dzięki temu projekt PL i EN otwiera ten sam plik `.kafd`.

---

## Angielski (wbudowany)

Paczka **`lore/locales/en/`** jest częścią aplikacji (nie trzeba pluginu zewnętrznego).

```powershell
lore-editor --locale en
```

---

## Zmiany w 0.7.4 (skrót)

- Locale packs: PL / EN / plugin `tlh`
- RPC: login (`--rpc-user` / `LORE_RPC_USER` + token)
- Bezpieczne zamykanie: `close(zapisz_lore=False)` **nie** flushuje dirty świata
- Odczyty KarminQL nie oznaczają świata dirty
- Autosave zgłasza błędy (status + ostrzeżenie)
- Izolacja katalogów projektów bez globalnego `CYNOBER_WORLDS_DIR`

## Zmiany w 0.7.5 (skrót, nie tylko i18n)

- RPC / Zespół: host poza loopback **wymaga** user+token (fail-fast); `LORE_RPC_ALLOW_ANON=1` świadomie
- Panel Zespół: pola User/Token + ostrzeżenie przy zdalnym hoście
- Historia: pełne przywrócenie (strict) usuwa rozdziały spoza snapshota
- Lokalny unfold: komenda **ROZWIŃ** (alias ROZWIJ na cynober-server)
- Autosave: tekst OK / lore nie — spójnie z ręcznym zapisem
- Build standalone: `LoreEditor-0.7.5-win64` (`scripts/build_nuitka.ps1`)

---

*Przykład `tlh` jest celowo niekompletny językowo — to szablon struktury, nie oficjalna lokalizacja klingońska.*
